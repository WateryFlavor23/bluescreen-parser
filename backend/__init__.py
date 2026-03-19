"""
Backend package for the bluescreen compiler.

Provides code generation (TAC) and optimization.
"""

from .codegen import CodeGenerator, Instruction
from .optimizer import Optimizer

__all__ = ["CodeGenerator", "Instruction", "Optimizer"]
