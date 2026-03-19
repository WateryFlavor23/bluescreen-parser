"""
Semantic analyzer for the bluescreen language.

Performs two checks on a valid AST:
  1. Every variable must be declared (``var``) before it is used.
  2. No variable may be declared more than once.

Errors are collected — not raised — so that we can report all of them at once.

Time complexity : O(n) where n = number of AST nodes.
Space complexity: O(v) where v = number of declared variables.
"""

from .lexer import *
from .parser import *

class Analyzer:
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements
        self.idx = 0
        self.symbols = {} # symbol table
        self.comp_errors = [] # for listing errors during compile time
        self.run_errors = [] # errors for division by zero
        
    def traverse(self, node) -> int | None:
        """ Function for traversing through an expression subtree
            if node != Factor or None, immediately traverse left and right branches
            final return == None if errors occured such as undefined var or var with no value
            
            Makes use of Post-Order Traversal to read the valules in an expression subtree
            
        Args:
            node::Expression|Term|Factor
                Takes the AST node as input and recursively reads
                its subsequent nodes.
        
        Returns:
            int|None
                The aim of the function is to return the value
                of each factor, term, and ultimately: the 
                expression
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
        """ Function for building the final symbol table and its values
        
        Args:
            self.statements::list[Statement]
                List of every line of the code file
            self.idx::int
                ID for accessing each statement in the list
            self.symbols::dict{}
                Symbol table to be filled with variable names and their
                values
            self.comp_errors::list[]
                Stores any detected errors at compilation-time;
                to be displayed after compilation
            self.run_errors::list[]
                Stores any detected errors at run-time; to be 
                displayed after incorrect operation values.
                i.e: zero division
        
        Returns:
            None
        """
        
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
                    try:
                        self.symbols[curr_statement.right] = int(input(f"{curr_statement.right} = "))
                    except:
                        self.run_errors.append("Invalid value input: only accepts INTEGER value")
            elif type(curr_statement) == Write:
                self.traverse(curr_statement.right)
                
            self.idx += 1
        
        # Post Compilation Checking
        if self.comp_errors or self.run_errors:
            if self.comp_errors:
                print("=======================================================")
                print("Compilation Errors:")
            
                for i in range(len(self.comp_errors)):
                    print(self.comp_errors[i])
            
            if self.run_errors:
                print("=======================================================")
                print("Run-Time Errors:")
            
                for i in range(len(self.run_errors)):
                    print(self.run_errors[i])
        