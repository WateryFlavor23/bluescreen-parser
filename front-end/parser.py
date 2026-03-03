from dataclasses import dataclass
from lexer import Lexer, Token, TokenType

@dataclass
class TreeNode:
    pass

@dataclass
class Int(TreeNode):
    value: int # Expected: {0-9}
    
@dataclass
class Expression:
    pass

@dataclass
class Factor(TreeNode):
    left: str | None # Expected: '('
    mid: str | Int | Expression # Expected: {identifier} or {0-9} or another EXPRESSION
    right: str | None # Expected: ')'

@dataclass
class Term(TreeNode):
    op: str | None #Expected: * or / or NULL
    left: Factor
    right: Factor | None

@dataclass
class Expression(TreeNode):
    op: str | None # Expected: + or - or NULL
    left: Term
    right: Term | None
    
@dataclass
class Declare(TreeNode):
    left: str # Expected: 'var'
    right: str # Expected: '{identifier}'
    
@dataclass
class Assign(TreeNode):
    left: str # Expected: '{identifier}'
    mid: str # Expected: '='
    right: Expression

@dataclass
class Read(TreeNode):
    left: str # Expected: 'input'
    right: str # Expected: '{identifier}'
    
@dataclass
class Write(TreeNode):
    left: str # Expected: 'output'
    right: Expression
    
@dataclass
class Statement(TreeNode):
    left: Declare | Assign | Read | Write
    right: str # Expected: ';'

class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.next_token_index = 0
        """points to the token to be consumed next"""
        
    def consume(self, expected_token_type: TokenType) -> Token:
        """Returns the next token if it is the expected type
        else, raises an error
        Main function for checking if code makes sense
        """
        
        next_token = self.tokens[self.next_token_index]
        self.next_token_index += 1
        if next_token.type != expected_token_type:
            raise RuntimeError(f"Expected {expected_token_type}, not {next_token!r}.")
        
        return next_token
    
    def peek(self, skip: int = 0) -> TokenType | None:
        """Checks upcoming token without consuming it"""
        peek_at = self.next_token_index + skip
        return self.tokens[peek_at].type if peek_at < len(self.tokens) else None
        
    def parse(self, parse_flag = 0):
        """Parses the program into the defined AST
        
        Parse Flag Rules:
        1 = Parse DECLARE, READ, WRITE statements
        2 = Parse ASSIGN statements
        3 = Parse EXPRESSION statements 
        4 = Parse TERM statements
        5 = Parse Factor
        
        """
        match parse_flag:
            case 0: # initial process: parse STATEMENT
                if self.peek() == TokenType.TT_KEYWORD:
                    left = self.parse(1)
                elif self.peek() == TokenType.TT_IDENT:
                    left = self.parse(2)
        
                right = self.consume(TokenType.TT_SEMI)
        
                self.consume(TokenType.TT_EOF)
        
                return Statement(left, right.value)
            case 1: # parse either DECLARE, READ, or WRITE
                left = self.consume(TokenType.TT_KEYWORD)
                if left.value == "var":
                    right = self.consume(TokenType.TT_IDENT)
                    
                    return Declare(left.value, right.value)
                elif left.value == "input":
                    right = self.parse(3)
                    
                    return Read(left.value, right)
                elif left.value == "output":
                    right = self.parse(3)
                    
                    return Write(left.value, right)
            case 2: # parse ASSIGN 
                left = self.consume(TokenType.TT_IDENT)
                mid = self.consume(TokenType.TT_ASSIGN)
                right = self.parse(3)
                
                return Assign(left.value, mid.value, right)
            case 3: # parse EXPRESSION
                left = self.parse(4)
                
                if self.peek() in (TokenType.TT_SEMI, TokenType.TT_RPAREN):
                    # return if expression is just ONE statement or number
                    return Expression(left, None, None)
                
                if self.peek() == TokenType.TT_PLUS:
                    op = "+"
                    self.consume(TokenType.TT_PLUS)
                elif self.peek() == TokenType.TT_MINUS:
                    op = "-"
                    self.consume(TokenType.TT_MINUS)
                    
                right = self.parse(4)
                
                return Expression(op, left, right)
            case 4: #parse TERM
                left = self.parse(5)
                
                if self.peek() in (TokenType.TT_SEMI, TokenType.TT_PLUS, TokenType.TT_MINUS, TokenType.TT_RPAREN):
                    # return if expression is just ONE statement or number
                    return Term(left, None, None)
                
                if self.peek() == TokenType.TT_STAR:
                    op = "*"
                    self.consume(TokenType.TT_STAR)
                elif self.peek() == TokenType.TT_SLASH:
                    op = "/"
                    self.consume(TokenType.TT_SLASH)
                    
                right = self.parse(5)
                
                return Term(op, left, right)
            case 5: # parse FACTOR
                if self.peek() in (TokenType.TT_LPAREN):
                    left = self.consume(TokenType.TT_LPAREN)
                    mid = self.parse(3)
                    right = self.consume(TokenType.TT_RPAREN)
                    
                    return Factor(left.value, mid, left.value)
                else:
                    if self.peek() == TokenType.TT_IDENT:
                        left = self.consume(TokenType.TT_IDENT)
                    else:
                        left = self.consume(TokenType.TT_NUMBER)
                    return Factor(left.value, None, None)
        
if __name__ == "__main__":
    code = "name = 12 * (2 + 3 / (2 * 3));"
    parser = Parser(list(Lexer(code)))
    print(parser.parse())
