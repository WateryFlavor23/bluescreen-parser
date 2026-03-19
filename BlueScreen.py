from front_end.lexer import Lexer
from front_end.parser import *
from front_end.semantic import *

from back_end.codegen import CodeGenerator, Instruction
from back_end.optimizer import Optimizer

if __name__ == "__main__":
    print("=======================================================")
    print("================  BLUESCREEN COMPILER  ================")
    print("=======================================================")

    while True:
        choice = (input("WRITE Code or READ From 'bs_code.txt'? [W/R]: ")).lower()
        
        if choice == 'w':
            program = []
            line = ""
            
            print("=======================================================")
            print("Type \"END\" to start Compilation:\n")
            while True:
                line = str(input())
                if line == "END":
                    break
                
                program.append(line)
                
            with open("bs_code.txt", 'w') as file:
                for i in range(len(program)):
                    file.write(program[i])
                    
            break
        elif choice == 'r':
            break
        else:
            print("Invalid Option")
            print("=======================================================")

    with open("bs_code.txt", "r") as file:
        program = file.read()
    
    lexer = list(Lexer(program))
    
    parser = Parser(lexer)
    parser.parse()

    print("=======================================================")

    analyzer = Analyzer(parser.statements)
    analyzer.analyze()
    
    if not (analyzer.comp_errors or analyzer.run_errors):
        print("=======================================================")
        print("Successful Compilation. Generating and Optimizing code")
        
        generator = CodeGenerator()
        gen_code = generator.generate(parser.statements) # returns raw TAC instructions
        
        optimizer = Optimizer()
        opt_code = optimizer.optimize(gen_code) # returns an optimized list[Instruction]
        
        final_code = generator.format_tac(opt_code) # takes optimized list[Instruction] and formats it
        
        with open("code.txt", 'w') as file:
            file.write(final_code)
        
        print("Optimal Code generated. Check 'code.txt'")
    print("=======================================================")
    input("Press ENTER to continue...")
