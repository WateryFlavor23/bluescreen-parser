"""Tests for the bluescreen compiler backend (code generation + optimization).

Uses the front-end lexer/parser to produce the AST, then tests the
code generator and optimizer.
"""

import sys
import os

# Add project root so we can import codegen/optimizer.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# Add front-end directory AFTER root (so it lands at index 0, highest priority)
# to ensure the front-end lexer/parser are used instead of root-level ones.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "front-end"))

import pytest

from lexer import Lexer
from parser import Parser
from backend.codegen import CodeGenerator, Instruction
from backend.optimizer import Optimizer


# ── helpers ───────────────────────────────────────────────────────────

def _compile_to_tac(source: str) -> list[Instruction]:
    """Front-end → CodeGenerator, returning raw TAC instructions."""
    tokens = list(Lexer(source))
    parser = Parser(tokens)
    parser.parse()
    return CodeGenerator().generate(parser.statements)


def _compile_and_optimize(source: str) -> list[Instruction]:
    """Full pipeline: front-end → CodeGenerator → Optimizer."""
    raw = _compile_to_tac(source)
    return Optimizer().optimize(raw)


def _tac_text(instructions: list[Instruction]) -> str:
    return CodeGenerator.format_tac(instructions)


# ===========================================================================
# Code generator tests
# ===========================================================================

class TestCodeGenerator:
    def test_var_decl_produces_no_tac(self):
        instrs = _compile_to_tac("var x;")
        assert instrs == []

    def test_input_generates_read(self):
        instrs = _compile_to_tac("var x; input x;")
        assert len(instrs) == 1
        assert instrs[0].op == "read"
        assert instrs[0].result == "x"

    def test_output_number_generates_print(self):
        instrs = _compile_to_tac("var x; output 42;")
        assert len(instrs) == 1
        assert instrs[0].op == "print"
        assert instrs[0].arg1 == 42

    def test_output_ident_generates_print(self):
        instrs = _compile_to_tac("var x; input x; output x;")
        assert instrs[1].op == "print"
        assert instrs[1].arg1 == "x"

    def test_simple_assignment(self):
        instrs = _compile_to_tac("var a; a = 5;")
        assert len(instrs) == 1
        assert str(instrs[0]) == "a = 5"

    def test_binary_expression_creates_temp(self):
        instrs = _compile_to_tac("var a; a = 1 + 2;")
        assert len(instrs) == 2
        # t1 = 1 + 2
        assert instrs[0].op == "+"
        assert instrs[0].arg1 == 1
        assert instrs[0].arg2 == 2
        assert instrs[0].result == "t1"
        # a = t1
        assert instrs[1].op == "="
        assert instrs[1].result == "a"
        assert instrs[1].arg1 == "t1"

    def test_spec_example_raw_tac(self):
        """The example from the spec:
        var a; a = 5 + 3 * 2; output a;
        Expected raw TAC:
            t1 = 3 * 2
            t2 = 5 + t1
            a = t2
            print a
        """
        instrs = _compile_to_tac("var a; a = 5 + 3 * 2; output a;")
        text = _tac_text(instrs)
        assert text == "t1 = 3 * 2\nt2 = 5 + t1\na = t2\nprint a"

    def test_nested_parentheses(self):
        instrs = _compile_to_tac("var r; r = (1 + 2) * (3 + 4);")
        # t1 = 1 + 2, t2 = 3 + 4, t3 = t1 * t2, r = t3
        assert len(instrs) == 4
        assert instrs[2].op == "*"

    def test_multiple_statements(self):
        src = "var a; var b; input a; input b; output a + b;"
        instrs = _compile_to_tac(src)
        ops = [i.op for i in instrs]
        assert ops == ["read", "read", "+", "print"]

    def test_format_tac_read(self):
        instr = Instruction(op="read", result="x")
        assert str(instr) == "read x"

    def test_format_tac_print(self):
        instr = Instruction(op="print", arg1="x")
        assert str(instr) == "print x"

    def test_format_tac_binop(self):
        instr = Instruction(op="+", result="t1", arg1=1, arg2=2)
        assert str(instr) == "t1 = 1 + 2"

    def test_format_tac_copy(self):
        instr = Instruction(op="=", result="a", arg1="t1")
        assert str(instr) == "a = t1"


# ===========================================================================
# Optimizer tests
# ===========================================================================

class TestOptimizer:
    def test_constant_folding_simple(self):
        """5 + 3 should be folded to 8."""
        instrs = _compile_and_optimize("var a; a = 5 + 3;")
        text = _tac_text(instrs)
        assert text == "a = 8"

    def test_constant_folding_nested(self):
        """5 + 3 * 2 should fold to 11."""
        instrs = _compile_and_optimize("var a; a = 5 + 3 * 2; output a;")
        text = _tac_text(instrs)
        assert text == "a = 11\nprint 11"

    def test_constant_propagation_through_print(self):
        """a = 10; output a → should propagate 10 into print."""
        instrs = _compile_and_optimize("var a; a = 10; output a;")
        text = _tac_text(instrs)
        assert text == "a = 10\nprint 10"

    def test_no_folding_with_variables(self):
        """input a; output a + 1 → cannot fold a + 1."""
        instrs = _compile_and_optimize("var a; input a; output a + 1;")
        # read a, t1 = a + 1, print t1  (t1 used, not eliminated)
        assert any(i.op == "+" for i in instrs)

    def test_dead_temp_elimination(self):
        """Unused temps should be removed after folding."""
        instrs = _compile_and_optimize("var a; a = 5 + 3 * 2;")
        # After folding: t1 = 6, t2 = 11, a = 11
        # t1 and t2 are dead → eliminated
        temps = [i for i in instrs if i.result and i.result.startswith("t")]
        assert len(temps) == 0

    def test_input_invalidates_constant(self):
        """After 'input a', 'a' should not be considered a constant."""
        instrs = _compile_and_optimize(
            "var a; a = 5; input a; output a;"
        )
        # 'a' was 5, then reassigned via input → print should use 'a' not 5
        print_instr = [i for i in instrs if i.op == "print"][0]
        assert print_instr.arg1 == "a"

    def test_division_folding(self):
        """10 / 2 should fold to 5."""
        instrs = _compile_and_optimize("var a; a = 10 / 2;")
        text = _tac_text(instrs)
        assert text == "a = 5"

    def test_subtraction_folding(self):
        """10 - 3 should fold to 7."""
        instrs = _compile_and_optimize("var a; a = 10 - 3;")
        text = _tac_text(instrs)
        assert text == "a = 7"

    def test_complex_all_constant(self):
        """(2 + 3) * (4 - 1) should fold to 15."""
        instrs = _compile_and_optimize("var r; r = (2 + 3) * (4 - 1);")
        text = _tac_text(instrs)
        assert text == "r = 15"

    def test_mixed_const_and_var(self):
        """input x; output x + 3 * 2 → 3*2 folds but x+6 cannot."""
        instrs = _compile_and_optimize("var x; input x; output x + 3 * 2;")
        # 3*2 → 6 (folded), x + 6 stays
        plus_instr = [i for i in instrs if i.op == "+"][0]
        assert plus_instr.arg2 == 6  # the folded constant

    def test_optimizer_nondestructive(self):
        """Optimizer should not modify the original instruction list."""
        raw = _compile_to_tac("var a; a = 5 + 3;")
        original_len = len(raw)
        Optimizer().optimize(raw)
        assert len(raw) == original_len

    def test_example_bs_tac(self):
        """example.bs logic: input a, input b, sum = a + b, output sum."""
        # Using source string directly (front-end lexer doesn't support
        # block comments, so we can't read examples/example.bs directly).
        src = "var a; var b; var sum; input a; input b; sum = a + b; output sum;"
        instrs = _compile_and_optimize(src)
        ops = [i.op for i in instrs]
        assert ops == ["read", "read", "+", "=", "print"]
