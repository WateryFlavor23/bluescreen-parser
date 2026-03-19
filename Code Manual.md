# bluescreen-parser

## 1) Project overview

`bluescreen-parser` is a small compiler-style backend for the custom **Bluescreen** language. The project is organized as a classic compilation pipeline:

1. **Lexical analysis** (`lexer.py`)  
   Converts source text into a stream of tokens.

2. **Syntax analysis** (`parser.py`)  
   Converts tokens into an Abstract Syntax Tree (AST).

3. **Semantic analysis** (`semantic.py`)  
   Checks for declaration rules and duplicate declarations.

4. **Code generation** (`codegen.py`)  
   Converts the AST into Three-Address Code (TAC).

5. **Optimization** (`optimizer.py`)  
   Performs constant folding, constant propagation, and dead temporary elimination.

6. **Orchestration** (`compiler.py`)  
   Runs the front-end pipeline and returns the compiled result.

The repository also includes tests and a sample program in `examples/example.bs`.

---

## 2) Repository map

### Core source files

- `lexer.py`
- `parser.py`
- `semantic.py`
- `compiler.py`
- `codegen.py`
- `optimizer.py`

### Tests

- `tests/test_compiler.py`
- `tests/test_backend.py`

### Example

- `examples/example.bs`

### Documentation

- `README.md`

---

## 3) File-by-file documentation

## `lexer.py`

### Responsibility
Turns raw source code into tokens.

### What it recognizes
- Keywords: `var`, `input`, `output`
- Identifiers
- Integer literals
- Operators: `+ - * / =`
- Punctuation: `( ) ;`
- Block comments: `/* ... */`

### Key behavior
- Skips whitespace.
- Tracks line numbers for error messages.
- Raises `LexerError` for:
  - unexpected characters
  - unterminated block comments

### Output
A list of `Token` objects ending with `TT_EOF`.

### Notes
The lexer is simple and linear in time, which is appropriate for a small language.

---

## `parser.py`

### Responsibility
Parses tokens into an AST using recursive descent.

### Grammar supported
- `var name;`
- `name = expression;`
- `input name;`
- `output expression;`

### Expression precedence
- `*` and `/` bind tighter than `+` and `-`
- Parentheses override precedence

### AST node types
- `Program`
- `VarDecl`
- `Assign`
- `Input`
- `Output`
- `Number`
- `Ident`
- `BinOp`

### Notes
The parser is structured clearly and matches the language described in the README.

---

## `semantic.py`

### Responsibility
Performs semantic checks on the AST.

### Checks performed
1. A variable must be declared before use.
2. A variable cannot be declared more than once.

### Error handling
- Semantic issues are collected into a list of `SemanticError` objects.
- Errors are returned instead of being raised immediately.

### Notes
This is useful because it lets the compiler report multiple semantic issues in one run.

---

## `compiler.py`

### Responsibility
Coordinates the front-end pipeline.

### Pipeline
`Lexer -> Parser -> SemanticAnalyzer`

### Return value
`compile_source(source)` returns:

- `tokens`
- `ast`
- `errors`

### Notes
This module is the clean entry point for automated tests or future CLI integration.

---

## `codegen.py`

### Responsibility
Generates Three-Address Code (TAC) from the AST.

### TAC concepts used
- Binary operation: `t1 = a + b`
- Copy assignment: `a = t1`
- Input / output instructions
- Temporary variables: `t1`, `t2`, `t3`, ...

### Traversal style
- Post-order traversal for expressions
- Statements are emitted in source order

### Important observation
The repository’s tests expect backend instructions like `read` and `print`, while the current `codegen.py` implementation emits `input` and `output` instructions internally. That is a consistency issue between the code and the test expectations.

### Notes
The generator is straightforward and easy to extend, but the instruction naming should be normalized so the backend and tests agree.

---

## `optimizer.py`

### Responsibility
Optimizes TAC instructions.

### Optimizations implemented
1. **Constant folding**  
   Example: `3 * 2` → `6`

2. **Constant propagation**  
   Example: if `a = 10`, later uses of `a` can be replaced with `10` when safe

3. **Dead temporary elimination**  
   Removes unused temporary assignments such as `t1`, `t2`, etc.

### Notes
The optimizer is practical for a teaching compiler, but it is still single-pass and limited to straight-line code. It does not handle control flow, branching, or more advanced data-flow optimization.

---

## `tests/test_compiler.py`

### Coverage
This file tests the front-end:

- lexing
- parsing
- semantic analysis
- integrated `compile_source`

### What the tests validate
- tokenization of keywords, identifiers, numbers, and operators
- comment skipping
- line tracking
- operator precedence
- parentheses
- missing semicolon errors
- semantic errors such as use-before-declaration and duplicate declaration

---

## `tests/test_backend.py`

### Coverage
This file tests the backend:

- code generation
- TAC formatting
- optimization

### What the tests validate
- variable declarations do not emit TAC
- input/output generation
- temporary generation for expressions
- constant folding
- propagation through prints
- elimination of dead temps
- non-destructive optimization behavior

### Important observation
These tests expect backend TAC instructions named `read` and `print`, which does not match the current `codegen.py` implementation. This should be resolved before relying on the backend in a final submission.

---

## `examples/example.bs`

### Sample program
The sample program:
- declares `a`, `b`, and `sum`
- reads two integers
- computes their sum
- prints the result

### Purpose
This is a simple end-to-end example that can be used to verify the compiler pipeline manually.

---

## 4) Bluescreen language reference

## Statements

Each statement ends with a semicolon:

- `var name;`
- `name = expression;`
- `input name;`
- `output expression;`

## Expressions

Supported operators:

- `+`
- `-`
- `*`
- `/`

Parentheses are supported.

## Identifiers

Identifiers may contain:
- letters
- digits
- underscores

They cannot start with a digit.

## Comments

Block comments are supported:

```text
/* comment */
```

---

## 5) Example compilation flow

Source:

```text
var a;
var b;
input a;
input b;
sum = a + b;
output sum;
```

Conceptual flow:

1. Lexer converts text into tokens.
2. Parser builds the AST.
3. Semantic analyzer checks declarations.
4. Code generator emits TAC.
5. Optimizer folds constants and removes dead temps.

---

## 6) Backend optimization review

Below are the most useful improvements to make the backend cleaner and more reliable.

### A. Normalize TAC instruction names
Unify the instruction vocabulary across the codebase.

Recommended convention:
- `read x`
- `print x`
- `a = b`
- `t1 = 1 + 2`

This will keep `codegen.py`, `optimizer.py`, and the tests aligned.

### B. Remove unused state
Some variables are defined but not used:

- `CodeGenerator._symbols`
- `Optimizer.assign_count`
- `Optimizer.seen_assigned`

Removing dead state makes the backend easier to maintain.

### C. Add unknown-node safeguards
The semantic analyzer and code generator should raise or report errors when they receive an unsupported AST node type. That makes debugging easier if the AST grows later.

### D. Improve semantic checks
Possible next checks:
- use-before-declaration inside more complex future constructs
- assignment to undeclared variables
- optional type rules if the language expands beyond integers

### E. Strengthen optimizer behavior
The optimizer is good for a straight-line compiler, but future improvements could include:
- common subexpression elimination
- algebraic simplification
- dead-code elimination beyond temporary variables
- support for branching / control flow graphs

### F. Add a command-line driver
A small CLI would make the compiler easier to use:

- read a `.bs` file
- print tokens
- print AST
- show semantic errors
- generate TAC
- print optimized TAC

### G. Add end-user error formatting
Right now the code has good internal errors, but a user-facing compiler would benefit from:
- filename
- line number
- a short code snippet
- a pointer to the exact position

---
