#interpreter.py
#===================================================================
#Walks all the AST nodes and executes them one by one.
#===================================================================
from .ast_nodes import *
from src.stdlib import *
from src.stdlib.native_arrays import inject_array_methods
from src.stdlib.native_string import inject_string_methods
from src.stdlib.native_builtins import inject_builtin_methods
from src.stdlib.native_math import inject_math_methods
from src.stdlib.native_random import inject_random_methods
from src.stdlib.native_time import inject_time_methods
#---Error Classes---------------------------------------------------------------
class AccidentalReassError(Exception):
    def __init__(self,var):
        super().__init__(f"class source.fatal:: environmental variable '{var.token_value}' already found, explicit reassignment expected,\n\t\t---> interpreter exited with error[#INTRPTR001]")

class UndefinedVariable(Exception):
    def __init__(self,var):
        super().__init__(f"class source.fatal:: environmental variable '{var}' is not defined, explicit definition expected,\n\t\t---> interpreter exited with error[#INTRPTR002]")

class ConstantMutation(Exception):
    def __init__(self,var):
        super().__init__(f"class source.fatal:: environmental constant '{var.token_value}' is a constant,even explicit reassignment not allowed,\n\t\t---> interpreter exited with error[#INTRPTR003]")

class ZeroDivisionError(Exception):
    def __init__(self,right,left):
        super().__init__(f"class source.fatal:: cannot divide by zero, mathematically undefined,\n\t\t---> undefined operation '{right}/{left}' interpreter exited with error[#INTRPTR004]")

class UndefinedFunc(Exception):
    def __init__(self,var):
        super().__init__(f"class source.recursive:: function '{var}' is not defined, explicit definition expected,\n\t\t---> interpreter exited with error[#INTRPTR005]")

class InvalidTypeConv(Exception):
    def __init__(self,var,type_):
        super().__init__(f"class source.fatal:: variable '{var.token_value}' is not of the required type '{type_}', cannot perform implicit type conversion - type mismatch,\n\t\t---> interpreter exited with error[#INTRPTR006]")

class MalformedTypeOperation(Exception):
    def __init__(self):
        super().__init__(f"class source.fatal:: operation is not of the required type, cannot perform operation - supported type operations:\nint + float\nint - float\nint * float\nint / float\nint // float\nint % float\\nint ** float \nbool + int\nbool + float\nstr * int,\n\t\t---> interpreter exited with error[#INTRPTR006]")

class UnrecognisedBinaryOp(Exception):
    def __init__(self,op):
        super().__init__(f"class source.non-fatal:: unrecognised binary operator encountered - this error was not even possible to occur, if it did, congratulations, you went horribly wrong somewhere. You're on your own now - '{op}' ,\n\t\t---> interpreter exited with error[#INTRPTR006]")

class InsufficientFuncArgs(Exception):
    def __init__(self):
        super().__init__(f"class source.fatal:: in-built function did not recieved specified arguements,\n\t\t---> interpreter exited with error[#INTRPTR007]")

class InvalidLibraryImported(Exception):
    def __init__(self,library):
        super().__init__(f"class source.fatal :: no in-built library found named {library},\n\t\t---> interpreter exited with error[#INTRPTR007]")

class BreakException(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value
#-----------------------------------------------------------------------------------------------------


#---STDLIB built-in Functions--------------------------------------------------------------------------
class NativeFuncNode:
    """Wrapper for built-ins of various functions"""
    def __init__(self,name,expected_args,method,is_const):
        self.name = name 
        self.expected_args = expected_args
        self.method = method 

#---Visitor Nodes------------------------------------------------------------
class Environment:
    """Creates a namespace to store variables."""
    def __init__(self,parent=None):
        self.parent = parent #parent scope
        self.vars = {} #symbol table to store all variables and their values

    #---Enters a value in the namespace-----------------
    def define(self,name,value,is_const=False):
        """Adds the variable and its value to namespace."""
        if name in self.vars:
            raise AccidentalReassError(name)
        else:
            self.vars[name] = (value, is_const)
    
    #---Finds the value of the variable in the given environment/scope-------------------
    def lookup(self,name):
        """Searches for a variable in the global and parent scope. """
        if name in self.vars:
            return self.vars[name][0]
        if self.parent:
            return self.parent.lookup(name)
        else:
            raise UndefinedVariable(name)
    
    #---Edits the value of a var in the namespace-----------------------------------------
    def reassign_var(self,name,value):
        """
        Reassigns the variable if not a consant.
        """
        if name in self.vars:
            val, is_const = self.vars[name]
            if is_const:
                raise ConstantMutation(name)
            else:
                self.vars[name] = (value,is_const)
                return 
            
        elif self.parent:
            self.parent.reassign_var(name,value)
            return 
        
        else:
            raise UndefinedVariable(name)
#----------------------------------------------------------------------------------------------

#---Evaluator Class---------------------------------------------------------------------------
class Evaluator:
    """The main engine of the interpreter that does all the work expected by any interpreter."""
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions = {}
        self.builtInLibraries = ('math','random','time')

        #---Load in-built methods into the scope-----------
        inject_array_methods(self.functions)
        inject_string_methods(self.functions)
        inject_builtin_methods(self.functions)
        #--------------------------------------------------
    
    #---Evaluate Func----------------------------
    def evaluate(self,node):
        """Gets the node name and visits the node."""
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self,method_name,None)

        if visitor is None:
            raise Exception(f"No visitor for {node.__class__.__name__}")

        return visitor(node)
    
#============================================================================
    #---Visitor Nodes-------------------------------------------------
    def visit_ProgramNode(self,node):
        result = None

        for statement in node.statements:
            result = self.evaluate(statement)

        return result

    def is_truthy(self,operand) -> bool:
        """
        Defining truthy and false operations.
        Returns -> True or False
        """
        if operand is None or operand is False:
            return False
        if operand == 0:
            return False
        else:
            return True

    def visit_NumberNode(self,node):
        if '.' in node.number:
            return float(node.number)
        else:
            return int(node.number)
    
    def visit_StringLiteral(self,node):
        return node.value
    
    def visit_BooleanLiteral(self,node):
        return node.value
    
    def visit_NullLiteral(self,node):
        return None 
    
    def visit_NoneType(self,node):
        return None
    
    def visit_ArrayLiteralNode(self,node):
        elements = []
        for el in node.elements:
            elements.append(self.evaluate(el))
        return elements
    
    def visit_IndexingNode(self,node):
        name = node.array.token_value  # get variable name
        array = self.current_env.lookup(name)
        start_index = self.evaluate(node.start_index)
        return array[start_index]
    
    def visit_SlicingNode(self,node):
        name = node.array.token_value #get array name
        array_value = self.current_env.lookup(name)
        start_index = self.evaluate(node.start_index)
        end_index = self.evaluate(node.end_index)
        steps = self.evaluate(node.steps)
        return array_value[start_index:end_index:steps]

    def visit_UnaryOpNode(self,node):
        operand = self.evaluate(node.value)

        if node.op == "+" or node.op == "":
            return +operand
        elif node.op == "-":
            return -operand
        elif node.op == "!":
            return not self.is_truthy(operand)
    
    def visit_BinaryOpNode(self,node):
        left = self.evaluate(node.left)
        operator = node.op
        right = self.evaluate(node.right)

        if operator == '+':
            try:
                return left + right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '-':
            try:
                return left - right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '*':
            try:
                return left * right
            except TypeError:
                raise MalformedTypeOperation()
        
        elif operator == '/':
            if right != 0:
                return left // right
            else:
                raise ZeroDivisionError(right,left)
        elif operator == '**':
            try:
                return left ** right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '>':
            try:
                return left > right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '<':
            try:
                return left < right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '<=':
            try:
                return left <= right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '>=':
            try:
                return left >= right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '==':
            try:
                return left == right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '!=':
            try:
                return left != right
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '&&':
            try:
                return self.is_truthy(left) and self.is_truthy(right)
            except TypeError:
                raise MalformedTypeOperation()

        elif operator == '||':
            try:
                return self.is_truthy(left) or self.is_truthy(right)
            except TypeError:
                raise MalformedTypeOperation()

        else:
            raise UnrecognisedBinaryOp(operator)
    
    def visit_VarAccessNode(self,node):
        return self.current_env.lookup(node.var_name_token.token_value)
    
    def visit_VarAssignNode(self,node):
        name = node.var_name_token.token_value
        value = self.evaluate(node.value_node)
        const = node.is_const
        self.current_env.define(name,value,const)
        return value
    
    def visit_VarReassignNode(self,node):
        name = node.var_name_token.token_value
        value = self.evaluate(node.value_node)
        self.current_env.reassign_var(name,value)
        return value
    
    def visit_StdOutNode(self,node):
        value = self.evaluate(node.value_node)
        print(value)
        return value
    
    def visit_ScanNode(self,node):
        user_input = input()
        type_ = node.type_
        
        if type_ == 'int':
            try:
                value = int(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable,type_)


        elif type_ == 'float':
            try:
                value = float(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable,type_)


        elif type_ == 'str':
            try:
                value = str(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable,type_)


        elif type_ == 'bool':
            try:
                value = bool(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable,type_)


        self.current_env.define(node.variable,value)
        return value



    def visit_IfNode(self,node):
        condition = self.evaluate(node.condition)
        if self.is_truthy(condition):
            result = None 
            for stmt in node.if_body:
                result = self.evaluate(stmt)
            return result 
        
        elif node.else_body:
            result = None
            if node.else_body:    
                for stmt in node.else_body:
                    result = self.evaluate(stmt)
                return result
        return None


    def visit_WhileNode(self,node):
        result = None
        try:            
            while self.is_truthy(self.evaluate(node.condition)):
                for stmt in node.while_body:
                    result = self.evaluate(stmt)        
        except BreakException:
            pass
        return result


    def visit_FuncDefNode(self,node):
        self.functions[node.func_name] = node
        return None
    
    def visit_FuncCallNode(self, node):
        if node.func_name not in self.functions:
            raise UndefinedFunc(node.func_name)
        
        func_def = self.functions[node.func_name]
        func_env = Environment(parent=self.current_env)

        #---Built-in Function Handler------------------------------
        if hasattr(func_def,'is_native'):
            evaluated_args = [self.evaluate(arg) for arg in node.func_args] # turn all the arguements into a list

            if len(evaluated_args) not in func_def.expected_args:
                raise InsufficientFuncArgs()
        
            return func_def.method(evaluated_args)

        #---User Defined Functions----------------------------------
        for i, param in enumerate(func_def.func_params):
            arg_value = self.evaluate(node.func_args[i])
            func_env.define(param.token_value, arg_value)
        
        #---Switch Environments/Scopes--------
        old_env = self.current_env
        self.current_env = func_env
        #-----------------------------------
        
        result = None
        try:
            for stmt in func_def.func_body:
                result = self.evaluate(stmt)
        
        except ReturnException as e:
            result = e.value

        self.current_env = old_env 
        return result


    def visit_BreakNode(self,node):
        raise BreakException()


    def visit_ReturnNode(self,node):
        value = self.evaluate(node.value) if node.value else None
        raise ReturnException(value)


    def visit_UseNode(self,node):
        library = node.library

        if library in self.builtInLibraries:
            if library == "math":
                inject_math_methods(self.functions)
            elif library == "random":
                inject_random_methods(self.functions)
            elif library == "time":
                inject_time_methods(self.functions)
        else:
            raise InvalidLibraryImported(library)
    
    def visit_ForNode(self,node):
        result = None
        variable = node.variable.var_name_token
        iterable = self.evaluate(node.iterable)
        statements = node.statements
        
        for variable in iterable:
            for stmt in statements:
                print(stmt)
                result = self.evaluate(stmt)
        return result
        
# ########################################################################
# #                         END OF FILE                                  #
# ########################################################################