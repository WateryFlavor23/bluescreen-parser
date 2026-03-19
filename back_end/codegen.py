"""
Code generator for the bluescreen language.

Traverses a valid AST (produced by the front-end parser) using
**post-order traversal** and emits Three-Address Code (TAC) as an
intermediate representation.

Each TAC instruction is one of:

    result = arg1 op arg2    (binary operation)
    result = arg1            (copy / assignment)
    read result              (read integer from stdin)
    print arg1               (write value to stdout)

Compatible with the front-end parser's AST node classes:
    Statement, Declare, Assign, Read, Write, Expression, Term, Factor

Time complexity : O(n) where n = number of AST nodes.
Space complexity: O(n) for the instruction list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ── TAC instruction ──────────────────────────────────────────────────

@dataclass
class Instruction:
    """A single three-address code instruction.

    Fields
    ------
    op : str
        The operation.  One of ``+  -  *  /  =  read  print``.
    result : str | None
        Destination variable (or temp).  ``None`` for ``print``.
    arg1 : str | int | None
        First operand.
    arg2 : str | int | None
        Second operand (``None`` for unary / copy / IO ops).
    """

    op: str
    result: str | None = None
    arg1: Any = None
    arg2: Any = None

    def __str__(self) -> str:
        if self.op == "read":
            return f"read {self.result}"
        if self.op == "print":
            return f"print {self.arg1}"
        if self.op == "=":
            return f"{self.result} = {self.arg1}"
        return f"{self.result} = {self.arg1} {self.op} {self.arg2}"


# ── Code generator ───────────────────────────────────────────────────

class CodeGenerator:
    """Generates three-address code from a bluescreen AST.

    Works with the front-end parser's AST node classes (Statement,
    Declare, Assign, Read, Write, Expression, Term, Factor).
    Uses duck typing — no parser imports required.

    Usage::

        gen = CodeGenerator()
        instructions = gen.generate(parser.statements)
        print(gen.format_tac(instructions))

    Design
    ------
    * **Post-order traversal**: every sub-expression is evaluated before
      it is used by its parent.
    * **Temporary variables** are named ``t1, t2, …`` via a monotonic
      counter.
    * A **symbol table** (set) tracks declared variables.
    """

    def __init__(self) -> None:
        self._temp_counter: int = 0
        self._instructions: list[Instruction] = []
        self._symbols: set[str] = set()

    # ── helpers ───────────────────────────────────────────────────────

    def _new_temp(self) -> str:
        """Return a fresh temporary variable name."""
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def _emit(self, instr: Instruction) -> None:
        self._instructions.append(instr)

    # ── public API ────────────────────────────────────────────────────

    def generate(self, statements: list) -> list[Instruction]:
        """Walk the AST statements and return a list of TAC instructions.

        Parameters
        ----------
        statements : list[Statement]
            The ``parser.statements`` list from the front-end parser.
            Each Statement has ``.left`` (the actual node) and
            ``.right`` (the semicolon).

        Time complexity: O(n).
        """
        self._temp_counter = 0
        self._instructions = []
        self._symbols = set()

        for stmt in statements:
            # Statement wraps the actual node in .left
            self._visit_statement(stmt.left)

        return list(self._instructions)

    @staticmethod
    def format_tac(instructions: list[Instruction]) -> str:
        """Return a human-readable string of the TAC program."""
        return "\n".join(str(i) for i in instructions)

    # ── statement visitors ────────────────────────────────────────────

    def _visit_statement(self, node) -> None:
        """Visit a statement node (Declare, Assign, Read, or Write)."""
        node_type = type(node).__name__

        if node_type == "Declare":
            # Declare: .left = "var", .right = variable name
            self._symbols.add(node.right)

        elif node_type == "Assign":
            # Assign: .left = variable name, .mid = "=", .right = Expression
            result = self._visit_expr(node.right)
            self._emit(Instruction(op="=", result=node.left, arg1=result))

        elif node_type == "Read":
            # Read: .left = "input", .right = variable name
            self._emit(Instruction(op="read", result=node.right))

        elif node_type == "Write":
            # Write: .left = "output", .right = Expression
            result = self._visit_expr(node.right)
            self._emit(Instruction(op="print", arg1=result))

        else:
            raise RuntimeError(f"Unknown statement node type: {node_type}")

    # ── expression visitors (post-order) ──────────────────────────────

    def _visit_expr(self, node) -> str | int:
        """Return the name/value that holds this expression's result.

        Handles Expression, Term, and Factor nodes from the front-end
        parser using post-order traversal.
        """
        node_type = type(node).__name__

        if node_type == "Expression":
            # Expression: .op (+/-/None), .left = Term, .right = Term|None
            left = self._visit_expr(node.left)
            if node.op is None:
                # Single-term expression, no operation
                return left
            right = self._visit_expr(node.right)
            temp = self._new_temp()
            self._emit(Instruction(op=node.op, result=temp, arg1=left, arg2=right))
            return temp

        if node_type == "Term":
            # Term: .op (*/÷/None), .left = Factor, .right = Factor|None
            left = self._visit_expr(node.left)
            if node.op is None:
                # Single-factor term, no operation
                return left
            right = self._visit_expr(node.right)
            temp = self._new_temp()
            self._emit(Instruction(op=node.op, result=temp, arg1=left, arg2=right))
            return temp

        if node_type == "Factor":
            # Factor: .left = "(" or None, .mid = int|str|Expression, .right = ")" or None
            if isinstance(node.mid, int):
                return node.mid
            if isinstance(node.mid, str):
                return node.mid
            # node.mid is an Expression (parenthesized)
            return self._visit_expr(node.mid)

        raise RuntimeError(f"Unknown expression node type: {node_type}")