"""Syntax analyzer (recursive-descent parser) for the bluescreen language.

Grammar:
    program     := statement* EOF
    statement   := var_decl
                 | assignment
                 | input_stmt
                 | output_stmt

    var_decl    := 'var' IDENT ';'
    assignment  := IDENT '=' expression ';'
    input_stmt  := 'input' IDENT ';'
    output_stmt := 'output' expression ';'

    expression  := term (('+' | '-') term)*
    term        := factor (('*' | '/') factor)*
    factor      := IDENT
                 | NUMBER
                 | '(' expression ')'

AST node classes are plain objects with a ``type`` string attribute.
"""

from lexer import (
    TT_KEYWORD, TT_IDENT, TT_NUMBER,
    TT_PLUS, TT_MINUS, TT_STAR, TT_SLASH,
    TT_ASSIGN, TT_LPAREN, TT_RPAREN, TT_SEMI, TT_EOF,
)


# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------

class ProgramNode:
    def __init__(self, statements):
        self.type = "Program"
        self.statements = statements  # list of statement nodes

    def __repr__(self):
        return f"ProgramNode({self.statements!r})"


class VarDeclNode:
    def __init__(self, name, line):
        self.type = "VarDecl"
        self.name = name
        self.line = line

    def __repr__(self):
        return f"VarDeclNode({self.name!r})"


class AssignNode:
    def __init__(self, name, expr, line):
        self.type = "Assign"
        self.name = name
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f"AssignNode({self.name!r}, {self.expr!r})"


class InputNode:
    def __init__(self, name, line):
        self.type = "Input"
        self.name = name
        self.line = line

    def __repr__(self):
        return f"InputNode({self.name!r})"


class OutputNode:
    def __init__(self, expr, line):
        self.type = "Output"
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f"OutputNode({self.expr!r})"


class BinOpNode:
    def __init__(self, op, left, right, line):
        self.type = "BinOp"
        self.op = op
        self.left = left
        self.right = right
        self.line = line

    def __repr__(self):
        return f"BinOpNode({self.op!r}, {self.left!r}, {self.right!r})"


class IdentNode:
    def __init__(self, name, line):
        self.type = "Ident"
        self.name = name
        self.line = line

    def __repr__(self):
        return f"IdentNode({self.name!r})"


class NumberNode:
    def __init__(self, value, line):
        self.type = "Number"
        self.value = value
        self.line = line

    def __repr__(self):
        return f"NumberNode({self.value!r})"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class ParseError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.line = line


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _current(self):
        return self.tokens[self.pos]

    def _peek_type(self):
        return self.tokens[self.pos].type

    def _consume(self, expected_type=None, expected_value=None):
        tok = self.tokens[self.pos]
        if expected_type and tok.type != expected_type:
            raise ParseError(
                f"Expected {expected_type!r} but got {tok.type!r} ({tok.value!r})",
                tok.line,
            )
        if expected_value and tok.value != expected_value:
            raise ParseError(
                f"Expected {expected_value!r} but got {tok.value!r}",
                tok.line,
            )
        self.pos += 1
        return tok

    # -----------------------------------------------------------------------
    # Top-level
    # -----------------------------------------------------------------------

    def parse(self):
        statements = []
        while self._peek_type() != TT_EOF:
            statements.append(self._statement())
        self._consume(TT_EOF)
        return ProgramNode(statements)

    def _statement(self):
        tok = self._current()

        if tok.type == TT_KEYWORD and tok.value == "var":
            return self._var_decl()
        if tok.type == TT_KEYWORD and tok.value == "input":
            return self._input_stmt()
        if tok.type == TT_KEYWORD and tok.value == "output":
            return self._output_stmt()
        if tok.type == TT_IDENT:
            return self._assignment()

        raise ParseError(
            f"Unexpected token {tok.value!r} at start of statement",
            tok.line,
        )

    def _var_decl(self):
        line = self._current().line
        self._consume(TT_KEYWORD, "var")
        name_tok = self._consume(TT_IDENT)
        self._consume(TT_SEMI)
        return VarDeclNode(name_tok.value, line)

    def _assignment(self):
        name_tok = self._consume(TT_IDENT)
        self._consume(TT_ASSIGN)
        expr = self._expression()
        self._consume(TT_SEMI)
        return AssignNode(name_tok.value, expr, name_tok.line)

    def _input_stmt(self):
        line = self._current().line
        self._consume(TT_KEYWORD, "input")
        name_tok = self._consume(TT_IDENT)
        self._consume(TT_SEMI)
        return InputNode(name_tok.value, line)

    def _output_stmt(self):
        line = self._current().line
        self._consume(TT_KEYWORD, "output")
        expr = self._expression()
        self._consume(TT_SEMI)
        return OutputNode(expr, line)

    # -----------------------------------------------------------------------
    # Expressions
    # -----------------------------------------------------------------------

    def _expression(self):
        left = self._term()
        while self._peek_type() in (TT_PLUS, TT_MINUS):
            op_tok = self._consume()
            right = self._term()
            left = BinOpNode(op_tok.value, left, right, op_tok.line)
        return left

    def _term(self):
        left = self._factor()
        while self._peek_type() in (TT_STAR, TT_SLASH):
            op_tok = self._consume()
            right = self._factor()
            left = BinOpNode(op_tok.value, left, right, op_tok.line)
        return left

    def _factor(self):
        tok = self._current()

        if tok.type == TT_IDENT:
            self._consume()
            return IdentNode(tok.value, tok.line)

        if tok.type == TT_NUMBER:
            self._consume()
            return NumberNode(tok.value, tok.line)

        if tok.type == TT_LPAREN:
            self._consume(TT_LPAREN)
            expr = self._expression()
            self._consume(TT_RPAREN)
            return expr

        raise ParseError(
            f"Unexpected token {tok.value!r} in expression",
            tok.line,
        )
