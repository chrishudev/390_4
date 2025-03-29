"""
uctypes.py.

This file contains definitions of classes that represent uC types, as
well as utility functions that operate on types.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

from ucerror import error


class Type:
    """Parent class for all uC types."""

    __creator_token = None  # controls access to type creation

    def __init__(self, token, name, position):
        """Initialize this type to have the given name."""
        Type._check_token(token)
        self.name = name
        self.position = position
        self._array_type = None  # cache for the array type

    @staticmethod
    def _check_token(token):
        """Check whether the given token has permission to create types."""
        if Type.__creator_token is None:
            Type.__creator_token = token
        elif Type.__creator_token is not token:
            raise AssertionError(
                'types can only be created by add_type() on the '
                'global environment or by accessing the array_type '
                'property on an existing type'
            )

    def __str__(self):
        """Return the name of this type."""
        return self.name

    @property
    def array_type(self):
        """Return the array type corresponding to this type."""
        if not self._array_type:
            self._array_type = ArrayType(self.__creator_token, self)
        return self._array_type

    def is_numeric(self):
        """Return whether this type is a primitive numeric type."""
        return False

    def is_integral(self):
        """Return whether this type is a primitive integral type."""
        return False

    def is_convertible_to(self, other):
        """Return whether this type is convertible to the given type."""
        return self is other  # all types are convertible to themselves

    def join(self, other):
        """Compute the type of a binary operation on this type and other."""
        # default to this type if other is not string
        return other if other.name == 'string' else self

    def lookup_field(self, phase, position, name, global_env):
        """Look up a field in this type.

        phase is the current compiler phase, position is the source
        position from where this lookup occurs, name is the name of
        the field, and global_env is the global environment. Reports
        an error if the field is not found. Returns the type of the
        field if it is found, int otherwise.
        """
        error(phase, position,
              f'type {self.name} has no field {name}')
        return global_env.lookup_type(phase, position, 'int')


class UncomputedType(Type):
    """A class representing an uncomputed type."""

    _instance = None  # singleton instance

    def __new__(cls, _token):
        """Return the singleton instance of the given class."""
        if cls._instance is None:
            cls._instance = super(UncomputedType, cls).__new__(cls)
        return cls._instance

    def __init__(self, token):
        """Initialize this type."""
        super().__init__(token, '<uncomputed type>', '<builtin>')

    @property
    def array_type(self):
        """Return the array type corresponding to this type."""
        return self

    @property
    def elem_type(self):
        """Return the element type corresponding to this type."""
        return self

    def check_args(self, _phase, _position, _args):
        """Check if the arguments are compatible with this type."""
        return True


class ArrayType(Type):
    """A class representing an array type.

    The instance attribute elem_type refers to the element type of the
    array.
    """

    def __init__(self, token, elem_type):
        """Initialize this type to have the given element type."""
        super().__init__(token, elem_type.name + '[]',
                         elem_type.position)
        self.elem_type = elem_type

    def check_args(self, phase, _position, args):
        """Check if the arguments are compatible with this array type.

        Compares the arguments against the element type of this array.
        The arguments must have already have their types computed.
        phase is the current compiler phase, position is the source
        position where this check occurs. Reports an error if an
        argument is incompatible.
        """
        # replace the code below with your solution
        for arg in args:
            if arg.get_type() is not self.elem_type:
                mssg = f"array of {self.elem_type} cannot be initialized with {arg.type}"
                error(phase, _position, mssg)
                return False

    def lookup_field(self, phase, position, name, global_env):
        """Look up a field in this type.

        phase is the current compiler phase, position is the source
        position from where this lookup occurs, name is the name of
        the field, and global_env is the global environment. Reports
        an error if the field is not found. Returns the type of the
        field if it is found, int otherwise.
        """
        # replace the code below with your solution
        if name == "length":
            return global_env.lookup_type(phase, position, 'int')
        error(phase, position, f"unknown field {name} of ArrayType")
        return global_env.lookup_type(phase, position, 'int')


class PrimitiveType(Type):
    """A class representing a primitive type."""

    __primitives = set()  # all primitive type names
    __integral_typenames = {'int', 'long'}
    __numerical_typenames = __integral_typenames | {'double'}
    __numerical_conversions = {
        ('int', 'long'), ('int', 'double'), ('long', 'double')
    }

    def __init__(self, token, name):
        """Initialize this primitive type."""
        super().__init__(token, name, '<builtin>')
        PrimitiveType.__primitives.add(name)

    @staticmethod
    def is_primitive_type_name(name):
        """Return whether name is the name of a primitive type."""
        return name in PrimitiveType.__primitives

    def is_numeric(self):
        """Return whether this type is a primitive numeric type."""
        return self.name in PrimitiveType.__numerical_typenames

    def is_integral(self):
        """Return whether this type is a primitive integral type."""
        return self.name in PrimitiveType.__integral_typenames

    def is_convertible_to(self, other):
        """Return whether this type is convertible to the given type."""
        return (super().is_convertible_to(other)
                or ((self.name, other.name) in
                    PrimitiveType.__numerical_conversions)
                or (self.name == 'null'
                    and isinstance(other, (ArrayType, UserType))))

    def join(self, other):
        """Compute the type of a binary operation on this type and other."""
        return (other if (other.name == 'string'  # string has highest priority
                          or ((self.name, other.name) in
                              PrimitiveType.__numerical_conversions))
                else self)  # default to this type


class UserType(Type):
    """A class representing a user-defined type."""

    def __init__(self, token, name, decl):
        """Initialize this type.

        name is a string representing the name of the type and decl is
        the AST node for the declaration of this type.
        """
        super().__init__(token, name, decl.name.position)
        self.decl = decl
        self.fields = decl.fielddecls

    def check_args(self, phase, position, args):
        """Check if the arguments are compatible with the field types.

        Compares the arguments against the types of the fields this
        type. The arguments must have already have their types
        computed. phase is the current compiler phase, position is the
        source position where this check occurs. Reports an error if
        an argument is incompatible.
        """
        # replace the code below with your solution
        if len(args) == 0:
            return True
        self.type = self.decl.type
        if len(self.fields) != len(args):
            mssg = f"{self.type} expected {len(self.fields)} arguments, got {len(args)}"
            error(phase, position, mssg)
            return False
        for index, arg in enumerate(args):
            if self.fields[index].get_type() is not arg.type:
                if arg.type.is_convertible_to(self.fields[index].get_type()):
                    continue
                mssg = f"{self.type} expected {self.fields[index].vartype.name.raw} at {index + 1}, got {arg.type}"
                error(phase, position, mssg)
                return False
        return True

    def lookup_field(self, phase, position, name, _global_env):
        """Look up a field in this type.

        phase is the current compiler phase, position is the source
        position from where this lookup occurs, name is the name of
        the field, and global_env is the global environment. Reports
        an error if the field is not found. Returns the type of the
        field if it is found, int otherwise.
        """
        # replace the code below with your solution
        for field in self.fields:
            if field.name.raw == name:
                return field.get_type()
        error(phase, position, f"{name} not in {self.name}")
        return _global_env.lookup_type(phase, position, 'int')


def add_builtin_types(types, token):
    """Add primitive types to the given dictionary."""
    for name in ('int', 'long', 'double', 'boolean', 'string', 'void',
                 'null'):
        types[name] = PrimitiveType(token, name)
