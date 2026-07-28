#stdlib/native_arrays.py 
#-----------------------------------------------------------------------------------
# This file contains all the built-ins methods for arrays
# Currently, it has:
# - len()
# - append()
# - pop()
# - insert()
# - del()
#-----------------------------------------------------------------------------------

#---Native Function Node/Class------------------------------------------------------
class NativeArrayFunction:
    """Wrapper for built-in Python functions to be called from Arc."""
    def __init__(self, name, expected_args, method, is_const=False):
        self.name = name
        self.expected_args = expected_args
        self.method = method
        self.is_native = True
        self.is_const = is_const

#==========================================================================
#                          Built In Methods
#==========================================================================

#---len()--------------------------
def native_length(args): #works for both strings and arrays 
    """Returns the length of the arguement."""
    return len(args[0])

#---append()------------------------
def native_append(args):
    """Appends a value to an array."""
    array = args[0]
    element = args[1]
    return array.append(element)

#---pop()---------------------------
def native_pop(args):
    """Pops a value from the array."""
    array = args[0]
    index = args[1]
    print(array[index])
    return array.pop(index)

#---insert()-------------------------
def native_insert(args): #insert(array,index,element)
    """Inserts an element into the specified index."""
    array = args[0]
    index = args[1]
    element = args[2]

    print(array,index,element)
    return array.insert(index,element)

#---del()--------------------------------
def native_del(args): # del(array,index)
    """Deletes an element at the given index."""
    array = args[0]
    index = args[1]

    del array[index]
#==========================================================================

#-----------------------------------------------------------
def inject_array_methods(function_table):
    """Injects native array methods into the given function dictionary(memory) in interpreter."""
    function_table["len"] = NativeArrayFunction("len", 1, native_length)
    function_table["append"] = NativeArrayFunction("append",2,native_append)
    function_table["pop"] = NativeArrayFunction("pop",2,native_pop)
    function_table["insert"] = NativeArrayFunction("insert",3,native_insert)
    function_table["del"] = NativeArrayFunction("del",2,native_del)
#-------------------------------------------------------------

############################################################################
#                           END OF FILE                                    #
############################################################################