"""Lexical analyzer for the bluescreen language.

Token types:
  KEYWORD   - var, input, output
  IDENT     - variable names ([a-zA-Z_][a-zA-Z0-9_]*)
  NUMBER    - integer literals ([0-9]+)
  PLUS      - +
  MINUS     - -
  STAR      - *
  SLASH     - /
  ASSIGN    - =
  LPAREN    - (
  RPAREN    - )
  SEMI      - ;
  EOF       - end of input
"""

KEYWORDS = {"var", "input", "output"}

# Token type constants
TT_KEYWORD = "KEYWORD"
TT_IDENT   = "IDENT"
TT_NUMBER  = "NUMBER"
TT_PLUS    = "PLUS"
TT_MINUS   = "MINUS"
TT_STAR    = "STAR"
TT_SLASH   = "SLASH"
TT_ASSIGN  = "ASSIGN"
TT_LPAREN  = "LPAREN"
TT_RPAREN  = "RPAREN"
TT_SEMI    = "SEMI"
TT_EOF     = "EOF"


class Token:
    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class LexerError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.line = line


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1

    def _current(self):
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self._current()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "/" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "*":
                # Block comment /* ... */
                start_line = self.line
                self._advance()  # consume '/'
                self._advance()  # consume '*'
                closed = False
                while self.pos < len(self.source):
                    if self._current() == "*" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "/":
                        self._advance()  # consume '*'
                        self._advance()  # consume '/'
                        closed = True
                        break
                    self._advance()
                if not closed:
                    raise LexerError("Unterminated block comment", start_line)
            else:
                break

    def tokenize(self):
        tokens = []
        while True:
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                tokens.append(Token(TT_EOF, None, self.line))
                break

            ch = self._current()
            line = self.line

            if ch.isalpha() or ch == "_":
                start = self.pos
                while self.pos < len(self.source) and (self._current().isalnum() or self._current() == "_"):
                    self._advance()
                word = self.source[start:self.pos]
                ttype = TT_KEYWORD if word in KEYWORDS else TT_IDENT
                tokens.append(Token(ttype, word, line))

            elif ch.isdigit():
                start = self.pos
                while self.pos < len(self.source) and self._current().isdigit():
                    self._advance()
                tokens.append(Token(TT_NUMBER, int(self.source[start:self.pos]), line))

            elif ch == "+":
                self._advance()
                tokens.append(Token(TT_PLUS, "+", line))
            elif ch == "-":
                self._advance()
                tokens.append(Token(TT_MINUS, "-", line))
            elif ch == "*":
                self._advance()
                tokens.append(Token(TT_STAR, "*", line))
            elif ch == "/":
                self._advance()
                tokens.append(Token(TT_SLASH, "/", line))
            elif ch == "=":
                self._advance()
                tokens.append(Token(TT_ASSIGN, "=", line))
            elif ch == "(":
                self._advance()
                tokens.append(Token(TT_LPAREN, "(", line))
            elif ch == ")":
                self._advance()
                tokens.append(Token(TT_RPAREN, ")", line))
            elif ch == ";":
                self._advance()
                tokens.append(Token(TT_SEMI, ";", line))
            else:
                raise LexerError(f"Unexpected character: {ch!r}", line)

        return tokens
