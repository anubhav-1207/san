#scanner.py
#===========================================================================================
#A lexer goes through each character and classifies each of them as their respective type of tokens
#===========================================================================================

#--------------------------------------------------------------------------------------
#---Token Types----------------------------------------------------
#The definitions are categorised based on their type
#------------------------------------------------------------------

#---Data Type Tokens----------------------------------------------
TT_INT = "INTEGER"
TT_FLOAT = "FLOAT"
TT_BOOL = "BOOLEAN"
TT_STR = "STRING"
TT_NUll = "NULL"

#---Arithmetic Operators--------------------------------------------
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_SLASH = "SLASH"
TT_STAR = "STAR"

#---Membership Operators-----------------------------------------------
TT_IN = "IN"

#---Logical Operators------------------------------------------------
TT_AND = "AND"
TT_OR = "OR"
TT_NOT = "NOT"

#---Comparison Operators---------------------------------------------------
TT_GT = "GT"
TT_LT = "LT"
TT_EQ = "EQ"
TT_GTE = "GTE"
TT_LTE = "LTE"
TT_BANG = "BANG"
TT_BANGEQ = "BANGEQ"

#---Multi-char Tokens-----------------------------------------------
TT_EQEQ = "EQEQ"
TT_STARSTAR = "STARSTAR"

#---Delimiters----------------------------------------------------------
TT_DOT = "DOT"
TT_COLON = "COLON"
TT_SEMICOLON = "SEMICOLON"
TT_COMMA = "COMMA"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_LBRACE = "LBRACE"
TT_RBRACE = "RBRACE"
TT_LBRACKET = "LBRACKET"
TT_RBRACKET = "RBRACKET"

#---Others---------------------------------------------------------------
TT_IDENT = "IDENT"
TT_KEYWORD = "KEYWORD"
TT_EOF = "EOF"
TT_NEWLINE = "NEWLINE"

#---Keywords-------------------------------------------------------------
KEYWORDS = {
    'dec', 'const','flux', 'func', 'return',
    'if', 'else', 'elif',
    'loop', 'for', 'in', 'break', 'skip',
    'stdout', 'scan',
    'Null',
    'use', 'type', 'init', 'ext',
    'try', 'catch', 'drop',
    'int','float','str','bool'
}

NUMBERS = "1234567890"
ALPHABETS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
SYMBOLS = """ !@#$%,^&*(})<>?/{:;|[]+=-`~'" """

class Tokens:
    def __init__(self,type_,line: int,token_value = None,col = None):
        self.type_ = type_
        self.token_value = token_value 
        self.line = line
        self.col = col

    def __repr__(self):
        if self.token_value:
            return f"Token({self.type_}:{self.token_value} -> line - {self.line}, col - {self.col})"
        else:
            return f"Token({self.type_} -> line - {self.line}, col - {self.col})"


#---Error Class-------------------------------------------------------------------
class InvalidTokenError(Exception):
    def __init__(self,char,line,col):
        super().__init__(f"class source.fatal:: private unrecognized malformed token found while tokenising '{char}',\n\t\t---> lexer exited with error[#LEX001], line:col {line}:{col}")

class UnterminatedStringLiteral(Exception):
    def __init__(self,line,col):
        super().__init__(f"str source.recursive:: unterminated string literal,\n\t\t---> lexer exited with error[#LEX002], line:col {line}:{col}")

class InvalidIdentifier(Exception):
    def __init__(self, char, line,col):
        super().__init__(f"ident source.fatal:: invalid identifier arguements:: <class 'int'> followed by '{char}',\n\t\t---> lexer exited with error[#LEX003], line:col {line}:{col}")

class InvalidFloatLiteral(Exception):
    def __init__(self, number, line,col):
        super().__init__(f"float source.recursive:: invalid float format passed '{number}':: nested floats initialised and not valid,\n\t\t---> lexer exited with error[#LEX004], line:col {line}:{col}")

class UnintialisedStringLiteral(Exception):
    def __init__(self,line,col):
        super().__init__(f"str source.recursive:: string literal not initialised,\n\t\t---> lexer exited with error[#LEX002], line:col {line}:{col}")


#---Lexer Class ------------------------------------------------------------------
class Lexer:
    def __init__(self,source) -> None:
        self.source = source 
        self.line = 1
        self.pos = 0
        self.col = 0
        self.tokens = []
    def __repr__(self) -> None:
        return f"Token({Tokens.token_type}:{Tokens.token_value})" 


    
    #---Current Character------------------------------------------------------------
    def current_char(self):
        """
        Returns which character the pointer is at.
        """
        if self.pos < len(self.source):
            return self.source[self.pos]
        else:
            return None


    #---Advance-------------------------------------------------------------------------
    def advance(self):
        """
        Stores & returns the current character and moves forward.
        """
        char = self.source[self.pos]
        self.pos += 1
        self.col += 1
        return char


    #---Peek-----------------------------------------------------------------------------
    def peek(self):
        """
        Returns the character next to the pointer but self.pod doesn't increase.
        """
        if (self.pos + 1) < len(self.source):
            return self.source[self.pos+1]
        else:
            return None

    #---Add---------------------------------------------------------------------------
    def add(self,token_type, line,token_value = None):
        """
        Appends the token objects into the list.
        """
        self.tokens.append(Tokens(token_type,line,token_value,self.col))


    #---Tokenise-----------------------------------------------------------------------
    def tokenise(self):
        """
        Main tokeniser which classifies characters as their specific category they belong too.
        """
        
#=======================================================================================
        #---String Reader------------------------------------------------------
        def read_strings(self,string_initialiser):
            """
            Called when the lexer spots a " or a ', and then continues reading till another of the like type is spotted.
            """
            result = []

            while self.current_char() is not None and self.current_char() != string_initialiser:
                if self.current_char() == '\n':
                    self.line += 1
                    result.append(self.advance())
                else:
                    result.append(self.advance())
            if self.current_char() == string_initialiser:
                self.advance()
                text = "".join(result)
                self.add(TT_STR,self.line,text)
            else:
                raise UnterminatedStringLiteral(self.line,self.col)
            
#=======================================================================================        
        #---Ident/kWord Reader----------------------------------------------------------
        def read_ident(self):
            """
            Checks if a given sequence of characters is a keyword or and identifier.
            """
            result = []
            while self.current_char() is not None and self.current_char() not in ('',' ','\t', '\n') and self.current_char() not in SYMBOLS:
                result.append(self.advance())
            text = "".join(result)
            if text in KEYWORDS:
                self.add(TT_KEYWORD,self.line,text)
            elif text in ("True","False"):
                self.add(TT_BOOL,self.line,text)
            else:
                self.add(TT_IDENT,self.line,text)

#=======================================================================================
        #---Read Numbers-----------------------------------------------------------------
        def read_numbers(self):
            """Checks if a given sequence of numbers is a float or an integer."""
            result = []
            while self.current_char() is not None and self.current_char() in "1234567890.":
                result.append(self.advance())
            
            number = "".join(result)
            dot_count = number.count('.')
            
            if dot_count > 1:
                raise InvalidFloatLiteral(number, self.line, self.col)
            elif dot_count == 1:
                self.add(TT_FLOAT, self.line, number)
            else:
                self.add(TT_INT, self.line, number)


#=======================================================================================
#---Main Tokenise Loop-------------------------------------------------------
        while self.current_char() is not None:
            char = self.current_char()

            #---Newlines---------------------
            if char == "\n":
                self.advance()
                self.line += 1
                self.col = 1

            #---Spaces----------------------
            elif char.isspace(): 
                self.advance()
            
            #---Equals----------------------
            elif char == '=':
                if self.peek() == '=':
                    self.add(TT_EQEQ,self.line,'==')
                    self.advance()
                    self.advance()
                else:
                    self.add(TT_EQ,self.line,'=')
                    self.advance()
            
            #---Greater--------------------
            elif char == '>':
                if self.peek() == '=':
                    self.add(TT_GTE,self.line,">=")
                    self.advance()
                    self.advance()
                else:
                    self.add(TT_GT,self.line,">")
                    self.advance()
            
            #---Lesser------------------------
            elif char == '<':
                if self.peek() == '=':
                    self.add(TT_LTE,self.line,'<=')
                    self.advance()
                    self.advance()
                else:
                    self.add(TT_LT,self.line,'<')
                    self.advance()
            
            #---Bang-------------------------
            elif char == '!':
                if self.peek() == '=':
                    self.add(TT_BANGEQ,self.line,'!=')
                    self.advance();self.advance()
                else:
                    self.add(TT_BANG,self.line,'!')
                    self.advance()
            
            #---And--------------------------
            elif char == '&' and self.peek() == '&':
                self.add(TT_AND,self.line,'&&')
                self.advance()
                self.advance()
            
            #---Or--------------------------
            elif char == "|" and self.peek() == '|':
                self.add(TT_OR,self.line,'||')
                self.advance()
                self.advance()
            
            #---Star-------------------------
            elif char == '*':
                if self.peek() == '*':
                    self.add(TT_STARSTAR,self.line,'**')
                    self.advance()
                    self.advance()
                else:
                    self.add(TT_STAR,self.line,'*')
                    self.advance()
        
            #---Slash------------------------
            elif char == '/':
                if self.peek() == '/':
                    self.advance()
                    while self.current_char() is not None and self.current_char() != '\n':
                        self.advance()
                
                elif self.peek() == '*':
                    self.advance()
                    self.advance()

                    while self.current_char() is not None and self.current_char() != '*' and self.peek() != '/':
                        self.advance()
                    self.advance()
                    self.advance()
                else:
                    self.add(TT_SLASH,self.line,'/')
                    self.advance()
            
#=======================================================================================
            #---Single Chars----------------------------------------------
            elif char == '(':self.add(TT_LPAREN,self.line,'(');self.advance()
            elif char == ')':self.add(TT_RPAREN,self.line,')');self.advance()
            elif char == '[':self.add(TT_LBRACKET,self.line,'[');self.advance()
            elif char == ']':self.add(TT_RBRACKET,self.line,']');self.advance()
            elif char == '{':self.add(TT_LBRACE,self.line,'{');self.advance()
            elif char == '}':self.add(TT_RBRACE,self.line,'}');self.advance()
            elif char == '+':self.add(TT_PLUS,self.line,'+');self.advance()
            elif char == '-':self.add(TT_MINUS,self.line,'-');self.advance()
            elif char == '.':self.add(TT_DOT,self.line,'.');self.advance()
            elif char == ',':self.add(TT_COMMA,self.line,',');self.advance()
            elif char == ';':self.advance()
            elif char == ':':self.add(TT_COLON,self.line,':');self.advance()
           
           #---Strings----------------------
            elif char in ('"',"'"):
                if self.peek() not in ALPHABETS or self.peek() not in NUMBERS or self.peek() not in SYMBOLS: 
                    string_initialiser = char
                    self.advance()
                    read_strings(self,string_initialiser)
                else:
                    raise UnterminatedStringLiteral(self.line,self.col)
                
            #---Keywords or Identifiers---------
            elif char in ALPHABETS or char == '_': 
                read_ident(self)
            
            #---Numbers----------------------
            elif char in NUMBERS: 
                read_numbers(self)
            
            else:
                raise InvalidTokenError(char,self.line,self.col)


    #---EOF Token------------------------------------------------------------------
        self.add(TT_EOF,self.line)            
        return self.tokens

#====================================================================
#END OF FILE
#====================================================================