"""Tests for the bluescreen compiler front-end."""

import sys
import os

# Ensure the project root is on the path so we can import the modules.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from lexer import Lexer, LexerError, Token
from lexer import (
    TT_KEYWORD, TT_IDENT, TT_NUMBER,
    TT_PLUS, TT_MINUS, TT_STAR, TT_SLASH,
    TT_ASSIGN, TT_LPAREN, TT_RPAREN, TT_SEMI, TT_EOF,
)
from parser import Parser, ParseError
from semantic import SemanticAnalyzer, SemanticError
from compiler import compile_source


# ===========================================================================
# Lexer tests
# ===========================================================================

class TestLexer:
    def _tokens(self, source):
        return Lexer(source).tokenize()

    def _types(self, source):
        return [t.type for t in self._tokens(source) if t.type != TT_EOF]

    def test_keywords(self):
        types = self._types("var input output")
        assert types == [TT_KEYWORD, TT_KEYWORD, TT_KEYWORD]

    def test_identifier(self):
        toks = [t for t in self._tokens("myVar_1") if t.type != TT_EOF]
        assert len(toks) == 1
        assert toks[0].type == TT_IDENT
        assert toks[0].value == "myVar_1"

    def test_number(self):
        toks = [t for t in self._tokens("42") if t.type != TT_EOF]
        assert toks[0].type == TT_NUMBER
        assert toks[0].value == 42

    def test_operators(self):
        types = self._types("+ - * / = ( ) ;")
        assert types == [
            TT_PLUS, TT_MINUS, TT_STAR, TT_SLASH,
            TT_ASSIGN, TT_LPAREN, TT_RPAREN, TT_SEMI,
        ]

    def test_whitespace_ignored(self):
        types1 = self._types("var x ;")
        types2 = self._types("var\tx\n;")
        assert types1 == types2

    def test_block_comment_ignored(self):
        types = self._types("/* this is a comment */ var x ;")
        assert types == [TT_KEYWORD, TT_IDENT, TT_SEMI]

    def test_multiline_comment(self):
        src = "var /* line1\nline2 */ x ;"
        types = self._types(src)
        assert types == [TT_KEYWORD, TT_IDENT, TT_SEMI]

    def test_unterminated_comment_raises(self):
        with pytest.raises(LexerError):
            self._tokens("/* not closed")

    def test_unexpected_character_raises(self):
        with pytest.raises(LexerError):
            self._tokens("@")

    def test_eof_token_present(self):
        toks = self._tokens("")
        assert toks[-1].type == TT_EOF

    def test_line_tracking(self):
        toks = self._tokens("var\nx\n;")
        non_eof = [t for t in toks if t.type != TT_EOF]
        assert non_eof[0].line == 1  # var
        assert non_eof[1].line == 2  # x
        assert non_eof[2].line == 3  # ;

    def test_identifier_starting_with_underscore(self):
        toks = [t for t in self._tokens("_myVar") if t.type != TT_EOF]
        assert toks[0].type == TT_IDENT

    def test_number_not_identifier(self):
        # A number followed immediately by a letter should tokenize as
        # a NUMBER token and then an IDENT token.
        types = self._types("123abc")
        assert types == [TT_NUMBER, TT_IDENT]


# ===========================================================================
# Parser tests
# ===========================================================================

class TestParser:
    def _parse(self, source):
        tokens = Lexer(source).tokenize()
        return Parser(tokens).parse()

    def test_var_decl(self):
        ast = self._parse("var x;")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.type == "VarDecl"
        assert stmt.name == "x"

    def test_assignment(self):
        ast = self._parse("var x; x = 5;")
        assign = ast.statements[1]
        assert assign.type == "Assign"
        assert assign.name == "x"
        assert assign.expr.type == "Number"
        assert assign.expr.value == 5

    def test_input_stmt(self):
        ast = self._parse("var x; input x;")
        inp = ast.statements[1]
        assert inp.type == "Input"
        assert inp.name == "x"

    def test_output_stmt(self):
        ast = self._parse("var x; x = 3; output x;")
        out = ast.statements[2]
        assert out.type == "Output"
        assert out.expr.type == "Ident"

    def test_binary_expression(self):
        ast = self._parse("var a; a = 1 + 2;")
        expr = ast.statements[1].expr
        assert expr.type == "BinOp"
        assert expr.op == "+"

    def test_operator_precedence(self):
        # 1 + 2 * 3 should give BinOp(+, 1, BinOp(*, 2, 3))
        ast = self._parse("var a; a = 1 + 2 * 3;")
        expr = ast.statements[1].expr
        assert expr.op == "+"
        assert expr.right.op == "*"

    def test_parentheses(self):
        # (1 + 2) * 3 should give BinOp(*, BinOp(+, 1, 2), 3)
        ast = self._parse("var a; a = (1 + 2) * 3;")
        expr = ast.statements[1].expr
        assert expr.op == "*"
        assert expr.left.op == "+"

    def test_missing_semicolon_raises(self):
        with pytest.raises(ParseError):
            self._parse("var x")

    def test_invalid_token_in_expression_raises(self):
        with pytest.raises(ParseError):
            self._parse("var a; a = ;")

    def test_multiple_statements(self):
        src = "var a; var b; input a; a = a + 1; output a;"
        ast = self._parse(src)
        assert len(ast.statements) == 5

    def test_comment_in_expression(self):
        ast = self._parse("var a; a = 1 /* plus */ + 2;")
        expr = ast.statements[1].expr
        assert expr.type == "BinOp"
        assert expr.op == "+"


# ===========================================================================
# Semantic analyzer tests
# ===========================================================================

class TestSemanticAnalyzer:
    def _analyze(self, source):
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        return SemanticAnalyzer().analyze(ast)

    def test_valid_program_no_errors(self):
        src = "var x; input x; output x;"
        errors = self._analyze(src)
        assert errors == []

    def test_use_before_declaration_assign(self):
        errors = self._analyze("x = 5;")
        assert len(errors) == 1
        assert "x" in str(errors[0])

    def test_use_before_declaration_input(self):
        errors = self._analyze("input x;")
        assert len(errors) == 1

    def test_use_before_declaration_output_expr(self):
        errors = self._analyze("output x;")
        assert len(errors) == 1

    def test_use_before_declaration_in_expression(self):
        errors = self._analyze("var a; a = b + 1;")
        assert len(errors) == 1
        assert "b" in str(errors[0])

    def test_double_declaration_error(self):
        errors = self._analyze("var x; var x;")
        assert len(errors) == 1
        assert "already declared" in str(errors[0])

    def test_complex_valid_program(self):
        src = """
        var a;
        var b;
        var result;
        input a;
        input b;
        result = (a + b) * 2;
        output result;
        """
        errors = self._analyze(src)
        assert errors == []

    def test_multiple_errors_collected(self):
        # Both 'x' and 'y' are used without declaration.
        errors = self._analyze("var a; a = x + y;")
        assert len(errors) == 2


# ===========================================================================
# Integration tests (compile_source)
# ===========================================================================

class TestCompileSource:
    def test_full_pipeline_valid(self):
        src = "var n; input n; output n * 2;"
        tokens, ast, errors = compile_source(src)
        assert errors == []
        assert any(t.type == TT_KEYWORD and t.value == "var" for t in tokens)
        assert ast.type == "Program"

    def test_full_pipeline_semantic_error(self):
        src = "output undeclared;"
        tokens, ast, errors = compile_source(src)
        assert len(errors) == 1

    def test_full_pipeline_lex_error(self):
        with pytest.raises(LexerError):
            compile_source("var x; x = @;")

    def test_full_pipeline_parse_error(self):
        with pytest.raises(ParseError):
            compile_source("var x x;")
