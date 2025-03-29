"""
ucfunctions.py.

This file contains definitions of classes that represent uC functions,
as well as utility functions that operate on functions.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

from ucerror import error
import uctypes


class Function:
    """A class that represents a uC function."""

    __creator_token = None  # controls access to function creation

    def __init__(self, token, name, position):
        """Initialize this function with the given name.

        The return is initially set to None, and the parameters to an
        empty set.
        """
        Function._check_token(token)
        self.name = name
        self.position = position
        self.rettype = None
        self.param_types = []

    @staticmethod
    def _check_token(token):
        """Check whether the token has permission to create functions."""
        if Function.__creator_token is None:
            Function.__creator_token = token
        elif Function.__creator_token is not token:
            raise AssertionError(
                'functions can only be created by add_function() on '
                'the global environment'
            )

    def __str__(self):
        """Return the name of this function."""
        return self.name

    @staticmethod
    def mangle(funcname):
        """Mangle the given function name.

        The mangled name is the name that should be used in code
        generation. funcname is a string representing the function
        name.
        """
        return f'UC_FUNCTION({funcname})'

    def check_args(self, phase, position, args):
        """Check if the arguments are compatible with this function.

        The given arguments are compared with the parameter types of
        this function. The arguments must have already have their
        types computed. phase is the current compiler phase, position
        is the source position where this check occurs. Reports an
        error if the arguments are incompatible with this function.
        """
        # replace the code below with your solution
        if len(self.param_types) != len(args):
            mssg = f"function {self.name} expected " + \
                f"{len(self.param_types)} arguments, got {len(args)}"
            error(phase, position, mssg)
            return False
        for index, param in enumerate(self.param_types):
            if param is not args[index].type:
                if args[index].type.is_convertible_to(param):
                    continue
                mssg = f"type {param} at {index + 1} not compatible " + \
                    f"with {args[index].type} parameter"
                error(phase, position, mssg)
                return False
        return True


class UncomputedFunction(Function):
    """A class representing an uncomputed function."""

    _instance = None  # singleton instance

    def __new__(cls, _token):
        """Return the singleton instance of the given class."""
        if cls._instance is None:
            cls._instance = super(UncomputedFunction, cls).__new__(cls)
        return cls._instance

    def __init__(self, token):
        """Initialize this type."""
        super().__init__(token, '<uncomputed function>', '<builtin>')
        self.rettype = uctypes.UncomputedType(token)

    @property
    def array_type(self):
        """Return the array type corresponding to this type."""
        return self


class PrimitiveFunction(Function):
    """A class that represents a primitive uC function."""

    def __init__(self, token, name, rettype, param_types, type_env):
        """Initialize this function with the given name.

        rettype is the name of the return type, param_types is a
        sequence of names of the parameter types, and type_env is the
        dictionary in which to look up type names.
        """
        super().__init__(token, name, '<builtin>')
        self.rettype = type_env[rettype]
        for param in param_types:
            self.param_types.append(type_env[param])


class UserFunction(Function):
    """A class that represents a user-defined uC function."""

    def __init__(self, token, name, decl):
        """Initialize this function with the given name.

        The return type is initially set to None, and the parameter
        types to an empty set. decl is the AST node that defines this
        function.
        """
        super().__init__(token, name, decl.name.position)
        self.decl = decl

    def add_param_types(self, param_types):
        """Add parameter types to the parameter list of this function.

        param_types must be a sequence of items, each of which must be
        of type uctypes.Type.
        """
        self.param_types += param_types


def make_conversion(target, source, type_env, token):
    """Create a primitive conversion function.

    The resulting function converts the type named by source to that
    named by target. type_env is the dictionary in which to look up
    type names.
    """
    return PrimitiveFunction(token, f'{source}_to_{target}',
                             target, (source,), type_env)


def add_conversions(func_env, type_env, token):
    """Create all the primitive conversion functions.

    func_env is the dictionary in which to insert the conversion
    functions. type_env is the dictionary to use to look up type
    names.
    """
    types = ('int', 'long', 'double', 'string')
    for type1 in types:
        for type2 in types:
            if type1 != type2:
                func = make_conversion(type1, type2, type_env, token)
                func_env[func.name] = func
    func = make_conversion('boolean', 'string', type_env, token)
    func_env[func.name] = func
    func = make_conversion('string', 'boolean', type_env, token)
    func_env[func.name] = func


def add_builtin_functions(func_env, type_env, token):
    """Create all the primitive uC functions.

    func_env is the dictionary in which to insert the conversion
    functions. type_env is the dictionary to use to look up type
    names.
    """
    add_conversions(func_env, type_env, token)
    # string functions
    func_env['length'] = PrimitiveFunction(
        token, 'length', 'int', ('string',), type_env
    )
    func_env['substr'] = PrimitiveFunction(
        token, 'substr', 'string', ('string', 'int', 'int'), type_env
    )
    func_env['ordinal'] = PrimitiveFunction(
        token, 'ordinal', 'int', ('string',), type_env
    )
    func_env['character'] = PrimitiveFunction(
        token, 'character', 'string', ('int',), type_env
    )

    # numerical functions
    func_env['pow'] = PrimitiveFunction(
        token, 'pow', 'double', ('double', 'double'), type_env
    )
    func_env['sqrt'] = PrimitiveFunction(
        token, 'sqrt', 'double', ('double',), type_env
    )
    func_env['ceil'] = PrimitiveFunction(
        token, 'ceil', 'double', ('double',), type_env
    )
    func_env['floor'] = PrimitiveFunction(
        token, 'floor', 'double', ('double',), type_env
    )

    # print functions
    func_env['print'] = PrimitiveFunction(
        token, 'print', 'void', ('string',), type_env
    )
    func_env['println'] = PrimitiveFunction(
        token, 'println', 'void', ('string',), type_env
    )

    # input functions
    func_env['peekchar'] = PrimitiveFunction(
        token, 'peekchar', 'string', (), type_env
    )
    func_env['readchar'] = PrimitiveFunction(
        token, 'readchar', 'string', (), type_env
    )
    func_env['readline'] = PrimitiveFunction(
        token, 'readline', 'string', (), type_env
    )

    # exit function
    func_env['exit'] = PrimitiveFunction(
        token, 'exit', 'void', ('int',), type_env
    )
