#interpreter.py
#===================================================================
#Walks through all the AST nodes and executes them one by one.
#===================================================================

#---Error Classes-------------------------------------------------------------------------------
class AccidentalReassError(Exception):
    def __init__(self,var):
        super().__init__(f"class source.fatal:: environmental variable '{var} already found, explicit reassignment expected,\n\t\t---> interpreter exited with error[#INTRPTR001]")

class UndefinedVariable(Exception):
    def __init__(self,var):
        super().__init__(f"class source.fatal:: environmental variable '{var} is not defined, explicit definition expected,\n\t\t---> interpreter exited with error[#INTRPTR002]")

class ConstantMutation(Exception):
    def __init__(self,var):
        super().__init__(f"class source.fatal:: environmental constant '{var} is a constant,even explicit reassignment not allowed,\n\t\t---> interpreter exited with error[#INTRPTR003]")

class ZeroDivisionError(Exception):
    def __init__(self,right,left):
        super().__init__(f"class source.fatal:: cannot divide by zero, mathematically undefined,\n\t\t---> undefined operation '{right}/{left}' interpreter exited with error[#INTRPTR004]")



#---Visitor Nodes-------------------------------------------------------------------------------
class BreakException(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Environment:
    """
    Creates a namespace to store variables.
    """
    def __init__(self,parent=None):
        self.parent = parent
        self.vars = {}

    def define(self,name,value,is_const=False):
        """
        Adds the variable and its value to namespace.
        """
        if name in self.vars:
            raise AccidentalReassError(name)
        else:
            self.vars[name] = (value, is_const)
    
    def lookup(self,name):
        """
        Searches for a variable in the global and parent scope. 
        """
        if name in self.vars:
            return self.vars[name][0]
        if self.parent:
            return self.parent.lookup(name)
        else:
            raise UndefinedVariable(name)
    
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


class Evaluator:
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions = {}
    
    def evaluate(self,node):
        """
        Gets the node name and visits the node.
        """
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self,method_name,None)
        if visitor is None:
            raise Exception(f"No visitor for {node.__class__.__name__}")
        return visitor(node)
    
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
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            if right != 0:
                return left // right
            else:
                raise ZeroDivisionError(right,left)
        elif operator == '**':
            return left ** right
        elif operator == '>':
            return left > right
        elif operator == '<':
            return left < right
        elif operator == '<=':
            return left <= right
        elif operator == '>=':
            return left >= right
        elif operator == '==':
            return left == right
        elif operator == '!=':
            return left != right
        elif operator == '&&':
            return self.is_truthy(left) and self.is_truthy(right)
        elif operator == '||':
            return self.is_truthy(left) or self.is_truthy(right)
        else:
            raise Exception(f"Unknown binary operator: {node.op}")
    
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
        try:
            value = float(user_input)
        except ValueError:
            value = user_input
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
            raise Exception(f"FUNC UNDEFINED {node.func_name}")
        
        func_def = self.functions[node.func_name]
        func_env = Environment(parent=self.current_env)

        for i, param in enumerate(func_def.func_params):
            arg_value = self.evaluate(node.func_args[i])
            func_env.define(param.token_value, arg_value)
        
        old_env = self.current_env
        self.current_env = func_env
        
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