
from error import Error

class BasicType:
  def add(self, sec):
    if type(sec) == type(self):
      return None, globals()[type(self).__name__](self.value + sec.value)

    return ["Interpreter", f"Can't add 2 different types ({type(self).__name__}, {type(sec).__name__})"], None

  def sub(self, sec):
    if type(sec) == type(self):
      return None, globals()[type(self).__name__](self.value - sec.value)

    return ["Interpreter", f"Can't subtract 2 different types ({type(self).__name__}, {type(sec).__name__})"], None

  def times(self, sec):
    if type(sec) == type(self):
      return None, globals()[type(self).__name__](self.value * sec.value)

    return ["Interpreter", f"Can't multiply 2 different types ({type(self).__name__}, {type(sec).__name__})"], None

  def div(self, sec):
    if type(sec) == type(self):
      return None, globals()[type(self).__name__](self.value / sec.value)

    return ["Interpreter", f"Can't divide 2 different types ({type(self).__name__}, {type(sec).__name__})"], None

class Integer(BasicType):
  def __init__(self, val):
    self.value = val
  
  def asString(self):
    return str(self.value)

class String(BasicType):
  def __init__(self, val):
    self.value = val

  def asString(self):
    return self.value

class Null:
  def __init__(self):
    self.value = None
  
  def asString(self):
    return "null"

  def add(self, sec):
    return ["Interpreter", f"Can't add null to anything."], None

  def sub(self, sec):
    return ["Interpreter", f"Can't subtract null from anything."], None

  def times(self, sec):
    return ["Interpreter", f"Can't multiply null by anything."], None

  def div(self, sec):
    return ["Interpreter", f"Can't divide null by anything."], None

class Bool:
  def __init__(self, val):
    self.value = val
  
  def asString(self):
    if self.value: return "true"
    return "false"

class BuiltInFunction:
  def __init__(self, func, interp):
    self.func = func
    self.interp = interp

  def execute(self):

    ret = self.func(self.interp)

    if ret == None: ret = Null()
    
    return ret

class FunctionWrapper:
  def __init__(self, code, func, interp):
    self.func = func
    self.code = code
    self.parScope = interp.currentScope
    self.funcScope = Scope(self.parScope)

  def execute(self):
    self.executor = Interpreter(self.code, "lol no ast for u interpreter", typef="function")
    self.executor.currentScope = self.funcScope
    
    for node in self.func.body:
      self.executor.execute(node)

    self.funcScope = self.executor.currentScope # functions save their scope
    return self.executor.ReturnValue

class Scope:
  def __init__(self, parent=None, top=False):
    self.parent = parent
    self.top = top
    self.variables = {}
    self.functions = {}

  def executeFunction(self, name):
    if self.functions.get(name.value, None):
      return self.functions[name.value].execute()
    else:
      if self.top or not self.parent:
        Error.generalError(f"No function named {name.value}")
      
      return self.parent.executeFunction(name)
  
  def setFunction(self, name, body):
    self.functions[name] = body
  
  def set_variable(self, name, value):
    if self.check_for_var(name):
      if self.top or self.variables.get(name, None):
        self.variables[name] = value
      else:
        self.parent.set_variable(name, value)
    else:
      self.variables[name] = value

  def check_for_var(self, name):
    if self.variables.get(name, None):
      return True
    else:
      if not self.top:
        return True
      
      if self.top:
        return False
  
  def get_variable(self, name):
    if self.variables.get(name, None):
      return self.variables[name]
    else:
      if not self.top:
        return self.parent.get_variable(name)
      
      if self.top:
        Error.generalError(f"No variable named {name}")

from astPrint import astPrint
from lexer import Lexer
from fardparser import Parser
class Interpreter:
  def __init__(self, code, ast, scope=None, typef=""):
    self.ast = ast
    self.code = code
    self.canReturn = typef == "function"
    self.typef = typef
    self.brokenExecution = False
    self.ReturnValue = Null()
    self.err = Error(code)
    
    if scope == None:
      scope = Scope()
    
    self.currentScope = scope

  def builtin_function(self, name):
    def inner(func):
      self.currentScope.functions[name] = BuiltInFunction(func, self)

    return inner
  
  def visit_BinaryExpression(self, expr):
    if "+" == expr.op:
      err, ret = self.execute(expr.left).add(self.execute(expr.right))

      if not err: return ret

      self.err.error(err[0], err[1], expr.left.start, expr.right.end - expr.left.start)
    if "-" == expr.op:
      err, ret = self.execute(expr.left).sub(self.execute(expr.right))
      
      if not err: return ret

      self.err.error(err[0], err[1], expr.left.start, expr.right.end - expr.left.start)
    if "*" == expr.op:
      err, ret = self.execute(expr.left).times(self.execute(expr.right))
      
      if not err: return ret

      self.err.error(err[0], err[1], expr.left.start, expr.right.end - expr.left.start)
    if "/" == expr.op:
      err, ret = self.execute(expr.left).div(self.execute(expr.right))
      
      if not err: return ret

      self.err.error(err[0], err[1], expr.left.start, expr.right.end - expr.left.start)
  
  def visit_LogicalOp(self, logop):
    left = self.execute(logop.left)
    right = self.execute(logop.right)

    if logop.type.value == "==":
      return Bool(type(left) == type(right) and left.value == right.value)
    elif logop.type.value == ">=":
      return Bool(type(left) == type(right) and left.value >= right.value)
    elif logop.type.value == "<=":
      return Bool(type(left) == type(right) and left.value <= right.value)
    elif logop.type.value == "!=":
      return Bool(type(left) != type(right) and left.value != right.value)
    elif logop.type.value == "<":
      return Bool(type(left) == type(right) and left.value < right.value)
    elif logop.type.value == ">":
      return Bool(type(left) == type(right) and left.value > right.value)

  def visit_NullLiteral(self, n):
    return Null()
  
  def visit_IfStatement(self, ifst):
    if self.execute(ifst.condition).value == False:
      return
    
    parScope = self.currentScope
    ifScope = Scope(parScope)
    executor = Interpreter(self.code, "lol no scope for u", typef=self.typef)
    executor.currentScope = ifScope
    
    for node in ifst.body:
      executor.execute(node)

    if type(executor.ReturnValue) != Null:
      self.ReturnValue = executor.ReturnValue
      self.brokenExecution = True

  def visit_BoolLiteral(self, bo):
    if bo.value.value == "true": return Bool(True)
    return Bool(False)
  
  def visit_PrintKeyword(self, printk):
    print(self.execute(printk.value).asString())

  def visit_ReturnStatement(self, ret):
    if not self.canReturn:
      Error.generalError("Can't use return outside a function nice try")

    self.ReturnValue = self.execute(ret.value)
    self.brokenExecution = True
  
  def visit_AccessVariable(self, var):
    return self.currentScope.get_variable(var.name.value)

  def visit_NumericLiteral(self, num):
    return Integer(num.value)
  
  def visit_VariableDefinition(self, var):
    self.currentScope.set_variable(
      var.name.value,
      self.execute(var.value)
    )

  def visit_ImportModule(self, imp):
    name = imp.name.value

    cont = ""
    try:
      with open(f"packages/{name}.gas", "r") as f:
        cont = f.read()
    except FileNotFoundError:
      Error.generalError(f"Package {name} not found!")

    lexr = Lexer(cont)
    parser = Parser(lexr.tokenizeFard(), cont)
    interp = Interpreter(cont, parser.parse(), scope=Scope(parent=None, top=True))
    interp.run()

    for var, value in interp.currentScope.variables.items():
      self.currentScope.variables[var] = value

    for name, func in interp.currentScope.functions.items():
      self.currentScope.functions[name] = func
  
  def visit_FunctionCall(self, func):
    ret = self.currentScope.executeFunction(func.name)
    return ret
  
  def visit_StringLiteral(self, string):
    return String(string.value)

  def visit_FunctionDefinition(self, func):
    name = func.name
    self.currentScope.setFunction(name, FunctionWrapper(self.code, func, self))

  def visit_Program(self, prog):
    for node in prog.body:
      self.execute(node)

  def execute(self, ast):
    if self.brokenExecution: return
    
    func = getattr(self, f"visit_{type(ast).__name__}", None)
    if func:
      return func(ast)
    else:
      print(f"Can't visit node {type(ast).__name__} because it hasn't got a visit method")
      exit(1)
  
  def run(self):
    self.execute(self.ast)
