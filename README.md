# bluescreen-parser

A compiler front-end by **bluescreen** custom programming language,

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
