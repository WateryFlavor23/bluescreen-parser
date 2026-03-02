from dataclasses import dataclass
from lexer import Lexer, Token, TokenType

@dataclass
class TreeNode:
    pass

@dataclass
class Expression(TreeNode):
    op: str
    left: "Int"
    right: "Int"
    
@dataclass
class Declare(TreeNode):
    left: str
    mid: str
    right: str
    
@dataclass
class Read(TreeNode):
    left: str
    mid: str
    right: str
    
@dataclass
class Output(TreeNode):
    left: str
    mid: str
    right: str | Expression

@dataclass
class Int(TreeNode):
    value: int | Expression
    
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
        
    def parse(self):
        """Parses the program into the defined AST"""
        
        if self.peek() == TokenType.TT_KEYWORD: # Declare & Read Statement
            left_op = self.consume(TokenType.TT_KEYWORD)
        
            op = self.consume(TokenType.TT_IDENT)
            right_op = self.consume(TokenType.TT_SEMI)
            
            if left_op.value == "var": return Declare(left_op.value, op.value, right_op.value)
            elif left_op.value == "output": return Output(left_op.value, op.value, right_op.value)
            else: return Read(left_op.value, op.value, right_op.value)
        
        left_op = self.consume(TokenType.TT_NUMBER)
        
        if self.peek() == TokenType.TT_PLUS:
            op = "+"
            self.consume(TokenType.TT_PLUS)
        else:
            op = "-"
            self.consume(TokenType.TT_MINUS)
        
        right_op = self.consume(TokenType.TT_NUMBER)
        
        return Expression(op, Int(left_op.value), Int(right_op.value))
        
if __name__ == "__main__":
    code = "3 + 5"
    parser = Parser(list(Lexer(code)))
    print(parser.parse())