"""
Semantic analyzer for the bluescreen language.

Performs two checks on a valid AST:
  1. Every variable must be declared (``var``) before it is used.
  2. No variable may be declared more than once.

Errors are collected — not raised — so that we can report all of them at once.

Time complexity : O(n) where n = number of AST nodes.
Space complexity: O(v) where v = number of declared variables.
"""

from __future__ import annotations
from parser import ASTNode, Program


class SemanticError:
    """A single semantic error with a human-readable message."""

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"SemanticError({self.message!r})"


class SemanticAnalyzer:
    """Walks an AST and returns a list of :class:`SemanticError` instances.

    Usage::

        errors = SemanticAnalyzer().analyze(ast)
    """

    def analyze(self, ast: Program) -> list[SemanticError]:
        """Analyze the program AST and return a list of semantic errors.

        Time complexity: O(n).
        """
        self.declared: set[str] = set()
        self.errors: list[SemanticError] = []
        for stmt in ast.statements:
            self._check_statement(stmt)
        return self.errors

    # ── statement visitors ────────────────────────────────────────────

    def _check_statement(self, node: ASTNode) -> None:
        if node.type == "VarDecl":
            if node.name in self.declared:
                self.errors.append(
                    SemanticError(f"Variable '{node.name}' already declared")
                )
            else:
                self.declared.add(node.name)

        elif node.type == "Assign":
            if node.name not in self.declared:
                self.errors.append(
                    SemanticError(
                        f"Variable '{node.name}' used before declaration"
                    )
                )
            self._check_expr(node.expr)

        elif node.type == "Input":
            if node.name not in self.declared:
                self.errors.append(
                    SemanticError(
                        f"Variable '{node.name}' used before declaration"
                    )
                )

        elif node.type == "Output":
            self._check_expr(node.expr)

    # ── expression visitors ───────────────────────────────────────────

    def _check_expr(self, node: ASTNode) -> None:
        if node.type == "Number":
            return
        if node.type == "Ident":
            if node.name not in self.declared:
                self.errors.append(
                    SemanticError(
                        f"Variable '{node.name}' used before declaration"
                    )
                )
        elif node.type == "BinOp":
            self._check_expr(node.left)
            self._check_expr(node.right)
