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

import yaml


class Line:
    def __init__(self, line_no, buffer, start, end):
        self.line_no = line_no
        self.start = start
        self.end = end
        self.buffer = buffer

    @property
    def content(self):
        return self.buffer[self.start:self.end]


class Token:
    def __init__(self, line_no, curr, prev, next, nextnext):
        self.line_no = line_no
        self.curr = curr
        self.prev = prev
        self.next = next
        self.nextnext = nextnext


class Comment:
    def __init__(self, line_no, column_no, buffer, pointer,
                 token_before=None, token_after=None, comment_before=None):
        self.line_no = line_no
        self.column_no = column_no
        self.buffer = buffer
        self.pointer = pointer
        self.token_before = token_before
        self.token_after = token_after
        self.comment_before = comment_before

    def __str__(self):
        end = self.buffer.find('\n', self.pointer)
        if end == -1:
            end = self.buffer.find('\0', self.pointer)
        if end != -1:
            return self.buffer[self.pointer:end]
        return self.buffer[self.pointer:]

    def __eq__(self, other):
        return (isinstance(other, Comment) and
                self.line_no == other.line_no and
                self.column_no == other.column_no and
                str(self) == str(other))

    def is_inline(self):
        return (
            not isinstance(self.token_before, yaml.StreamStartToken) and
            self.line_no == self.token_before.end_mark.line + 1 and
            # sometimes token end marks are on the next line
            self.buffer[self.token_before.end_mark.pointer - 1] != '\n'
        )


def line_generator(buffer):
    line_no = 1
    cur = 0
    next = buffer.find('\n')
    while next != -1:
        if next > 0 and buffer[next - 1] == '\r':
            yield Line(line_no, buffer, start=cur, end=next - 1)
        else:
            yield Line(line_no, buffer, start=cur, end=next)
        cur = next + 1
        next = buffer.find('\n', cur)
        line_no += 1

    yield Line(line_no, buffer, start=cur, end=len(buffer))


def comments_between_tokens(token1, token2):
    """Find all comments between two tokens"""
    if token2 is None:
        buf = token1.end_mark.buffer[token1.end_mark.pointer:]
    elif (token1.end_mark.line == token2.start_mark.line and
          not isinstance(token1, yaml.StreamStartToken) and
          not isinstance(token2, yaml.StreamEndToken)):
        return
    else:
        buf = token1.end_mark.buffer[token1.end_mark.pointer:
                                     token2.start_mark.pointer]

    line_no = token1.end_mark.line + 1
    column_no = token1.end_mark.column + 1
    pointer = token1.end_mark.pointer

    comment_before = None
    for line in buf.split('\n'):
        pos = line.find('#')
        if pos != -1:
            comment = Comment(line_no, column_no + pos,
                              token1.end_mark.buffer, pointer + pos,
                              token1, token2, comment_before)
            yield comment

            comment_before = comment

        pointer += len(line) + 1
        line_no += 1
        column_no = 1


def token_or_comment_generator(buffer):
    """
    Generates tokens and comments from a given YAML buffer.

    Parameters:
    - buffer (str): A string containing the YAML content to be processed.

    Returns:
    - Yields a Token object for each token found in the buffer, which
      includes the current token, its previous and next tokens, and the
      next-next token. Additionally, it yields Comment objects for comments
      found between the tokens.

    Dependencies:
    - This function relies on the `yaml` module, specifically
      `yaml.BaseLoader`, to parse the YAML content and retrieve tokens. It
      interacts with the `comments_between_tokens` function to extract
      comments related to the tokens.
    - The `Token` class is used to encapsulate the structure of each token,
      while the `Comment` class is utilized to manage comment details. The
      method `get_token()` from the `yaml_loader` retrieves tokens one at a
      time, and `check_token()` and `peek_token()` are used to manage the
      flow of token extraction.
    """
    yaml_loader = yaml.BaseLoader(buffer)

    # Tokens are read ahead, up to two of them after the current one, so that
    # each token knows its neighbours.
    window = []
    reading = True  # False once the loader has no more tokens, or failed
    failed = False  # True if the loader stopped because of a scanning error
    prev = None

    while True:
        while reading and len(window) < 3:
            try:
                if yaml_loader.check_token():
                    window.append(yaml_loader.get_token())
                else:
                    reading = False
            except yaml.YAMLError:
                reading = False
                failed = True

        if not window:
            return
        if failed and len(window) < 3:
            # After a scanning error, only the tokens whose neighbours were
            # read are yielded. The error itself is reported as a syntax error.
            return

        curr = window.pop(0)
        following = window[0] if window else None
        after_following = window[1] if len(window) > 1 else None

        yield Token(curr.start_mark.line + 1, curr, prev, following,
                    after_following)
        if following is not None:
            yield from comments_between_tokens(curr, following)

        prev = curr


def token_or_comment_or_line_generator(buffer):
    """Generator that mixes tokens and lines, ordering them by line number"""
    tok_or_com_gen = token_or_comment_generator(buffer)
    line_gen = line_generator(buffer)

    tok_or_com = next(tok_or_com_gen, None)
    line = next(line_gen, None)

    while tok_or_com is not None or line is not None:
        if tok_or_com is None or (line is not None and
                                  tok_or_com.line_no > line.line_no):
            yield line
            line = next(line_gen, None)
        else:
            yield tok_or_com
            tok_or_com = next(tok_or_com_gen, None)
