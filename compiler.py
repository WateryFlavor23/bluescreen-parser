"""Main entry point for the bluescreen compiler front-end.

Usage:
    python compiler.py <source_file>

The compiler reads the source file and runs three phases:
  1. Lexical analysis  - produces a token stream
  2. Syntax analysis   - produces an abstract syntax tree (AST)
  3. Semantic analysis - type-checks the AST

On success the AST is printed and the program exits with code 0.
On error the relevant message is printed to stderr and the program
exits with a non-zero code.
"""

import sys

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyzer


def compile_source(source):
    """Run all three front-end phases on *source* text.

    Returns ``(tokens, ast, semantic_errors)`` on success or raises
    ``LexerError`` / ``ParseError`` on hard failures.
    """
    # Phase 1 – Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    # Phase 2 – Syntax analysis
    parser = Parser(tokens)
    ast = parser.parse()

    # Phase 3 – Semantic analysis
    analyzer = SemanticAnalyzer()
    semantic_errors = analyzer.analyze(ast)

    return tokens, ast, semantic_errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python compiler.py <source_file>", file=sys.stderr)
        sys.exit(1)

    source_path = sys.argv[1]
    try:
        with open(source_path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        tokens, ast, semantic_errors = compile_source(source)
    except LexerError as exc:
        print(f"Lexer error (line {exc.line}): {exc}", file=sys.stderr)
        sys.exit(2)
    except ParseError as exc:
        print(f"Parse error (line {exc.line}): {exc}", file=sys.stderr)
        sys.exit(3)

    if semantic_errors:
        for err in semantic_errors:
            print(f"Semantic error (line {err.line}): {err}", file=sys.stderr)
        sys.exit(4)

    print("Compilation successful.")
    print("\n--- Token stream ---")
    for tok in tokens:
        print(f"  {tok}")
    print("\n--- Abstract Syntax Tree ---")
    _print_ast(ast)


def _print_ast(node, indent=0):
    prefix = "  " * indent
    ntype = getattr(node, "type", type(node).__name__)

    if ntype == "Program":
        print(f"{prefix}Program")
        for stmt in node.statements:
            _print_ast(stmt, indent + 1)

    elif ntype == "VarDecl":
        print(f"{prefix}VarDecl: {node.name}")

    elif ntype == "Assign":
        print(f"{prefix}Assign: {node.name} =")
        _print_ast(node.expr, indent + 1)

    elif ntype == "Input":
        print(f"{prefix}Input: {node.name}")

    elif ntype == "Output":
        print(f"{prefix}Output:")
        _print_ast(node.expr, indent + 1)

    elif ntype == "BinOp":
        print(f"{prefix}BinOp: {node.op}")
        _print_ast(node.left, indent + 1)
        _print_ast(node.right, indent + 1)

    elif ntype == "Ident":
        print(f"{prefix}Ident: {node.name}")

    elif ntype == "Number":
        print(f"{prefix}Number: {node.value}")

    else:
        print(f"{prefix}{node!r}")


if __name__ == "__main__":
    main()
