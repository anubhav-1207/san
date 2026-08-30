#ast_nodes.py
#==================================================================================
# An AST (Abstract Syntax Tree) is a tree data structure that represents and preserves the 
# hierarchial data of the expressions  
#==================================================================================

# NAMESPACE TO STORE THE CONSTANTS NAME
const_variables = []

# NAMESPACE TO STORE SCALAR/VARIABLES NAME 
dec_variables = []

#==============================================================================
# Parent class which is inherited by all the other classes
class AST:
    def __init__(self,line,col):
        self.line = line 
        self.col = col

#---Number Node--------------------------------------------------------
class NumberNode(AST): ##################
    def __init__(self,number):
        self.number = number.token_value
    def __repr__(self):
        return f"(Number {self.number})"

#---Unary Operation Node--------------------------------------------------------
class UnaryOpNode(AST):
    def __init__(self,op,value):
        self.op = op 
        self.value = value
    def __repr__(self):
        return f"(UnaryOp{self.op} {self.value})"

#---Binary Operations Node--------------------------------------------------------    
class BinaryOpNode(AST):
    def __init__(self,left,op,right):
        self.left = left
        self.op = op 
        self.right = right
    def __repr__(self):
        return f"(BinaryOp {self.left} {self.op} {self.right})"

#---Boolean Literal Node--------------------------------------------------------
class BooleanLiteral(AST):
    def __init__(self,value):
        self.value = value
    def __repr__(self):
        return f"(BOOL {self.value})"

#---String Literal Node--------------------------------------------------------
class StringLiteral(AST):
    def __init__(self,value):
        self.value = value 
    def __repr__(self):
        return f"(STRING {self.value})"

#---Null Literal Node--------------------------------------------------------
class NullLiteral(AST):
    def __init__(self):
        pass
    def __repr__(self):
        return f"(Null)"

class ArrayLiteralNode(AST):
    def __init__(self,elements):
        self.elements = elements 
    def __repr__(self):
        return f"(Array {self.elements})"

class ArrayAssignNode(AST): ############
    def __init__(self,name,elements):
        self.name = name
        self.elements = elements 
    def __repr__(self):
        return f"(ArrayAssign {self.name}={self.elements}"

class IndexingNode(AST):
    def __init__(self,array,start_index):
        self.array = array
        self.start_index = start_index
        # self.end_index = end_index
        # self.steps = steps

    def __repr__(self):
        return f"ArrayIndex {self.array}[{self.start_index}]"

class SlicingNode(AST):
    def __init__(self,array,start_index,end_index,steps):
        self.array = array 
        self.start_index = start_index 
        self.end_index = end_index 
        self.steps = steps 
    
    def __repr__(self):
        return f"(SLICING {self.array}[{self.start_index}:{self.end_index}:{self.steps}]"

#---Variable Assignment Node--------------------------------------------------------
class VarAssignNode(AST):
    def __init__(self, var_name_token, value_node,is_const):
        self.var_name_token = var_name_token 
        self.value_node = value_node
        self.is_const = is_const

        if self.is_const:
            const_variables.append(var_name_token.token_value)
        else:
            dec_variables.append(var_name_token.token_value)

    def __repr__(self):
        keyword = "CONST" if self.is_const else "DEC"
        return f"({keyword} {self.var_name_token.token_value} = {self.value_node})"

#---Variable REASSIGNMENT Node--------------------------------------------------------
class VarReassignNode(AST):
    def __init__(self,var_name_token,value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node
    def __repr__(self):
        return f"(REASSIGN {self.var_name_token} = {self.value_node})"

#---Variable Access Node--------------------------------------------------------
class VarAccessNode(AST):
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token

    def __repr__(self):
        return f"(ACCESS {self.var_name_token.token_value})"

#---Block or Scope Node--------------------------------------------------------
class BlockNode(AST):
    def __init__(self,statements):
        self.statements = statements
    def __repr__(self):
        return f"(BLOCK {self.statements})"

#---Program Node--------------------------------------------------------
class ProgramNode(AST):
    def __init__(self,statements):
        self.statements = statements 
    def __repr__(self):
        return f"(PROGRAM {self.statements})"

#---Conditionals Node--------------------------------------------------------
class IfNode(AST):
    def __init__(self,condition,if_body,else_body=None):
        self.condition = condition 
        self.if_body = if_body
        self.else_body = else_body
    def __repr__(self):
        if self.else_body:
            return f"(IF {self.condition} THEN {self.if_body} ELSE {self.else_body})"
        else:
            return f"(IF {self.condition} THEN {self.if_body})"

#---While Node--------------------------------------------------------
class WhileNode(AST):
    def __init__(self,condition,while_body):
        self.condition = condition
        self.while_body = while_body
    def __repr__(self):
        return f"(WHILE {self.condition} DO {self.while_body})"

#---Function Definition Node--------------------------------------------------------
class FuncDefNode(AST):
    def __init__(self, func_name, func_params, func_body):
        self.func_name = func_name
        self.func_params = func_params
        self.func_body = func_body
    def __repr__(self):
        func_params_names = ", ".join([parameter.token_value for parameter in self.func_params])
        return f"(DEF FUNC {self.func_name} ({func_params_names}) -> {self.func_body})"

#---Function Call Node--------------------------------------------------------
class FuncCallNode(AST):
    def __init__(self, func_name, func_args):
        self.func_name = func_name
        self.func_args = func_args
    def __repr__(self):
        return f"(CALL {self.func_name}({self.func_args}))"

#---Return Node--------------------------------------------------------        
class ReturnNode(AST):
    def __init__(self,value=None):
        self.value = value
    def __repr__(self):
        return f"(RETURN {self.value})"

#---Break Node--------------------------------------------------------
class BreakNode(AST):
    def __init__(self):
        pass
    def __repr__(self):
        return f"(BREAK)"

#---Stdout Node--------------------------------------------------------
class StdOutNode(AST):
    def __init__(self,value_node):
        self.value_node = value_node
    def __repr__(self):
        return f"(STDOUT {self.value_node})"

#---Scan Node--------------------------------------------------------
class ScanNode(AST):
    def __init__(self,variable,type_):
        self.variable = variable
        self.type_ = type_
    def __repr__(self):
        return f"(SCAN {self.variable}:{self.type_})"

class UseNode(AST):
    def __init__(self,library):
        self.library = library 
    
    def __repr__(self):
        return f"(Use {self.library})"

class ForNode(AST):
    def __init__(self,variable,iterable,statements):
        self.variable = variable
        self.iterable = iterable
        self.statements = statements
    
    def __repr__(self):
        return f"(FOR {self.variable} in {self.iterable} :: {self.statements})"
#---------------------------------------------------------------------

#####################################################################
#                       END OF FILE
#####################################################################