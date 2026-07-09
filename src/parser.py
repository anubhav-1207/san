#parser.py
#===============================================================================
#A parser goes through the list of tokens and produces an AST from it, discarding all irrelevant tokens.
#===============================================================================
from src.ast_nodes import *
from src.scanner import *

#---Error Classes--------------------------------------------------------------------
class UnexpectedTokenError(Exception):
    def __init__(self,token,expected_token,line,col):
        super().__init__(f"class source.fatal:: private unexpected token found while parsing '{token}' instead of {expected_token},\n\t\t---> parser exited with error[#PAR001], line:col {line}:{col}")

class ControlFLowError(Exception):
    def __init__(self,code,line,col):
        super().__init__(f"class source.fatal:: private statements found null in {code} body, cannot handle empty {code} body,\n\t\t---> parser exited with error[#PAR002], line:col {line}:{col}")

class NullFuncBody(Exception):
    def __init__(self,line,col):
        super().__init__(f"class source.recursive:: environmental statements found null in function definiton, cannot handle null function,\n\t\t---> parser exited with error[#PAR003], line:col {line}:{col}")

#---Parser Class---------------------------------------------------------------------
class Parser:
    def __init__(self,tokens):
        self.tokens = tokens 
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else None

    #---Advance----------------------------------------------------
    def advance(self):
        """
        Consumes and returns the current token and advances past it.
        """
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None
    
    #---Peek-------------------------------------------------------
    def peek(self):
        """
        Returns the next token without consuming it.
        """
        if (self.pos + 1) < (len(self.tokens)):
            return self.tokens[self.pos+1]
        else:
            return None 
    
    #---Match----------------------------------------------------
    def match(self,token_types):
        """
        Tells if the current token_type matches the given token types(s).
        """
        return self.current_token.type_ in token_types
    
    #---Expect---------------------------------------------------
    def expect(self,token_types):
        """
        Matches the current token, if true, then consumes it, else returns error.
        """
        if self.match(token_types):
            tok = self.current_token
            self.advance()
            return tok 
        else:
            raise UnexpectedTokenError(self.current_token.token_value,token_types,self.current_token.line,self.current_token.col)
    
    #---OR Parser------------------------------------------------
    def parse_logical_or(self):
        """
        Parser '||' operator.
        """
        left = self.parse_logical_and()
        while self.current_token and self.match([TT_OR]):
            op = self.current_token.token_value
            self.advance()
            right = self.parse_logical_and()
            left = BinaryOpNode(left, op, right)
        return left

    #---AND parser------------------------------------------
    def parse_logical_and(self):
        """
        Parses the '&&' operator.
        """
        left = self.parse_comp_expr()
        while self.current_token and self.match([TT_AND]):
            op = self.current_token.token_value
            self.advance()
            right = self.parse_comp_expr()
            left = BinaryOpNode(left, op, right)
        return left

    #---Factor Parser------------------------------------------
    def parse_factor(self):
        """
        Parses factors.
        """
        if self.match([TT_PLUS,TT_MINUS,TT_BANG]):
            op = self.current_token.token_value
            self.advance()
            node = self.parse_factor()
            return UnaryOpNode(op,node)
        
        elif self.match([TT_INT,TT_FLOAT]):
            tok = self.expect([TT_INT,TT_FLOAT])
            return NumberNode(tok)
        
        elif self.match([TT_BOOL]):
            value = self.current_token.token_value
            self.advance()
            return BooleanLiteral(value)
        
        elif self.match([TT_STR]):
            value = self.current_token.token_value
            self.advance()
            return StringLiteral(value)
        
        elif self.match([TT_LPAREN]):
            self.expect([TT_LPAREN])
            expression_node = self.parse_logical_or()
            self.expect([TT_RPAREN])
            return expression_node
        
        elif self.current_token and self.current_token.token_value == 'Null':
            self.advance()
            return NullLiteral()

        elif self.current_token and self.current_token.token_value == 'flux':
            self.advance()
            var_token = self.expect([TT_IDENT])
            self.expect([TT_EQ])
            value = self.parse_logical_or()
            return VarReassignNode(var_token, value)
            
        elif self.match([TT_IDENT]):
            variable = self.expect([TT_IDENT])
            
            if self.current_token and self.current_token.type_ == TT_LPAREN:

                self.expect([TT_LPAREN]) 
                
                args = []
                if self.current_token and self.current_token.type_ != TT_RPAREN:

                    args.append(self.parse_logical_or())

                    while self.current_token and self.current_token.type_ == TT_COMMA:
                        self.expect([TT_COMMA])
                        args.append(self.parse_logical_or())
                
                self.expect([TT_RPAREN]) 
                return FuncCallNode(variable.token_value, args)
            
            return VarAccessNode(variable)
    
    #---Exponents Parser--------------------------------------------------------
    def parse_power(self):
        """
        Parser exponents.
        """
        left = self.parse_factor()
        if self.current_token and self.match([TT_STARSTAR]):
            op = self.current_token.token_value
            self.advance()
            right = self.parse_power()
            left = BinaryOpNode(left,op,right)
        return left
    
    #---Term Parser------------------------------------------------------------
    def parse_term(self):
        """
        Parses terminals values.
        """
        left = self.parse_power()
        while self.current_token and self.match([TT_STAR,TT_SLASH]):
            op = self.current_token.token_value 
            self.advance()
            right = self.parse_power()
            right = right
            left = BinaryOpNode(left,op,right)
        return left 

    #---Expression Parser-------------------------------------------------------
    def parse_expr(self):
        """
        Parses expressions.
        """
        left = self.parse_term()
        while self.current_token and self.match([TT_PLUS,TT_MINUS]):
            op = self.current_token.token_value
            self.advance()
            right = self.parse_term()
            left = BinaryOpNode(left,op,right)
        return left

    #---Comparison Parser--------------------------------------------------
    def parse_comp_expr(self):
        """
        Parses comparison expressions.
        """
        left = self.parse_expr()
        while self.current_token and self.match([TT_GT,TT_GTE,TT_LT,TT_LTE,TT_EQEQ,TT_BANGEQ]):
            op = self.current_token.token_value
            self.advance()
            right = self.parse_expr()
            left = BinaryOpNode(left,op,right)
        return left
    
    #---Parse Statements--------------------------------------------------------
    def parse_statements(self):
        """
        Parses statements.
        """
        if self.current_token and self.current_token.token_value in ('dec','const'):
            # is_const = (self.current_token.token_value == 'const')

            if self.current_token.token_value == 'const':
                is_const = True
            else:
                is_const = False

            self.expect([self.current_token.type_])
            var_name_token = self.expect([TT_IDENT])
            self.expect([TT_EQ])
            var_value_node = self.parse_comp_expr()
            return VarAssignNode(var_name_token,var_value_node,is_const)
        
        elif self.current_token and self.current_token.token_value == 'if':
            self.advance()
            self.expect([TT_LPAREN])
            condition = self.parse_logical_or()
            self.expect([TT_RPAREN])
            # self.expect([TT_LBRACE])
            if_body = self.parse_blocks()
            if not if_body:
                raise ControlFLowError("if",self.current_token.line,self.current_token.col)
            # self.expect([TT_RBRACE])

            else_body = None 
            if self.current_token and self.current_token.token_value == 'else':
                self.advance()
                # self.expect([TT_LBRACE])
                else_body = self.parse_blocks()
                # self.expect([TT_RBRACE])
            
            return IfNode(condition,if_body,else_body)

        elif self.current_token and self.current_token.token_value == 'while':
            self.expect([self.current_token.type_])
            self.expect([TT_LPAREN])
            condition = self.parse_logical_or()
            self.expect([TT_RPAREN])
            while_body = self.parse_blocks()
            if not while_body:
                raise ControlFLowError("while",self.current_token.line,self.current_token.col)
            return WhileNode(condition,while_body)
        
        elif self.current_token and self.current_token.token_value == 'func':
            self.expect([self.current_token.type_])
            func_name = self.current_token.token_value
            self.expect([TT_IDENT])
            self.expect([TT_LPAREN])
            params = []
            if self.current_token and self.current_token.type_ != TT_RPAREN:
                params.append(self.expect([TT_IDENT]))
                while self.current_token and self.current_token.type_ == TT_COMMA:
                    self.expect([TT_COMMA])
                    params.append(self.expect([TT_IDENT]))  
            self.expect([TT_RPAREN])
            func_body = self.parse_blocks()
            if not func_body:
                raise NullFuncBody(self.current_token.line,self.current_token.col)
            return FuncDefNode(func_name,params,func_body)
        
        elif self.current_token and self.current_token.token_value == 'return':
            self.expect([self.current_token.type_])
            value = None
            if self.current_token and self.current_token.type_ not in (TT_EOF,TT_RBRACE):
                value = self.parse_logical_or()
            return ReturnNode(value)

        elif self.current_token and self.current_token.token_value == 'break':
            self.advance()
            return BreakNode()
        
        elif self.current_token and self.current_token.token_value == 'stdout':
            self.expect([self.current_token.type_])
            self.expect([TT_LPAREN])
            value = self.parse_logical_or()
            self.expect([TT_RPAREN])
            return StdOutNode(value)
        
        elif self.current_token and self.current_token.token_value == 'scan':
            self.expect([self.current_token.type_])
            self.expect(TT_LPAREN)
            variable = self.current_token.token_value
            self.expect([TT_IDENT])
            self.expect([TT_RPAREN])
            return ScanNode(variable)
        
        else:
            expr = self.parse_logical_or()
            return expr
    
    #---Statement List Parser------------------------------------------------------
    def parse_statements_list(self):
        """
        Parses statements inside a block until '}' is reached.
        """
        statements = []
        while self.current_token and self.current_token.type_ != TT_RBRACE:
            stmt = self.parse_statements()
            if stmt:
                statements.append(stmt)
            else:
                break
        return statements


    def parse_blocks(self):
        """
        Parses blocks '{}'.
        """
        if self.current_token and self.current_token.type_ == TT_LBRACE:
            self.expect([TT_LBRACE])
            statements = self.parse_statements_list()
            self.expect([TT_RBRACE])  
            return statements

    def parse(self):
        """
        The main parser method from where the parsing begins.
        """
        statements = []
        while self.current_token and self.current_token.type_ != TT_EOF:
            stmt = self.parse_statements()
            if stmt:
                statements.append(stmt)
            else:
                break
        return ProgramNode(statements)

#=========================================================================================================
#END OF FILE
#=========================================================================================================
