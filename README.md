# bluescreen-parser

A compiler front-end for the **bluescreen** custom programming language,
built for the course *CSTPLANGS – Translation of Programming Languages*.

The front-end implements three classic compiler phases:

| Phase | Module | Description |
|-------|--------|-------------|
| Lexical analysis | `lexer.py` | Converts source text into a stream of tokens |
| Syntax analysis | `parser.py` | Builds an Abstract Syntax Tree (AST) from the token stream |
| Semantic analysis | `semantic.py` | Type-checks the AST (declaration-before-use, no duplicate declarations) |

---

## Language reference

### Statements

Every statement ends with a semicolon (`;`).  
Whitespace (spaces, tabs, newlines) is not significant.  
Block comments (`/* … */`) may span multiple lines.

| Statement | Syntax | Effect |
|-----------|--------|--------|
| Variable declaration | `var name;` | Declares an integer variable |
| Assignment | `name = expression;` | Assigns a value to a declared variable |
| Read from console | `input name;` | Reads an integer into a declared variable |
| Write to console | `output expression;` | Evaluates and prints an expression |

### Expressions

All variables hold **integers**.  Allowed operators (with standard precedence):

```
expression  →  term  ( ('+' | '-')  term  )*
term        →  factor  ( ('*' | '/')  factor  )*
factor      →  IDENTIFIER | NUMBER | '(' expression ')'
```

### Identifiers

Variable names consist of letters (`a–z`, `A–Z`), digits (`0–9`), and
underscores (`_`).  They **cannot** start with a digit.

### Keywords

`var`, `input`, `output`

---

## Usage

```bash
python compiler.py <source_file>
```

The compiler prints the token stream and AST on success, or a descriptive
error message on failure.

**Example** – run the bundled sample program:

```bash
python compiler.py examples/example.bs
```

---

## Running tests

```bash
python -m pytest tests/test_compiler.py -v
```

---

## Project structure

```
bluescreen-parser/
├── compiler.py          # Entry point – ties all phases together
├── lexer.py             # Phase 1 – Lexical analysis
├── parser.py            # Phase 2 – Syntax analysis (recursive-descent)
├── semantic.py          # Phase 3 – Semantic analysis (type checking)
├── examples/
│   └── example.bs       # Sample bluescreen source program
└── tests/
    └── test_compiler.py # Pytest test suite (36 tests)
```