"""
Optimizer for bluescreen three-address code.

Applies three basic optimizations in a single pass:

1. **Constant folding** – evaluate binary operations on two constants
   at compile time (e.g. ``t1 = 3 * 2`` → ``t1 = 6``).

2. **Constant propagation** – when a variable or temp is assigned a
   constant and is never reassigned, every later reference to it is
   replaced by the constant value.

3. **Dead temporary elimination** – remove instructions whose result
   is a temporary (``tN``) that is never referenced by any later
   instruction.

Time complexity : O(n) where n = number of TAC instructions.
Space complexity: O(n) for the constant map and usage sets.
"""

from __future__ import annotations

import operator
from collections import Counter

from .codegen import Instruction


# Map operator strings to Python callables.
_OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.floordiv,   # integer division
}


class Optimizer:
    """Optimizes a list of TAC :class:`Instruction` objects.

    Usage::

        opt  = Optimizer()
        code = opt.optimize(instructions)

    The optimizer is **non-destructive**: it returns a new instruction
    list and leaves the original untouched.
    """

    # ── public API ────────────────────────────────────────────────────

    def optimize(self, instructions: list[Instruction]) -> list[Instruction]:
        """Return an optimized copy of *instructions*.

        Applies constant folding + propagation in one forward pass,
        then dead-temp elimination in a backward scan.

        Time complexity: O(n).
        """
        folded = self._fold_and_propagate(instructions)
        cleaned = self._eliminate_dead_temps(folded)
        return cleaned

    # ── constant folding + propagation ────────────────────────────────

    @staticmethod
    def _fold_and_propagate(
        instructions: list[Instruction],
    ) -> list[Instruction]:
        """Forward pass: fold constants and propagate known values.

        Maintains a dict ``constants`` mapping variable/temp names to
        their known constant integer values.  A name is removed from
        the map when it is reassigned (or read from stdin).

        Time complexity: O(n).
        """
        constants: dict[str, int] = {}
        # Track how many times each variable is assigned (to detect reassignment).
        assign_count: Counter[str] = Counter()
        # First pass: count assignments per variable.
        for instr in instructions:
            if instr.result is not None:
                assign_count[instr.result] += 1

        result: list[Instruction] = []
        # Track variables that have been seen assigned (to know about reassignment).
        seen_assigned: Counter[str] = Counter()

        for instr in instructions:
            # --- resolve operands via constant propagation ---------
            a1 = instr.arg1
            a2 = instr.arg2
            if isinstance(a1, str) and a1 in constants:
                a1 = constants[a1]
            if isinstance(a2, str) and a2 in constants:
                a2 = constants[a2]

            op = instr.op

            # --- constant folding ----------------------------------
            if op in _OPS and isinstance(a1, int) and isinstance(a2, int):
                value = _OPS[op](a1, a2)
                new_instr = Instruction(op="=", result=instr.result, arg1=value)
                # record the folded constant
                if instr.result is not None:
                    constants[instr.result] = value
                result.append(new_instr)
                if instr.result:
                    seen_assigned[instr.result] += 1
                continue

            # --- copy propagation: result = constant ---------------
            if op == "=" and isinstance(a1, int):
                if instr.result is not None:
                    constants[instr.result] = a1
                result.append(Instruction(op="=", result=instr.result, arg1=a1))
                if instr.result:
                    seen_assigned[instr.result] += 1
                continue

            # --- read invalidates constant knowledge ---------------
            if op == "read" and instr.result is not None:
                constants.pop(instr.result, None)
                result.append(instr)
                if instr.result:
                    seen_assigned[instr.result] += 1
                continue

            # --- general instruction (with propagated operands) ----
            new_instr = Instruction(op=op, result=instr.result, arg1=a1, arg2=a2)
            # result is no longer a known constant
            if instr.result is not None:
                constants.pop(instr.result, None)
            result.append(new_instr)
            if instr.result:
                seen_assigned[instr.result] += 1

        return result

    # ── dead temporary elimination ────────────────────────────────────

    @staticmethod
    def _eliminate_dead_temps(
        instructions: list[Instruction],
    ) -> list[Instruction]:
        """Remove instructions that assign to a temporary never used later.

        A temporary is a name matching ``tN`` (e.g. t1, t2).
        Only temps are candidates for elimination; user variables are
        never removed.

        Time complexity: O(n).
        """
        # Collect all names that appear as operands (i.e. are *used*).
        used: set[str | int] = set()
        for instr in instructions:
            if instr.arg1 is not None:
                used.add(instr.arg1)
            if instr.arg2 is not None:
                used.add(instr.arg2)

        def _is_temp(name: str | None) -> bool:
            return (
                isinstance(name, str)
                and len(name) >= 2
                and name[0] == "t"
                and name[1:].isdigit()
            )

        result: list[Instruction] = []
        for instr in instructions:
            # Keep the instruction unless it writes to an unused temp.
            if _is_temp(instr.result) and instr.result not in used:
                continue
            result.append(instr)

        return result
