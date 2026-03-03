"""
Lexical analyzer for the bluescreen language.

Converts source text into a stream of tokens.

Time complexity: O(n) where n = number of characters in source.
Space complexity: O(n) for the output token list.
"""

from dataclasses import dataclass, field
from typing import Any

# ── Token type constants ──────────────────────────────────────────────
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

KEYWORDS = {"var", "input", "output"}

SINGLE_CHAR_TOKENS = {
    "+": TT_PLUS,
    "-": TT_MINUS,
    "*": TT_STAR,
    "=": TT_ASSIGN,
    "(": TT_LPAREN,
    ")": TT_RPAREN,
    ";": TT_SEMI,
}


class LexerError(Exception):
    """Raised when the lexer encounters an invalid character or unterminated comment."""


@dataclass
class Token:
    type: str
    value: Any = None
    line: int = 1


class Lexer:
    """Tokenizes bluescreen source code.

    Usage::

        tokens = Lexer(source).tokenize()
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1

    # ── helpers ───────────────────────────────────────────────────────

    def _peek(self) -> str | None:
        return self.source[self.pos] if self.pos < len(self.source) else None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def _skip_whitespace(self) -> None:
        while self.pos < len(self.source) and self.source[self.pos] in " \t\r\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        """Skip a /* ... */ block comment.  Raises LexerError if unterminated."""
        start_line = self.line
        self._advance()  # skip '/'
        self._advance()  # skip '*'
        while self.pos < len(self.source) - 1:
            if self.source[self.pos] == "*" and self.source[self.pos + 1] == "/":
                self._advance()  # skip '*'
                self._advance()  # skip '/'
                return
            self._advance()
        # handle edge case: at last char or past end
        if self.pos < len(self.source):
            self._advance()
        raise LexerError(
            f"Unterminated block comment starting at line {start_line}"
        )

    def _read_number(self) -> Token:
        start = self.pos
        line = self.line
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
        return Token(TT_NUMBER, int(self.source[start : self.pos]), line)

    def _read_word(self) -> Token:
        start = self.pos
        line = self.line
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] == "_"
        ):
            self.pos += 1
        word = self.source[start : self.pos]
        tt = TT_KEYWORD if word in KEYWORDS else TT_IDENT
        return Token(tt, word, line)

    # ── public API ────────────────────────────────────────────────────

    def tokenize(self) -> list["Token"]:
        """Return a list of tokens ending with a TT_EOF token.

        Time complexity: O(n).
        """
        tokens: list[Token] = []

        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.source[self.pos]

            # block comment
            if (
                ch == "/"
                and self.pos + 1 < len(self.source)
                and self.source[self.pos + 1] == "*"
            ):
                self._skip_block_comment()
                continue

            # single-character tokens (except '/' which could start a comment)
            if ch in SINGLE_CHAR_TOKENS:
                tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, self.line))
                self._advance()
                continue

            # '/' as division (not a comment start)
            if ch == "/":
                tokens.append(Token(TT_SLASH, ch, self.line))
                self._advance()
                continue

            # numbers
            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            # identifiers / keywords
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_word())
                continue

            raise LexerError(f"Unexpected character {ch!r} at line {self.line}")

        tokens.append(Token(TT_EOF, None, self.line))
        return tokens
