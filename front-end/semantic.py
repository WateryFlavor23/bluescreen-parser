from lexer import Lexer, Token, TokenType
from parser import *

class Analyzer:
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements
        self.idx = 0
        self.symbols = {} # symbol table
        self.comp_errors = []
        self.run_errors = []
        
    def traverse(self, node) -> int | None:
        """
        
        function for traversing through an expression subtree
        if node != Factor or None, immediately traverse left and right branches
        final return == None if errors occured such as undefined var or var with no value
        
        """
        if node == None: return None # Handling for assign sole identifier to identifier
        
        if type(node) == Factor:
            if type(node.mid) == str:
                if node.mid not in self.symbols:
                    self.comp_errors.append(RuntimeError(f"Undefined var: {node.mid}"))
                    return None
                else:
                    if self.symbols[node.mid] == None:
                        self.comp_errors.append(RuntimeError(f"Var with no value: {node.mid}"))
                        return None
                    else: return self.symbols[node.mid] 
                
            elif type(node.mid) == int:
                return node.mid
            elif type(node.mid) == Expression:
                return self.traverse(node.mid)
        
        # post-order traversal
        left = self.traverse(node.left)
        right = self.traverse(node.right)
        
        if left == None: # if left is None, and error must have occured; especially so if on first expression
            return None
        elif right == None: # right == None means expression is a sole identifier or integer
            return left
        
        if node.op == "*":
            return left * right
        elif node.op == "/":
            if right == 0:
                self.run_errors.append("Attempted zero division")
            else: return left / right
        
        return left + right if node.op == "+" else left - right
            
    
    def analyze(self) -> None:
        while self.idx < len(self.statements):
            curr_statement = self.statements[self.idx].left
            
            if type(curr_statement) == Declare:
                if curr_statement.right in self.symbols:
                    self.comp_errors.append(RuntimeError(f"Redeclaration of var: {curr_statement.right}"))
                else:
                    self.symbols[curr_statement.right] = None
                    
            elif type(curr_statement) == Assign:
                val = self.traverse(curr_statement.right)
                if curr_statement.left not in self.symbols:
                    self.comp_errors.append(RuntimeError(f"Undefined var: {curr_statement.left}"))
                else:
                    self.symbols[curr_statement.left] = val
                
            elif type(curr_statement) == Read:
                if curr_statement.right not in self.symbols:
                    self.comp_errors.append(RuntimeError(f"Undefined var: {curr_statement.right}"))
                else:
                    self.symbols[curr_statement.right] = int(input(f"{curr_statement.right} = "))
                    
            elif type(curr_statement) == Write:
                self.traverse(curr_statement.right)
                
            self.idx += 1
        
        # Post Compilation Checking
        if not [self.comp_errors, self.run_errors]:
            print("===============================================")
            print("Successful Compilation.")
        else:
            if self.comp_errors:
                print("===============================================")
                print("Compilation Errors:")
            
                for i in range(len(self.comp_errors)):
                    print(self.comp_errors[i])
            
            if self.run_errors:
                print("===============================================")
                print("Run-Time Errors:")
            
                for i in range(len(self.run_errors)):
                    print(self.run_errors[i])
    
"""
Example Code Run:

    code = "var a;
    var b;
    var sum;
    
    a = 12;
    b = a * (3 + 12);

    sum = a * b;

    output sum;"
    
    parser = Parser(list(Lexer(code)))
    parser.parse()
    
    analyzer = Analyzer(parser.statements)

    analyzer.analyze()
    
"""