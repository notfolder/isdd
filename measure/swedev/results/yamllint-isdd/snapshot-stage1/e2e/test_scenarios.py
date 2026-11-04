# E2E tests for the scenarios in docs/detail_design.md section 8-2.
# They call the public entry points only: yamllint.linter.run,
# yamllint.config.YamlLintConfig, yamllint.cli.run and yamllint.parser.

import io

import pytest

from yamllint import linter
from yamllint.cli import run as cli_run
from yamllint.config import YamlLintConfig, YamlLintConfigError
from yamllint.linter import LintProblem
from yamllint.parser import Comment, Line, Token, \
    token_or_comment_or_line_generator, token_or_comment_generator


def lint(buffer, config_text='extends: default'):
    return list(linter.run(buffer, YamlLintConfig(config_text)))


def rule_lines(problems, rule):
    return sorted(p.line for p in problems if p.rule == rule)


def test_lint_buffer_problems():
    buffer = 'a:   1\nb: 2 \n'
    problems = lint(buffer)

    assert problems
    assert all(isinstance(p, LintProblem) for p in problems)
    assert all(p.line >= 1 and p.column >= 1 for p in problems)
    # The linter reports problems in line order.
    lines = [p.line for p in problems]
    assert lines == sorted(lines)
    assert rule_lines(problems, 'colons') == [1]
    assert rule_lines(problems, 'trailing-spaces') == [2]

    # A stream is accepted too.
    streamed = list(linter.run(io.StringIO(buffer), YamlLintConfig(
        'extends: default')))
    assert streamed == problems

    assert lint('---\na: 1\n') == []


def test_report_syntax_errors():
    problems = lint('a: [1, 2\n')

    syntax = [p for p in problems if p.rule is None]
    assert len(syntax) == 1
    assert syntax[0].level == 'error'
    assert 'syntax error' in syntax[0].desc


def test_directives_disable_rules():
    buffer = ('a:   1\n'
              '# yamllint disable rule:colons\n'
              'b:   2\n'
              '# yamllint enable rule:colons\n'
              'c:   3\n')
    assert rule_lines(lint(buffer), 'colons') == [1, 5]

    buffer = 'a:   1  # yamllint disable-line rule:colons\nb:   2\n'
    assert rule_lines(lint(buffer), 'colons') == [2]

    buffer = '# yamllint disable-file\na:   1\n'
    assert lint(buffer) == []


def test_load_config():
    conf = YamlLintConfig('extends: default\n'
                          'rules:\n'
                          '  colons: disable\n'
                          'ignore: |\n'
                          '  ignored.yaml\n')
    assert conf.is_file_ignored('ignored.yaml')
    assert not conf.is_file_ignored('kept.yaml')
    assert conf.is_yaml_file('kept.yaml')
    assert 'colons' not in [r.ID for r in conf.enabled_rules('kept.yaml')]
    assert 'indentation' in [r.ID for r in conf.enabled_rules('kept.yaml')]

    relaxed = YamlLintConfig('extends: relaxed')
    assert relaxed.rules['line-length']['level'] == 'warning'

    with pytest.raises(YamlLintConfigError):
        YamlLintConfig('rules:\n  indentation: {spaces: nope}\n')
    with pytest.raises(YamlLintConfigError):
        YamlLintConfig('rules:\n  no-such-rule: enable\n')


def test_cli_run_and_exit(tmp_path, capsys):
    bad = tmp_path / 'bad.yaml'
    good = tmp_path / 'good.yaml'
    bad.write_text('a:   1\n')
    good.write_text('a: 1\n')
    default = ['-d', 'extends: default']

    with pytest.raises(SystemExit) as e:
        cli_run(default + [str(good)])
    assert e.value.code == 0

    with pytest.raises(SystemExit) as e:
        cli_run(default + [str(bad)])
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert str(bad) in out
    assert '1:5' in out

    with pytest.raises(SystemExit) as e:
        cli_run(default + ['-f', 'parsable', str(bad)])
    assert e.value.code == 1
    assert capsys.readouterr().out.startswith(f'{bad}:1:')

    with pytest.raises(SystemExit) as e:
        cli_run(['-d', 'extends: default\nrules: {colons: {level: warning}}',
                 str(bad)])
    assert e.value.code == 0
    with pytest.raises(SystemExit) as e:
        cli_run(['-d', 'extends: default\nrules: {colons: {level: warning}}',
                 '-s', str(bad)])
    assert e.value.code == 2
    with pytest.raises(SystemExit) as e:
        cli_run(['-d', 'extends: default\nrules: {colons: {level: warning}}',
                 '--no-warnings', str(bad)])
    assert e.value.code == 0


def test_parse_tokens_and_comments():
    buffer = '# first\n- a  # second\n# third\n- b\n'
    elements = list(token_or_comment_or_line_generator(buffer))

    assert any(isinstance(e, Token) for e in elements)
    assert sum(isinstance(e, Comment) for e in elements) == 3
    assert sum(isinstance(e, Line) for e in elements) == 5

    numbers = [e.line_no for e in elements]
    assert numbers == sorted(numbers)

    tokens = [t for t in token_or_comment_generator(buffer)
              if isinstance(t, Token)]
    assert tokens[0].prev is None
    assert tokens[-1].next is None
    for before, after in zip(tokens, tokens[1:]):
        assert after.prev is before.curr


def test_check_indentation():
    config = ('extends: default\n'
              'rules:\n'
              '  indentation: {spaces: 2}\n')
    problems = lint('---\na:\n    b: 1\n', config)
    assert [(p.line, p.column, p.rule) for p in problems] == [
        (3, 5, 'indentation')]
    assert 'expected 2 but found 4' in problems[0].desc

    assert lint('---\na:\n  b: 1\n', config) == []


def test_check_line_layout():
    long_line = '---\nk: ' + 'x' * 80 + '\n'
    problems = lint(long_line)
    assert rule_lines(problems, 'line-length') == [2]

    problems = lint('---\nk: 1 \n\n\n\n\nj: 2\n')
    assert rule_lines(problems, 'trailing-spaces') == [2]
    assert rule_lines(problems, 'empty-lines') == [6]

    problems = lint('---\r\nk: 1\r\n')
    assert rule_lines(problems, 'new-lines') == [1]


def test_check_spacing():
    assert rule_lines(lint('---\na :  1\n'), 'colons') == [2, 2]
    assert rule_lines(lint('---\n- a\n-  b\n'), 'hyphens') == [3]
    assert rule_lines(lint('---\na: [1 ,2]\n'), 'commas') == [2, 2]


def test_check_document_markers():
    assert rule_lines(lint('a: 1\n'), 'document-start') == [1]
    assert lint('---\na: 1\n') == []

    config = 'extends: default\nrules:\n  document-end: {present: true}\n'
    assert rule_lines(lint('---\na: 1\n', config), 'document-end') == [2]


def test_check_comments():
    assert rule_lines(lint('---\na: 1 #bad\n'), 'comments') == [2, 2]
    assert rule_lines(lint('---\na: 1  # good\n'), 'comments') == []

    assert rule_lines(lint('---\na:\n    # wrong\n  b: 1\n'),
                      'comments-indentation') == [3]


def test_check_values():
    assert rule_lines(lint('---\na: yes\n'), 'truthy') == [2]
    assert lint('---\na: true\n') == []


def test_check_keys():
    assert rule_lines(lint('---\na: 1\na: 2\n'), 'key-duplicates') == [3]

    config = 'extends: default\nrules:\n  key-ordering: enable\n'
    assert rule_lines(lint('---\nb: 1\na: 2\n', config),
                      'key-ordering') == [3]

    assert rule_lines(lint('---\na: *x\n'), 'anchors') == [2]
