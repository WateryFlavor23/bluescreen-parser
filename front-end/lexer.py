from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any, Generator
from string import digits

class TokenType(StrEnum):
    TT_KEYWORD = auto()
    TT_IDENT = auto()
    TT_NUMBER = auto()
    TT_PLUS = auto()
    TT_MINUS = auto()
    TT_STAR = auto()
    TT_SLASH = auto()
    TT_ASSIGN = auto() 
    TT_LPAREN = auto()
    TT_RPAREN = auto()
    TT_SEMI = auto()
    TT_EOF = auto()
    
@dataclass
class Token:
    type: TokenType
    value: Any = None
    
class Lexer:
    """ Class for tokenizing the input code stream into a token stream """
    def __init__(self, code: str) -> None:
        """ Initialization of the Lexer class
        
        Args:
            code::[str]
                Input code string to be read and divided into tokens
                To be used by the following functions: next_token &
                __iter__
                
        Returns:
            None
        """
        
        self.code = code
        self.ptr = 0
        
    def next_token(self) -> Token:
        """ Splits the input code into words and verifies what token
        it is
        
        Args:
            self.code::[str]
                Code string to be processed into different tokens
            self.ptr::int
                Pointer value to access individual char values 
            
        Returns:
            Token::TokenType
                Each "word" is another token defined as per the
                language rules
        """
         
        while self.ptr < len(self.code) and self.code[self.ptr] in (" ", "\n"): # skips whitespaces
            self.ptr += 1
            
        if self.ptr == len(self.code): # end of file
            return Token(TokenType.TT_EOF)
        
        sub_code = self.code[self.ptr] # stores the analyzed word
        self.ptr += 1
        
        # section for operators/punctuations
        if sub_code == "+": return Token(TokenType.TT_PLUS, sub_code)
        elif sub_code == "-": return Token(TokenType.TT_MINUS, sub_code)
        elif sub_code == "*": return Token(TokenType.TT_STAR, sub_code)
        elif sub_code == "/": return Token(TokenType.TT_SLASH, sub_code)
        elif sub_code == "=": return Token(TokenType.TT_ASSIGN, sub_code)
        elif sub_code == "(": return Token(TokenType.TT_LPAREN, sub_code)
        elif sub_code == ")": return Token(TokenType.TT_RPAREN, sub_code)
        elif sub_code == ";": return Token(TokenType.TT_SEMI, sub_code)
        
        elif sub_code in digits: # section for checking numbers
            while self.ptr < len(self.code) and self.code[self.ptr] in digits:
                sub_code += self.code[self.ptr]
                self.ptr += 1
                
            return Token(TokenType.TT_NUMBER, int(sub_code))
        
        elif sub_code.isalpha() or sub_code == "_": # section for checking keywords - identifiers
            while self.ptr < len(self.code) and (self.code[self.ptr].isalnum() or self.code[self.ptr] == "_"):
                sub_code += self.code[self.ptr]
                self.ptr += 1
            
            if sub_code in ["var","input","output"]:
                return Token(TokenType.TT_KEYWORD, sub_code)
            else:
                return Token(TokenType.TT_IDENT, sub_code) # if not keyword, identifier
        else: 
            raise RuntimeError(f"Invalid Character: {sub_code!r}")
        
    def __iter__(self) -> Generator[Token, None, None]:
        """ Calls next_token function until the end-of-file is found
        
        Args:
            self.next_token::Token
                Function for splitting the code into different tokens
        
        Returns:
            Generator[Token, None, None]::iterator
                Yields a generator object of each token found
                in the code string
        """
        
        while (token := self.next_token()).type != TokenType.TT_EOF:
            yield token
        yield token