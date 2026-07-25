class NativeFunction:
    """Wrapper for built-in Python functions to be called from Arc."""
    def __init__(self, name, expected_args, method, is_const=False):
        self.name = name
        self.expected_args = expected_args
        self.method = method
        self.is_native = True
        self.is_const = is_const

def native_length(args):
    return len(args[0])

def native_append(args):
    array = args[0]
    element = args[1]
    return array.append(element)

def native_pop(args):
    array = args[0]
    index = args[1]
    print(array[index])
    return array.pop(index)

def native_insert(args): #insert(array,index,element)
    array = args[0]
    index = args[1]
    element = args[2]

    print(array,index,element)
    return array.insert(index,element)

def native_del(args): # del(array,index)
    array = args[0]
    index = args[1]

    del array[index]



def inject_array_methods(function_table):
    """Injects native array methods into the given function dictionary."""
    function_table["len"] = NativeFunction("len", 1, native_length)
    function_table["append"] = NativeFunction("append",2,native_append)
    function_table["pop"] = NativeFunction("pop",2,native_pop)
    function_table["insert"] = NativeFunction("insert",3,native_insert)
    function_table["del"] = NativeFunction("del",2,native_del)
