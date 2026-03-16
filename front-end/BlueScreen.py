from lexer import Lexer, Token, TokenType
from parser import *
from semantic import *

print("===============================================")
print("============  BLUESCREEN COMPILER  ============")
print("===============================================")

while True:
    choice = (input("WRITE Code or READ From 'code.txt'? [W/R]: ")).lower()
    
    if choice == 'w':
        program = []
        line = ""
        
        print("===============================================")
        print("Type \"END\" to start Compilation:\n")
        while True:
            line = str(input())
            if line == "END":
                break
            
            program.append(line)
            
        with open("code.txt", 'w') as file:
            for i in range(len(program)):
                file.write(program[i])
                
        break
    elif choice == 'r':
        break
    else:
        print("Invalid Option")
        print("===============================================")

with open("code.txt", "r") as file:
    program = file.read()
    
parser = Parser(list(Lexer(program)))
parser.parse()

print("===============================================")

analyzer = Analyzer(parser.statements)
analyzer.analyze()
print("===============================================")