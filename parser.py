"""
Recursive-descent parser for the bluescreen language.

Builds a typed Abstract Syntax Tree from a token list.

Grammar (EBNF)::

    program    → statement* EOF
    statement  → var_decl | assign | input_stmt | output_stmt
    var_decl   → 'var' IDENT ';'
    assign     → IDENT '=' expression ';'
    input_stmt → 'input' IDENT ';'
    output_stmt→ 'output' expression ';'
    expression → term  ( ('+' | '-')  term  )*
    term       → factor ( ('*' | '/') factor )*
    factor     → NUMBER | IDENT | '(' expression ')'

Time complexity : O(n) where n = number of tokens.
Space complexity: O(n) for the AST.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lexer import (
    Token,
    TT_KEYWORD, TT_IDENT, TT_NUMBER,
    TT_PLUS, TT_MINUS, TT_STAR, TT_SLASH,
    TT_ASSIGN, TT_LPAREN, TT_RPAREN, TT_SEMI, TT_EOF,
)


# ── Exceptions ────────────────────────────────────────────────────────

class ParseError(Exception):
    """Raised when the parser encounters unexpected tokens."""


# ── AST node classes ──────────────────────────────────────────────────

@dataclass
class ASTNode:
    """Base class for every AST node."""
    type: str = field(init=False)

@dataclass
class Number(ASTNode):
    value: int
    def __post_init__(self):
        self.type = "Number"

@dataclass
class Ident(ASTNode):
    name: str
    def __post_init__(self):
        self.type = "Ident"

@dataclass
class BinOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode
    def __post_init__(self):
        self.type = "BinOp"

@dataclass
class VarDecl(ASTNode):
    name: str
    def __post_init__(self):
        self.type = "VarDecl"

@dataclass
class Assign(ASTNode):
    name: str
    expr: ASTNode
    def __post_init__(self):
        self.type = "Assign"

@dataclass
class Input(ASTNode):
    name: str
    def __post_init__(self):
        self.type = "Input"

@dataclass
class Output(ASTNode):
    expr: ASTNode
    def __post_init__(self):
        self.type = "Output"

@dataclass
class Program(ASTNode):
    statements: list = field(default_factory=list)
    def __post_init__(self):
        self.type = "Program"


# ── Parser ────────────────────────────────────────────────────────────

class Parser:
    """Recursive-descent parser for bluescreen.

    Usage::

        tokens = Lexer(source).tokenize()
        ast    = Parser(tokens).parse()
    """

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # ── helpers ───────────────────────────────────────────────────────

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _at(self, *types: str) -> bool:
        return self._peek().type in types

    def _consume(self, expected: str) -> Token:
        tok = self._peek()
        if tok.type != expected:
            raise ParseError(
                f"Expected {expected}, got {tok.type} ({tok.value!r}) "
                f"at line {tok.line}"
            )
        self.pos += 1
        return tok

    # ── grammar rules ────────────────────────────────────────────────

    def parse(self) -> Program:
        """Parse the full program and return a ``Program`` AST node."""
        stmts: list[ASTNode] = []
        while not self._at(TT_EOF):
            stmts.append(self._statement())
        return Program(statements=stmts)

    def _statement(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TT_KEYWORD:
            if tok.value == "var":
                return self._var_decl()
            elif tok.value == "input":
                return self._input_stmt()
            elif tok.value == "output":
                return self._output_stmt()

        if tok.type == TT_IDENT:
            return self._assign()

        raise ParseError(
            f"Unexpected token {tok.type} ({tok.value!r}) at line {tok.line}"
        )

    def _var_decl(self) -> VarDecl:
        self._consume(TT_KEYWORD)          # 'var'
        name = self._consume(TT_IDENT).value
        self._consume(TT_SEMI)
        return VarDecl(name=name)

    def _input_stmt(self) -> Input:
        self._consume(TT_KEYWORD)          # 'input'
        name = self._consume(TT_IDENT).value
        self._consume(TT_SEMI)
        return Input(name=name)

    def _output_stmt(self) -> Output:
        self._consume(TT_KEYWORD)          # 'output'
        expr = self._expression()
        self._consume(TT_SEMI)
        return Output(expr=expr)

    def _assign(self) -> Assign:
        name = self._consume(TT_IDENT).value
        self._consume(TT_ASSIGN)
        expr = self._expression()
        self._consume(TT_SEMI)
        return Assign(name=name, expr=expr)

    # ── expressions (precedence climbing) ────────────────────────────

    def _expression(self) -> ASTNode:
        """expression → term ( ('+' | '-') term )*"""
        node = self._term()
        while self._at(TT_PLUS, TT_MINUS):
            op = self._peek().value
            self.pos += 1
            right = self._term()
            node = BinOp(op=op, left=node, right=right)
        return node

    def _term(self) -> ASTNode:
        """term → factor ( ('*' | '/') factor )*"""
        node = self._factor()
        while self._at(TT_STAR, TT_SLASH):
            op = self._peek().value
            self.pos += 1
            right = self._factor()
            node = BinOp(op=op, left=node, right=right)
        return node

    def _factor(self) -> ASTNode:
        """factor → NUMBER | IDENT | '(' expression ')'"""
        tok = self._peek()

        if tok.type == TT_NUMBER:
            self.pos += 1
            return Number(value=tok.value)

        if tok.type == TT_IDENT:
            self.pos += 1
            return Ident(name=tok.value)

        if tok.type == TT_LPAREN:
            self.pos += 1
            node = self._expression()
            self._consume(TT_RPAREN)
            return node

        raise ParseError(
            f"Expected expression, got {tok.type} ({tok.value!r}) "
            f"at line {tok.line}"
        )
