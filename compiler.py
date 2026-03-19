"""
Compiler entry-point for the bluescreen language.

Orchestrates the full pipeline::

    source → Lexer → Parser → SemanticAnalyzer → CodeGenerator → Optimizer

The :func:`compile_source` function runs the front-end and returns
``(tokens, ast, errors)`` for inspection or further processing.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from lexer import Lexer, Token
from parser import Parser, Program
from semantic import SemanticAnalyzer, SemanticError

if TYPE_CHECKING:
    pass


def compile_source(source: str) -> tuple[list[Token], Program, list[SemanticError]]:
    """Run the front-end pipeline on *source* and return results.

    Returns:
        A 3-tuple ``(tokens, ast, errors)`` where *errors* is a list of
        :class:`SemanticError` instances (empty when the program is valid).

    Raises:
        LexerError: on invalid characters or unterminated comments.
        ParseError: on syntax errors.
    """
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    errors = SemanticAnalyzer().analyze(ast)
    return tokens, ast, errors
