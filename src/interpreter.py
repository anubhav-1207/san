#interpreter.py
#===================================================================
#Walks all the AST nodes and executes them one by one.
#===================================================================
from __future__ import annotations

from typing import Any, Callable, Optional, TypeAlias

from .ast_nodes import *
from .scanner import Tokens
from src.stdlib import *
from src.stdlib.native_arrays import inject_array_methods
from src.stdlib.native_string import inject_string_methods
from src.stdlib.native_builtins import inject_builtin_methods
from src.stdlib.native_math import inject_math_methods
from src.stdlib.native_random import inject_random_methods
from src.stdlib.native_time import inject_time_methods

FunctionTable: TypeAlias = dict[str, Any]
RuntimeValue: TypeAlias = Any

#---Error Classes---------------------------------------------------------------
class AccidentalReassError(Exception): #done
    def __init__(self, var: Any, line: int, col: int) -> None:
        super().__init__(f"class source.fatal:: environmental variable '{var}' already found, explicit reassignment expected,\n\t\t---> interpreter exited with error[#INTRPTR001] line:col {line}:{col}")

class UndefinedVariable(Exception): #done
    def __init__(self, var: Tokens | str, line: int, col: int) -> None:
        name = var.token_value if isinstance(var, Tokens) else var
        super().__init__(f"class source.fatal:: environmental variable '{name}' is not defined, explicit definition expected,\n\t\t---> interpreter exited with error[#INTRPTR002] line:col {line}:{col}")

class ConstantMutation(Exception): #done
    def __init__(self, var: Any, line: int, col: int) -> None:
        super().__init__(f"class source.fatal:: environmental constant '{var}' is a constant,even explicit reassignment not allowed,\n\t\t---> interpreter exited with error[#INTRPTR003] line:col {line}:{col}")

class ZeroDivisionError(Exception): #done
    def __init__(self, right: Any, left: Any, line: int, col: int) -> None:
        super().__init__(f"class source.fatal:: cannot divide by zero, mathematically undefined,\n\t\t---> undefined operation '{right}/{left}' interpreter exited with error[#INTRPTR004] line:col {line}:{col}")

class UndefinedFunc(Exception): #done
    def __init__(self, var: Any, line: int, col: int) -> None:
        super().__init__(f"class source.recursive:: function '{var}' is not defined, explicit definition expected,\n\t\t---> interpreter exited with error[#INTRPTR005] line:col {line}:{col}")

class InvalidTypeConv(Exception): #done
    def __init__(self, var: Any, type_: Any, line: int, col: int) -> None:
        super().__init__(f"class source.fatal:: variable '{var}' is not of the required type '{type_}', cannot perform implicit type conversion - type mismatch,\n\t\t---> interpreter exited with error[#INTRPTR006] line:col {line}:{col}")

class MalformedTypeOperation(Exception): #done
    def __init__(self, line: int, col: int) -> None:
        super().__init__(f"class source.fatal:: operation is not of the required type, cannot perform operation - supported type operations:\nint + float\nint - float\nint * float\nint / float\nint // float\nint % float\\nint ** float \nbool + int\nbool + float\nstr * int,\n\t\t---> interpreter exited with error[#INTRPTR006] line:col {line}:{col}")

class UnrecognisedBinaryOp(Exception): #done
    def __init__(self, op: Any, line: int, col: int) -> None:
        super().__init__(f"class source.non-fatal:: unrecognised binary operator encountered - this error was not even possible to occur, if it did, congratulations, you went horribly wrong somewhere. You're on your own now - '{op}' ,\n\t\t---> interpreter exited with error[#INTRPTR006] line:col {line}:{col}")

class InsufficientFuncArgs(Exception): #done
    def __init__(self, len_of_params: int, line: int, col: int) -> None:
        super().__init__(f"class source.fatal:: in-built function did not received number of specified arguments ({len_of_params}),\n\t\t---> interpreter exited with error[#INTRPTR007] line:col {line}:{col}")

class InvalidLibraryImported(Exception): #done
    def __init__(self, library: str, line: int, col: int) -> None:
        super().__init__(f"class source.fatal :: no in-built library found named '{library}',\n\t\t---> interpreter exited with error[#INTRPTR007] line:col {line}:{col}")

class BreakException(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value
#------------------------------------------------------------------------------------


#---STDLIB built-in Functions--------------------------------------------------------------------------
class NativeFuncNode:
    """Wrapper for built-ins of various functions"""
    def __init__(self, name: str, expected_args: tuple[int, ...], method: Callable[[list[Any]], Any], is_const: bool) -> None:
        self.name: str = name
        self.expected_args: tuple[int, ...] = expected_args
        self.method: Callable[[list[Any]], Any] = method
        self.is_const: bool = is_const

#---Visitor Nodes------------------------------------------------------------
class Environment:
    """Creates a namespace/environment/scope to store variables.
       Create a new scope using new_scope = Environment(parent=current_scope)
       Then use using the following methods using new_scope.define(name,value) to define a variable and so on....
       """
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.parent: Optional[Environment] = parent #parent scope
        self.vars: dict[str, tuple[Any, bool]] = {} #symbol table to store all variables and their values

    #---Enters a value in the namespace-----------------
    def define(self, name: Tokens, value: Any, is_const: bool = False) -> None:
        """Adds the variable and its value to namespace."""
        if name.token_value in self.vars:
            raise AccidentalReassError(name.token_value, name.line, name.col)
        else:
            self.vars[name.token_value] = (value, is_const)
    
    #---Finds the value of the variable in the given environment/scope-------------------
    def lookup(self, name: Tokens) -> Any:
        """Searches for a variable in the global and parent scope. """
        if name.token_value in self.vars:
            return self.vars[name.token_value][0]
        if self.parent:
            return self.parent.lookup(name)
        else:
            raise UndefinedVariable(name, name.line, name.col)
    
    #---Edits the value of a var in the namespace-----------------------------------------
    def reassign_var(self, name: Tokens, value: Any) -> None:
        """
        Reassigns the variable if not a constant.
        """
        name_value = name.token_value
        if name_value in self.vars:
            val, is_const = self.vars[name_value]
            if is_const:
                raise ConstantMutation(name_value, name.line, name.col)
            else:
                self.vars[name_value] = (value, is_const)
                return 
            
        elif self.parent:
            self.parent.reassign_var(name, value)
            return 
        
        else:
            raise UndefinedVariable(name, name.line, name.col)
    
    def update_local(self, name: Tokens, value: Any) -> None:
        """
        Updates a variable in the current scope only.
        """
        name_value = name.token_value

        if name_value in self.vars:
            _, is_const = self.vars[name_value]
            self.vars[name_value] = (value, is_const)
        else:
            raise UndefinedVariable(name, name.line, name.col)
            
#----------------------------------------------------------------------------------------------

#---Evaluator Class---------------------------------------------------------------------------
class Evaluator:
    """The main engine of the interpreter that does all the work expected by any interpreter."""
    def __init__(self) -> None:
        self.global_env: Environment = Environment()
        self.current_env: Environment = self.global_env
        self.functions: FunctionTable = {}
        self.builtInLibraries: tuple[str, ...] = ('math', 'random', 'time')

        #---Load in-built methods into the scope-----------
        inject_array_methods(self.functions)
        inject_string_methods(self.functions)
        inject_builtin_methods(self.functions)
        #--------------------------------------------------
    
    #---Evaluate Func----------------------------
    def evaluate(self, node: Any) -> Any:
        """Gets the node name and visits the node."""
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, None)

        if visitor is None:
            raise Exception(f"No visitor for {node.__class__.__name__}")

        return visitor(node)
    
#============================================================================
    #---Visitor Nodes-------------------------------------------------
    def visit_ProgramNode(self, node: Any) -> Any:
        result: Any = None

        for statement in node.statements:
            result = self.evaluate(statement)

        return result

    def is_truthy(self, operand: Any) -> bool:
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

    def visit_NumberNode(self, node: Any) -> int | float:
        if '.' in node.number:
            return float(node.number)
        else:
            return int(node.number)
    
    def visit_StringLiteral(self, node: Any) -> str:
        return node.value
    
    def visit_BooleanLiteral(self, node: Any) -> bool:
        return bool(node.value)
    
    def visit_NullLiteral(self, node: Any) -> None:
        return None 
    
    def visit_NoneType(self, node: Any) -> None:
        return None
    
    def visit_ArrayLiteralNode(self, node: Any) -> list[Any]:
        elements: list[Any] = []
        for el in node.elements:
            elements.append(self.evaluate(el))
        return elements
    
    def visit_IndexingNode(self, node: Any) -> Any:
        name = node.array
        name_value = node.array.token_value  # get variable name
        array = self.current_env.lookup(name)
        start_index = self.evaluate(node.start_index)
        return array[start_index]
    
    def visit_SlicingNode(self, node: Any) -> Any:
        name = node.array
        name_value = node.array.token_value #get array name
        array_value = self.current_env.lookup(name)
        start_index = self.evaluate(node.start_index)
        end_index = self.evaluate(node.end_index)
        steps = self.evaluate(node.steps)
        return array_value[start_index:end_index:steps]

    def visit_UnaryOpNode(self, node: Any) -> Any:
        operand = self.evaluate(node.value)

        if node.op == "+" or node.op == "":
            return +operand
        elif node.op == "-":
            return -operand
        elif node.op == "!":
            return not self.is_truthy(operand)
    
    def visit_BinaryOpNode(self, node: Any) -> Any:
        left = self.evaluate(node.left)
        operator = node.op.token_value
        right = self.evaluate(node.right)

        if operator == '+':
            try:
                return left + right
            except TypeError:
                raise MalformedTypeOperation(node.op.line,node.op.col)

        elif operator == '-':
            try:
                return left - right
            except TypeError:
                raise MalformedTypeOperation(node.op.line,node.op.col)

        elif operator == '*':
            try:
                return left * right
            except TypeError:
                raise MalformedTypeOperation(node.op.line,node.op.col)
        
        elif operator == '/':
            if right != 0:
                return left / right
            else:
                raise ZeroDivisionError(right,left,node.op.line,node.op.col)
        elif operator == '**':
            try:
                return left ** right
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '>':
            try:
                return left > right
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '<':
            try:
                return left < right
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '<=':
            try:
                return left <= right
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '>=':
            try:
                return left >= right
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '==':
            try:
                return left == right
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '!=':
            try:
                return left != right
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '&&':
            try:
                return self.is_truthy(left) and self.is_truthy(right)
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        elif operator == '||':
            try:
                return self.is_truthy(left) or self.is_truthy(right)
            except TypeError:
                raise MalformedTypeOperation(node.op.line, node.op.col)

        else:
            raise UnrecognisedBinaryOp(node.op.token_value, node.op.line, node.op.col)
    
    def visit_VarAccessNode(self, node: Any) -> Any:
        return self.current_env.lookup(node.var_name_token)
    
    def visit_VarAssignNode(self, node: Any) -> Any:
        name = node.var_name_token
        value = self.evaluate(node.value_node)
        const = node.is_const
        self.current_env.define(name, value, const)
        return value
    
    def visit_VarReassignNode(self, node: Any) -> Any:
        name = node.var_name_token
        value = self.evaluate(node.value_node)
        self.current_env.reassign_var(name, value)
        return value
    
    def visit_ScanNode(self, node: Any) -> Any:
        user_input = input()
        type_ = node.type_
        
        if type_ == 'int':
            try:
                value = int(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable, type_, node.variable.line, node.variable.col)

        elif type_ == 'float':
            try:
                value = float(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable, type_, node.variable.line, node.variable.col)

        elif type_ == 'str':
            try:
                value = str(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable, type_, node.variable.line, node.variable.col)

        elif type_ == 'bool':
            try:
                value = bool(user_input)
            except ValueError:
                raise InvalidTypeConv(node.variable, type_, node.variable.line, node.variable.col)
        else:
            value = user_input

        try:
            self.current_env.define(node.variable, value)
        except AccidentalReassError:
            self.current_env.reassign_var(node.variable, value)
        return value



    def visit_IfNode(self, node: Any) -> Any:
        if self.is_truthy(self.evaluate(node.if_condition)):
            result = None
            for stmt in node.if_body:
                result = self.evaluate(stmt)
            return result

        for i, cond in enumerate(node.elif_condition):
            if self.is_truthy(self.evaluate(cond)):
                result = None
                for stmt in node.elif_body[i]:
                    result = self.evaluate(stmt)
                return result
    
        if node.else_body:
            result = None
            for stmt in node.else_body:
                result = self.evaluate(stmt)
                return result

        return None
    


    def visit_WhileNode(self, node: Any) -> Any:
        result: Any = None
        old_env = self.current_env

        try:            
            while self.is_truthy(self.evaluate(node.condition)):
                loop_env = Environment(parent=self.current_env)
                self.current_env = loop_env
                try:
                    for stmt in node.while_body:
                        result = self.evaluate(stmt)
                except BreakException:
                    break
                finally:
                    self.current_env = old_env
            return result
        except BreakException:
            pass
        
        finally:
            self.current_env = old_env


    def visit_FuncDefNode(self, node: Any) -> None:
        self.functions[node.func_name.token_value] = node
        return None
    
    def visit_FuncCallNode(self, node: Any) -> Any:
        if node.func_name.token_value not in self.functions:
            raise UndefinedFunc(node.func_name.token_value, node.func_name.line, node.func_name.col)
        
        func_def = self.functions[node.func_name.token_value]
        func_env = Environment(parent=self.current_env)

        #---Built-in Function Handler------------------------------
        if hasattr(func_def, 'is_native'):
            evaluated_args = [self.evaluate(arg) for arg in node.func_args] #turn all the arguments into a list
            if len(evaluated_args) not in func_def.expected_args:
                line = getattr(func_def, 'line', None)
                col = getattr(func_def, 'col', None)
                if line is None or col is None:
                    line = node.func_name.line
                    col = node.func_name.col
                raise InsufficientFuncArgs(len(func_def.expected_args), line, col)
        
            return func_def.method(evaluated_args)

        #---User Defined Functions----------------------------------
        for i, param in enumerate(func_def.func_params):
            try:
                arg_value = self.evaluate(node.func_args[i])
            except Exception:
                raise InsufficientFuncArgs(len(func_def.func_params), node.func_name.line, node.func_name.col)
            func_env.define(param, arg_value)
        
        #---Switch Environments/Scopes--------
        old_env = self.current_env
        self.current_env = func_env
        #-----------------------------------
        
        result: Any = None
        try:
            for stmt in func_def.func_body:
                result = self.evaluate(stmt)
        
        except ReturnException as e:
            result = e.value

        self.current_env = old_env 
        return result


    def visit_BreakNode(self, node: Any) -> None:
        raise BreakException()


    def visit_ReturnNode(self, node: Any) -> Any:
        value = self.evaluate(node.value) if node.value else None
        raise ReturnException(value)


    def visit_UseNode(self, node: Any) -> None:
        library_name = node.library.token_value

        if library_name in self.builtInLibraries:
            if library_name == "math":
                inject_math_methods(self.functions)
            elif library_name == "random":
                inject_random_methods(self.functions)
            elif library_name == "time":
                inject_time_methods(self.functions)
        else:
            raise InvalidLibraryImported(library_name, node.library.line, node.library.col)
    
    def visit_ForNode(self, node: Any) -> Any:
        result: Any = None

        variable = node.variable.var_name_token
        iterable = self.evaluate(node.iterable)
        statements = node.statements

        previous_env = self.current_env #store the current scope so we can switch later
        loop_env = Environment(parent=previous_env) #create new scope for the loop
        
        try:
            self.current_env = loop_env #switch to new scope 

            for i in iterable:
                if variable.token_value in loop_env.vars: #check if the variable is already defined in the current scope
                    self.current_env.update_local(variable, i)
                else: #if not defined, create the variable
                    self.current_env.define(variable, i)        
                
                for stmt in statements: #actually starts executing the loop now
                    result = self.evaluate(stmt)
            
            return result
        except BreakException:
            pass
        
        finally:
            self.current_env = previous_env #switch to the previous scope after the loop is done executing

    def visit_TupleLiteralNode(self, node: Any) -> tuple[Any, ...]:
        tuple_ = []
        for elem in node.elements:
            tuple_.append(self.evaluate(elem))
        return tuple(tuple_)
    #---------------------------------------------------------------------
        
# ########################################################################
# #                         END OF FILE                                  #
# ########################################################################
