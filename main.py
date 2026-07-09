import src
import colorama
from colorama import Fore, init
from src.scanner import Lexer, InvalidTokenError, UnterminatedStringLiteral, InvalidIdentifier, InvalidFloatLiteral, UnintialisedStringLiteral
from src.parser import *
from src.interpreter import Evaluator
import sys

init(autoreset = True)

def run_file(filename,pipeline_flags):
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
        if pipeline_flags:
            if pipeline_flags == 'explicit':
                lexer = Lexer(source)
                print(Fore.CYAN + "[-]" + Fore.GREEN+" Input source read")
                tokens = lexer.tokenise()
                print(Fore.CYAN + "[-]" + Fore.GREEN+"Tokenisation Finished")
                for tok in tokens:
                    print(Fore.CYAN + "[+]" + Fore.BLUE+f"{tok}")
                parser = Parser(tokens)
                print(Fore.CYAN + "[-]" + Fore.GREEN+"Passed tokens")
                ast = parser.parse()
                print(Fore.CYAN + "[-]" + Fore.GREEN+"Finished parsing")
                print(Fore.LIGHTMAGENTA_EX + "[+]" + Fore.BLUE+f'{ast}')
                evaluator = Evaluator()
                print(Fore.CYAN + "[-]" + Fore.GREEN+"Recieved AST")
                evaluator.evaluate(ast)
                print(Fore.CYAN + "[-]" + Fore.GREEN+"Evaluated AST")

        else:
            lexer = Lexer(source)
            tokens = lexer.tokenise()
            parser = Parser(tokens)
            ast = parser.parse()
            evaluator = Evaluator()
            evaluator.evaluate(ast)

    except (InvalidTokenError, UnterminatedStringLiteral, InvalidIdentifier, InvalidFloatLiteral, UnintialisedStringLiteral) as e:
        print(Fore.RED+f"{e.__class__.__name__}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.san>")
    
    pipeline_flags = sys.argv[2]
    
    run_file(sys.argv[1],pipeline_flags)
    sys.exit(1)