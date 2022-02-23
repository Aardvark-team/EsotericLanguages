
with open("main.gas", "r") as gas:
  code = gas.read()

code = code.replace("\t", "  ")

from lexer import Lexer
#from parser import Parser

lexer = Lexer(code)
tokens = lexer.tokenizeFard()


####################################################################
#                           PARSER TEST                            #
####################################################################
from fardparser import Parser
from interpreter import Interpreter, Scope, Null, String, Integer

lexer = Lexer(code)
parser = Parser(lexer.tokenizeFard(), code)

ast = parser.parse()

interpreter = Interpreter(code, ast, scope=Scope(parent=None, top=True))

@interpreter.builtin_function("testing")
def test_func(intrp):
  print("Testing function")

interpreter.run()