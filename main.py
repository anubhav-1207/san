#main.py
#------------------------------------------------------------------------
# This is the entry point for San. 
# All programmes start from here 
#----------------------------------------------------------------------------------------------------
#---Importing Dependencies---------------------------------------------
import sys
import src
import colorama
from colorama import Fore, init
from src.scanner import *
from src.parser import *
from src.interpreter import *

#---Setup autoreset to white color--------------------------------------
init(autoreset = True)
#-----------------------------------------------------------------------

#---File Runner Function-------------------------------------------------------------------
def run_file(filename,pipeline_flags=False):
    """
    Reads the terminal input and runs the file.
    """
    if not filename.endswith('.san'):
        print(Fore.RED + "Error: File must have .san extension")
        return
    
    try:
        with open(filename, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(Fore.RED+f"Error: File '{filename}' not found")
        return
    
    try:
        if pipeline_flags: # when user wants to read the tokens and ASTs
            if pipeline_flags == 'explicit':
                lexer = Lexer(source)
                print(Fore.RED+"\n====================================================")
                print(Fore.CYAN + "[-]" + Fore.GREEN+" Input source read")
                print(Fore.RED+"\n====================================================")
                
                tokens = lexer.tokenise()
                
                print(Fore.RED+"\n====================================================")
                print(Fore.CYAN + "\n[!]" + Fore.GREEN+" Initialising Lexer")
                print(Fore.CYAN + "\t[-]" + Fore.GREEN+" Tokenisation Finished")
                
                for tok in tokens:
                    print(Fore.LIGHTMAGENTA_EX + "\t\t[+]" + Fore.BLUE+f"{tok}")

                parser = Parser(tokens)
                
                print(Fore.CYAN + "\n\t[-]" + Fore.GREEN+" Passed tokens")
                
                print(Fore.RED+"\n====================================================")
                ast = parser.parse()
                
                print(Fore.CYAN + "\n[!]" + Fore.GREEN+" Initialising Parser")
                print(Fore.CYAN + "\t[-]" + Fore.GREEN+" Finished parsing")
                print(Fore.LIGHTMAGENTA_EX + "\n[+]" + Fore.BLUE+f'{ast}')
                print(Fore.RED+"\n====================================================")
                
                print(Fore.RED+"\n====================================================")
                evaluator = Evaluator()
                print(Fore.CYAN + "\n\t[-]" + Fore.GREEN+" Recieved AST")
                print(Fore.CYAN + "\t[-]" + Fore.GREEN+" Evaluated AST")
                print(Fore.RED+"\n====================================================")
                
                print(Fore.BLUE+"\n=====================OUTPUT=========================")
                print(Fore.CYAN + "[-]" + Fore.GREEN+" Evaluating")
                evaluator.evaluate(ast)

        else: # running without the 'explicit' tag
            lexer = Lexer(source)
            tokens = lexer.tokenise()
            parser = Parser(tokens)
            ast = parser.parse()
            evaluator = Evaluator()
            evaluator.evaluate(ast)

    except (InvalidTokenError, UnterminatedStringLiteral, InvalidIdentifier, InvalidFloatLiteral, UnintialisedStringLiteral,UnexpectedTokenError,ControlFLowError, NullFuncBody,AccidentalReassError,UndefinedVariable,ConstantMutation,UndefinedFunc,ZeroDivisionError,ConstantArrayError) as e:
        print(Fore.RED+f"{e.__class__.__name__}: {e}")

#---Running The File------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.san>")
    
    elif len(sys.argv) == 3:
        pipeline_flags = sys.argv[2]
        
        run_file(sys.argv[1],pipeline_flags)
        sys.exit(1)
    
    else:
        run_file(sys.argv[1])
        sys.exit(1)
#=====================================================================================

###############################################################################
#                           END OF FILE
###############################################################################