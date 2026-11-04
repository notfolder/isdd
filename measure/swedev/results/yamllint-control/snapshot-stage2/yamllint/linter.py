# Copyright (C) 2016 Adrien Vergé
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import io
import re

import yaml

from yamllint import parser

PROBLEM_LEVELS = {
    0: None,
    1: 'warning',
    2: 'error',
    None: 0,
    'warning': 1,
    'error': 2,
}

DISABLE_RULE_PATTERN = re.compile(r'^# yamllint disable( rule:\S+)*\s*$')
ENABLE_RULE_PATTERN = re.compile(r'^# yamllint enable( rule:\S+)*\s*$')


class LintProblem:
    """Represents a linting problem found by yamllint."""

    def __init__(self, line, column, desc='<no description>', rule=None):
        self.line = line
        self.column = column
        self.desc = desc
        self.rule = rule
        self.level = None

    def __lt__(self, other):
        return (self.line, self.column) < (other.line, other.column)

    def __eq__(self, other):
        return (self.line == other.line and
                self.column == other.column and
                self.rule == other.rule)

    @property
    def message(self):
        if self.rule is not None:
            return f'{self.desc} ({self.rule})'
        return self.desc



    def __repr__(self):
        return f'{self.line}:{self.column}: {self.message}'


def get_cosmetic_problems(buffer, conf, filepath):
    rules = conf.enabled_rules(filepath)

    # Split token rules from line rules
    token_rules = [r for r in rules if r.TYPE == 'token']
    comment_rules = [r for r in rules if r.TYPE == 'comment']
    line_rules = [r for r in rules if r.TYPE == 'line']

    context = {}
    for rule in token_rules:
        context[rule.ID] = {}

    class DisableDirective:
        def __init__(self):
            self.rules = set()
            self.all_rules = {r.ID for r in rules}

        def process_comment(self, comment):
            comment = str(comment)

            if DISABLE_RULE_PATTERN.match(comment):
                items = comment[18:].rstrip().split(' ')
                rules = [item[5:] for item in items][1:]
                if len(rules) == 0:
                    self.rules = self.all_rules.copy()
                else:
                    for id in rules:
                        if id in self.all_rules:
                            self.rules.add(id)

            elif ENABLE_RULE_PATTERN.match(comment):
                items = comment[17:].rstrip().split(' ')
                rules = [item[5:] for item in items][1:]
                if len(rules) == 0:
                    self.rules.clear()
                else:
                    for id in rules:
                        self.rules.discard(id)

        def is_disabled_by_directive(self, problem):
            return problem.rule in self.rules

    class DisableLineDirective(DisableDirective):
        def process_comment(self, comment):
            comment = str(comment)

            if re.match(r'^# yamllint disable-line( rule:\S+)*\s*$', comment):
                items = comment[23:].rstrip().split(' ')
                rules = [item[5:] for item in items][1:]
                if len(rules) == 0:
                    self.rules = self.all_rules.copy()
                else:
                    for id in rules:
                        if id in self.all_rules:
                            self.rules.add(id)

    # Use a cache to store problems and flush it only when an end of line is
    # found. This allows the use of yamllint directive to disable some rules on
    # some lines.
    cache = []
    disabled = DisableDirective()
    disabled_for_line = DisableLineDirective()
    disabled_for_next_line = DisableLineDirective()

    for elem in parser.token_or_comment_or_line_generator(buffer):
        if isinstance(elem, parser.Token):
            for rule in token_rules:
                rule_conf = conf.rules[rule.ID]
                for problem in rule.check(rule_conf,
                                          elem.curr, elem.prev, elem.next,
                                          elem.nextnext,
                                          context[rule.ID]):
                    problem.rule = rule.ID
                    problem.level = rule_conf['level']
                    cache.append(problem)
        elif isinstance(elem, parser.Comment):
            for rule in comment_rules:
                rule_conf = conf.rules[rule.ID]
                for problem in rule.check(rule_conf, elem):
                    problem.rule = rule.ID
                    problem.level = rule_conf['level']
                    cache.append(problem)

            disabled.process_comment(elem)
            if elem.is_inline():
                disabled_for_line.process_comment(elem)
            else:
                disabled_for_next_line.process_comment(elem)
        elif isinstance(elem, parser.Line):
            for rule in line_rules:
                rule_conf = conf.rules[rule.ID]
                for problem in rule.check(rule_conf, elem):
                    problem.rule = rule.ID
                    problem.level = rule_conf['level']
                    cache.append(problem)

            # This is the last token/comment/line of this line, let's flush the
            # problems found (but filter them according to the directives)
            for problem in cache:
                if not (disabled_for_line.is_disabled_by_directive(problem) or
                        disabled.is_disabled_by_directive(problem)):
                    yield problem

            disabled_for_line = disabled_for_next_line
            disabled_for_next_line = DisableLineDirective()
            cache = []


def get_syntax_error(buffer):
    try:
        list(yaml.parse(buffer, Loader=yaml.BaseLoader))
    except yaml.error.MarkedYAMLError as e:
        problem = LintProblem(e.problem_mark.line + 1,
                              e.problem_mark.column + 1,
                              'syntax error: ' + e.problem + ' (syntax)')
        problem.level = 'error'
        return problem


def run(input, conf, filepath=None):
    """
    Lints a YAML source and identifies potential problems using the yamllint configuration.

    This function checks the provided YAML input for syntax errors and cosmetic issues according to the `yamllint` rules. It returns a generator that yields instances of `LintProblem`, which encapsulate the details of any detected problems.

    Parameters:
    - input: A buffer, string, or stream to read from containing the YAML source.
    - conf: A configuration object specific to `yamllint`, which defines the linting rules and their statuses.
    - filepath: An optional string representing the file path of the input, used to check if the file is ignored by the configuration.

    Returns:
    - A generator of `LintProblem` objects representing any linting issues or syntax errors found in the input. If the file is ignored or if the input is of unsupported type, appropriate handling is performed.

    Dependencies:
    - This function relies on the `_run` function to process the input and the `get_cosmetic_problems` function to identify linting issues. Additionally, it interacts with `io` for reading from stream inputs and uses `yaml` for parsing YAML content.
    """
    if filepath is not None and conf.is_file_ignored(filepath):
        return ()

    if isinstance(input, io.IOBase):
        # The whole content is needed to parse the YAML correctly.
        return _run(input.read(), conf, filepath)
    elif isinstance(input, bytes):
        try:
            content = input.decode('utf-8')
        except UnicodeDecodeError:
            content = input.decode('iso-8859-1')
        return _run(content, conf, filepath)
    elif isinstance(input, str):
        return _run(input, conf, filepath)
    else:
        raise TypeError('input should be a string, bytes or a stream')


def _run(buffer, conf, filepath):
    """
    Runs the YAML linting process on a provided buffer, checking for syntax errors and generating cosmetic problem reports.

    Parameters:
    - buffer: A string, bytes, or a buffer-like object containing the YAML content to lint.
    - conf: A configuration object that defines linting rules and directives.
    - filepath: An optional string representing the file path of the YAML document (used for rule application context).

    Returns:
    - A generator yielding LintProblem instances, which encapsulate linting issues found in the YAML source.

    Dependencies:
    - The function uses the `get_syntax_error` function to check for syntax errors and `get_cosmetic_problems` to identify stylistic issues.
    - If the content includes a disable-file directive on the first line, linting is skipped.
    - The function asserts that the input buffer supports indexing, as it requires access to specific lines of the input.

    Side Effects:
    - The function can yield a syntax error if present, immediately prioritizing it over cosmetic problems to prevent redundancy in output.
    """
    assert hasattr(buffer, '__getitem__')

    first_line = next(parser.line_generator(buffer)).content
    if re.match(r'^#\s*yamllint disable-file\s*$', first_line):
        return

    syntax_error = get_syntax_error(buffer)
    if syntax_error is not None:
        yield syntax_error
        return

    yield from get_cosmetic_problems(buffer, conf, filepath)
