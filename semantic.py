"""Semantic analyzer for the bluescreen language.

Checks performed:
  1. Variable must be declared with 'var' before it can be used.
  2. A variable may only be declared once.
  3. All operands and assignments involve integer-typed values (all
     variables and literals in this language are integers by definition,
     so this check is satisfied as long as only declared variables are used).
"""

from parser import (
    ProgramNode, VarDeclNode, AssignNode, InputNode, OutputNode,
    BinOpNode, IdentNode, NumberNode,
)


class SemanticError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.line = line


class SemanticAnalyzer:
    def __init__(self):
        self.declared = {}  # name -> line of declaration

    def analyze(self, program):
        """Walk the AST and perform semantic checks.

        Returns a list of SemanticError instances (empty means no errors).
        Each call resets internal state so the same instance can be reused.
        """
        self.declared = {}
        errors = []
        for stmt in program.statements:
            self._check_stmt(stmt, errors)
        return errors

    # -----------------------------------------------------------------------
    # Statement visitors
    # -----------------------------------------------------------------------

    def _check_stmt(self, node, errors):
        if isinstance(node, VarDeclNode):
            self._check_var_decl(node, errors)
        elif isinstance(node, AssignNode):
            self._check_assign(node, errors)
        elif isinstance(node, InputNode):
            self._check_input(node, errors)
        elif isinstance(node, OutputNode):
            self._check_output(node, errors)

    def _check_var_decl(self, node, errors):
        if node.name in self.declared:
            errors.append(SemanticError(
                f"Variable '{node.name}' is already declared (first declared at line {self.declared[node.name]})",
                node.line,
            ))
        else:
            self.declared[node.name] = node.line

    def _check_assign(self, node, errors):
        if node.name not in self.declared:
            errors.append(SemanticError(
                f"Variable '{node.name}' used before declaration",
                node.line,
            ))
        self._check_expr(node.expr, errors)

    def _check_input(self, node, errors):
        if node.name not in self.declared:
            errors.append(SemanticError(
                f"Variable '{node.name}' used before declaration",
                node.line,
            ))

    def _check_output(self, node, errors):
        self._check_expr(node.expr, errors)

    # -----------------------------------------------------------------------
    # Expression visitor
    # -----------------------------------------------------------------------

    def _check_expr(self, node, errors):
        if isinstance(node, IdentNode):
            if node.name not in self.declared:
                errors.append(SemanticError(
                    f"Variable '{node.name}' used before declaration",
                    node.line,
                ))
        elif isinstance(node, NumberNode):
            pass  # always an integer literal - valid
        elif isinstance(node, BinOpNode):
            self._check_expr(node.left, errors)
            self._check_expr(node.right, errors)
