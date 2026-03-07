"""
Code generator for the bluescreen language.

Traverses a valid AST using **post-order traversal** and emits
Three-Address Code (TAC) as an intermediate representation.

Each TAC instruction is one of:

    result = arg1 op arg2    (binary operation)
    result = arg1            (copy / assignment)
    read result              (read integer from stdin)
    print arg1               (write value to stdout)

Time complexity : O(n) where n = number of AST nodes.
Space complexity: O(n) for the instruction list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from parser import Program, ASTNode


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
        if self.op == "input":
            return f"input {self.result}"
        if self.op == "output":
            return f"output {self.arg1}"
        if self.op == "=":
            return f"{self.result} = {self.arg1}"
        return f"{self.result} = {self.arg1} {self.op} {self.arg2}"


# ── Code generator ───────────────────────────────────────────────────

class CodeGenerator:
    """Generates three-address code from a bluescreen AST.

    Usage::

        gen = CodeGenerator()
        instructions = gen.generate(ast)
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

    def generate(self, ast: Program) -> list[Instruction]:
        """Walk the AST and return a list of TAC instructions.

        Time complexity: O(n).
        """
        self._temp_counter = 0
        self._instructions = []
        self._symbols = set()

        for stmt in ast.statements:
            self._visit_statement(stmt)

        return list(self._instructions)

    @staticmethod
    def format_tac(instructions: list[Instruction]) -> str:
        """Return a human-readable string of the TAC program."""
        return "\n".join(str(i) for i in instructions)

    # ── statement visitors ────────────────────────────────────────────

    def _visit_statement(self, node: ASTNode) -> None:
        if node.type == "VarDecl":
            self._symbols.add(node.name)

        elif node.type == "Assign":
            result = self._visit_expr(node.expr)
            self._emit(Instruction(op="=", result=node.name, arg1=result))

        elif node.type == "Input":
            self._emit(Instruction(op="input", result=node.name))

        elif node.type == "Output":
            result = self._visit_expr(node.expr)
            self._emit(Instruction(op="output", arg1=result))

    # ── expression visitors (post-order) ──────────────────────────────

    def _visit_expr(self, node: ASTNode) -> str | int:
        """Return the name/value that holds this expression's result.

        For a literal ``Number``, the integer value is returned directly.
        For an ``Ident``, the variable name is returned.
        For a ``BinOp``, a new temporary is created and its name returned.
        """
        if node.type == "Number":
            return node.value

        if node.type == "Ident":
            return node.name

        if node.type == "BinOp":
            left = self._visit_expr(node.left)
            right = self._visit_expr(node.right)
            temp = self._new_temp()
            self._emit(Instruction(op=node.op, result=temp, arg1=left, arg2=right))
            return temp

        raise RuntimeError(f"Unknown AST node type: {node.type}")  # pragma: no cover
