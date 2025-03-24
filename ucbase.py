"""
ucbase.py.

This file contains definitions of the base AST node, declaration
nodes, global and local environments, and utility functions.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

import dataclasses
from dataclasses import dataclass
import functools
import itertools
import sys
from typing import List, Optional, ClassVar, Iterator
from ucerror import error
import uctypes
import ucfunctions


################################
# Environments in the Compiler #
################################

class GlobalEnv:
    """A class that represents the global environment of a uC program.

    Maps names to types and to functions.
    """

    __token = object()
    uncomputed_type = uctypes.UncomputedType(__token)
    uncomputed_function = ucfunctions.UncomputedFunction(__token)

    def __init__(self):
        """Initialize the environment with built-in names."""
        self.__types = {}
        self.__functions = {}
        uctypes.add_builtin_types(self.__types, GlobalEnv.__token)
        ucfunctions.add_builtin_functions(
            self.__functions, self.__types, GlobalEnv.__token
        )

    def add_type(self, phase, position, name, declnode):
        """Add the given type to this environment.

        phase is the current compiler phase, position is the source
        position of the type declaration, name is a string containing
        the name of the type, and declnode is the AST node
        corresponding to the declaration. Reports an error if a type
        of the given name is already defined. Returns the uctypes.Type
        object corresponding to the type declaration.
        """
        type_ = uctypes.UserType(self.__token, name, declnode)
        if name in self.__types:
            error(phase, position,
                  f'redefinition of type {name}, previously defined '
                  f'at line {self.__types[name].position}')
        else:
            self.__types[name] = type_
        return type_

    def add_function(self, phase, position, name, declnode):
        """Add the given function to this environment.

        phase is the current compiler phase, position is the source
        position of the function declaration, name is a string
        containing the name of the function, and declnode is the AST
        node corresponding to the declaration. Reports an error if a
        function of the given name is already defined. Returns the
        ucfunctions.Function object corresponding to the function
        declaration.
        """
        func = ucfunctions.UserFunction(self.__token, name, declnode)
        if name in self.__functions:
            error(phase, position,
                  f'redefinition of function {name}, previously '
                  f'defined at line {self.__functions[name].position}')

        else:
            self.__functions[name] = func
        return func

    def lookup_type(self, phase, position, name, strict=True):
        """Return the uctypes.Type represented by the given name.

        phase is the current compiler phase, position is the source
        position that resulted in this lookup, name is a string
        containing the name of the type to look up. If strict is True,
        then an error is reported if the name is not found, and the
        int type is returned. Otherwise, if the name is not found,
        None is returned.
        """
        if name not in self.__types:
            if strict:
                error(phase, position, 'undefined type ' + name)
                return self.__types['int']  # treat it as int by default
            return None
        return self.__types[name]

    def lookup_function(self, phase, position, name, strict=True):
        """Return the ucfunctions.Function represented by the given name.

        phase is the current compiler phase, position is the source
        position that resulted in this lookup, name is a string
        containing the name of the function to look up. If strict is
        True, then an error is reported if the name is not found, and
        string_to_int function is returned. Otherwise, if the name is
        not found, None is returned.
        """
        if name not in self.__functions:
            if strict:
                error(phase, position, 'undefined function ' + name)
                return self.__functions['string_to_int']  # default
            return None
        return self.__functions[name]


class VarEnv:
    """A class that represents a local environment in a uC program.

    Maps names to types of fields, parameters, and variables.
    """

    def __init__(self, parent_env, global_env):
        """Initialize this to an empty local environment.

        parent is the parent local environment for this environment;
        it is None if no parent exists. The given global environment
        is used to look up a default type when a name is not defined.
        """
        self.__parent = parent_env
        self.__global_env = global_env
        self.__var_types = {}
        self.__var_positions = {}

    def add_variable(self, phase, position, name, var_type):
        """Insert a variable into this environment.

        phase is the current compiler phase, position is the source
        position of the field, parameter, or variable declaration,
        name is a string containing the name of the field, variable,
        or parameter, var_type is a uctypes.Type object representing
        the type of the variable, and kind_str is one of 'field,
        'variable', or 'parameter'. Reports an error if a field,
        variable, or parameter of the given name already exists in
        this environment or any of its ancestors.
        """
        if (previous_line := self.get_line_number(name)) != -1:
            error(phase, position,
                  f'redeclaration of {name}, previously declared at '
                  f'line {previous_line}')
        else:
            self.__var_types[name] = var_type
            self.__var_positions[name] = position

    def get_line_number(self, name):
        """Get line number of definition of name, if it exists."""
        if name in self.__var_types:
            return self.__var_positions[name]
        if self.__parent:
            return self.__parent.get_line_number(name)
        return -1

    def contains(self, name):
        """Return whether or not name is defined in the environment."""
        return self.get_line_number(name) != -1

    def get_type(self, phase, position, name):
        """Look up a name and return the type of the entity it names.

        phase is the current compiler phase, position is the source
        position where the name appears, and name is a string
        containing the name. Reports an error if the given name is not
        defined and returns the int type.
        """
        if name in self.__var_types:
            return self.__var_types[name]
        if not self.__parent:
            error(phase, position, f'undefined variable or field {name}')
            # default to int
            return self.__global_env.lookup_type(phase, position, 'int')
        return self.__parent.get_type(phase, position, name)


@dataclass(slots=True)
class Position:
    """A class that represents a position in a uC source file."""

    line: int
    column: int
    end_line: int
    end_column: int

    def __str__(self):
        """Return a string representation of this position."""
        return f'{self.line}:{self.column}'

    def start(self):
        """Return the start line and column of this position."""
        return self.line, self.column

    def end(self):
        """Return the end line and column of this position."""
        return self.end_line, self.end_column


#################
# Base AST Node #
#################

@dataclass
class ASTNode:
    """The base class for all AST nodes.

    Implements default functionality for an AST node.
    """

    # used for giving each node a unique id
    next_id: ClassVar[Iterator[int]] = itertools.count()

    node_id: int = dataclasses.field(
        init=False, default_factory=lambda: next(ASTNode.next_id)
    )
    position: Position

    @functools.cached_property
    def __children(self):
        """Return the children of this AST node."""
        return [getattr(self, field) for field in self.__child_names]

    @functools.cached_property
    def __child_names(self):
        """Return the names of the children of this AST node."""
        return [field.name for field in dataclasses.fields(self)[2:]
                if field.default == dataclasses.MISSING]

    def __str__(self):
        """Return a string representation of this and its children."""
        result = '{' + type(self).__name__ + ':'
        for name in self.__child_names:
            result += ' ' + child_str(getattr(self, name))
        return result + '}'

    def graph_gen(self, parent_id, child_name, out):
        """Print a graph representation of the this AST node to out.

        The output is in a format compatible with Graphviz.
        """
        if parent_id:
            edge = '  {0} -> {{N{1} [label="{2}{4}"]}} [label="{3}"]'
            type_attr = getattr(self, 'type', None)
            print(edge.format(parent_id, self.node_id,
                              type(self).__name__, child_name,
                              f' ({type_attr.name})'
                              if type_attr else ''),
                  file=out)
            new_parent_id = f'N{self.node_id}'
        else:
            print('digraph {', file=out)
            new_parent_id = type(self).__name__
        for i, child in enumerate(self.__children):
            graph_gen(child, new_parent_id, i, self.__child_names[i],
                      out)
        if not parent_id:
            print('}', file=out)

    def write_types(self, ctx):
        """Write out a representation of this AST to ctx.out.

        Includes type annotations for each node that has a type.
        """
        ctx.print(type(self).__name__, indent=True, end='')
        if 'type' in dir(self):
            node_type = getattr(self, 'type')
            ctx.print(
                f': {node_type.name if node_type else node_type}',
                end=''
            )
        ctx.print(' {')
        new_ctx = ctx.clone()
        new_ctx.indent += '  '
        ast_map(lambda n: n.write_types(new_ctx), self.__children,
                lambda s: new_ctx.print(s, indent=True))
        ctx.print('}', indent=True)

    def validate(self, ctx):
        """Check that all func and type attributes have been computed."""
        ctx['trace'].append(self)
        for attr, uncomputed in (('type', GlobalEnv.uncomputed_type),
                                 ('func', GlobalEnv.uncomputed_function)):
            if attr in dir(self):
                node_type = getattr(self, attr)
                if node_type is uncomputed:
                    error(ctx.phase, self.position,
                          f'{uncomputed} in {type(self).__name__}; trace:'
                          + ''.join(f'\n  {type(node).__name__} at line '
                                    f'{node.position}'
                                    for node in ctx['trace']))
        ast_map(lambda n: n.validate(ctx), self.__children)
        ctx['trace'].pop()

    def find_decls(self, ctx):
        """Process the type and function declarations in this subtree.

        Adds the types and functions that are found to ctx.global_env.
        Reports an error if a type or function is multiply defined.
        """
        ast_map(lambda n: n.find_decls(ctx), self.__children)

    def resolve_types(self, ctx):
        """Resolve type names to the actual types they name.

        Uses ctx.global_env to look up a type name. Reports
        an error if an unknown type is named.
        """
        ast_map(lambda n: n.resolve_types(ctx), self.__children)

    def resolve_calls(self, ctx):
        """Match function calls to the actual functions they name.

        Uses ctx.global_env to look up a function name. Reports an
        error if an unknown function is named.
        """
        ast_map(lambda n: n.resolve_calls(ctx), self.__children)

    def check_names(self, ctx):
        """Check variable names and resolve variable accesses.

        Checks the names introduced within a type or function to
        ensure they are unique in the scope of the type or
        function. Resolves the types of name expressions.
        """
        ast_map(lambda n: n.check_names(ctx), self.__children)

    def basic_control(self, ctx):
        """Check basic control flow within this AST node."""
        ast_map(lambda n: n.basic_control(ctx), self.__children)

    def type_check(self, ctx):
        """Compute the type of each expression.

        Uses ctx['local_env'] to compute the type of a local name.
        Checks that the type of an expression is compatible with the
        context in which it is used.
        """
        ast_map(lambda n: n.type_check(ctx), self.__children)

    def advanced_control(self, ctx):
        """Check advanced control flow within this AST node."""
        ast_map(lambda n: n.advanced_control(ctx), self.__children)


#################
# AST Functions #
#################

def attribute(initial):
    """Specify that a field is an attribute.

    An attribute is initially defaulted to the given value but will be
    filled in with its proper value in an analysis phase.
    """
    return getattr(dataclasses, 'field')(default=initial, init=False)


def ast_map(func, item, terminal_func=None):
    """Map the given function on an AST component.

    If the item is a list, then the function is mapped across its
    elements. If the item is a terminal rather than an AST node, then
    terminal_func is applied if given.
    """
    ast_map_dispatch(item, func, terminal_func)


@functools.singledispatch
def ast_map_dispatch(item, _func, terminal_func=None):
    """Map the given function on an AST component.

    If the item is a list, then the function is mapped across its
    elements. If the item is a terminal rather than an AST node, then
    terminal_func is applied if given.
    """
    if terminal_func:
        terminal_func(item)


@ast_map_dispatch.register(ASTNode)
def ast_map_node(item, func, terminal_func=None):
    """Map the given function on an AST node."""
    func(item)


@ast_map_dispatch.register(list)
def ast_map_list(item, func, terminal_func=None):
    """Map the given function on a list."""
    for element in item:
        ast_map_dispatch(element, func, terminal_func)


##############
# Start Node #
##############

@dataclass
class DeclNode(ASTNode):
    """The base node for type and function declarations."""


@dataclass
class ProgramNode(ASTNode):
    """Represents a uC program."""

    decls: List[DeclNode]


##########################
# Names and Declarations #
##########################

@dataclass
class NameNode(ASTNode):
    """An AST node representing a name.

    raw is the actual string containing the name.
    """

    raw: str

    # add your code below if necessary


@dataclass
class BaseTypeNameNode(ASTNode):
    """The base node for type names and array type names.

    type is the instance of uctypes.Type associated with the type
    named by this node.
    """

    type: Optional[uctypes.Type] = attribute(GlobalEnv.uncomputed_type)

    def mangle(self):
        """Return the mangled name corresponding to this type.

        The mangled name is the name that should be used in code
        generation (Project 5).
        """
        raise NotImplementedError


@dataclass
class TypeNameNode(BaseTypeNameNode):
    """An AST node representing the name of a type.

    name is a node representing the name of the type.
    """

    name: NameNode

    def mangle(self):
        """Return the mangled name corresponding to this simple type.

        The mangled name is the name that should be used in code
        generation (Project 5).
        """
        if uctypes.PrimitiveType.is_primitive_type_name(self.name.raw):
            return f'UC_PRIMITIVE({self.name.raw})'
        # user-defined types have reference semantics
        return f'UC_REFERENCE({self.name.raw})'

    # add your code below if necessary
    def resolve_types(self, ctx):
        self.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, self.name.raw)


@dataclass
class ArrayTypeNameNode(BaseTypeNameNode):
    """An AST node representing an array type.

    elem_type is a node representing the element type.
    """

    elem_type: BaseTypeNameNode

    def mangle(self):
        """Return the mangled name corresponding to this array type.

        The mangled name is the name that should be used in code
        generation (Project 5).
        """
        return f'UC_ARRAY({self.elem_type.mangle()})'

    # add your code below if necessary
    def resolve_types(self, ctx):
        if self.elem_type.type is GlobalEnv.uncomputed_type:
            self.elem_type.resolve_types(ctx)
        self.type = self.elem_type.type.array_type


@dataclass
class FieldDeclNode(ASTNode):
    """An AST node representing a field declaration.

    vartype is a node representing the type and name is a node
    representing the name.
    """

    vartype: BaseTypeNameNode
    name: NameNode

    # add your code below if necessary
    def resolve_types(self, ctx):
        self.vartype.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, self.vartype.name.raw)


@dataclass
class ParameterNode(ASTNode):
    """An AST node representing a parameter declaration.

    vartype is a node representing the type and name is a node
    representing the name.
    """

    vartype: BaseTypeNameNode
    name: NameNode

    # add your code below if necessary
    def resolve_types(self, ctx):
        self.vartype.resolve_types(ctx)


@dataclass
class StructDeclNode(DeclNode):
    """An AST node representing a type declaration.

    name is the name of the type and fielddecls is a list of field
    declarations. type is the instance of uctypes.Type that is
    associated with this declaration.
    """

    name: NameNode
    fielddecls: List[FieldDeclNode]
    type: Optional[uctypes.Type] = attribute(GlobalEnv.uncomputed_type)
    local_env: Optional[VarEnv] = attribute(None)

    # add your code below
    def find_decls(self, ctx):
        self.type = ctx.global_env.add_type(
            ctx.phase, self.position, self.name.raw, self)

    def resolve_types(self, ctx):
        for i in range(len(self.fielddecls)):
            self.fielddecls[i].resolve_types(ctx)

    def check_names(self, ctx):
        # set local environment
        parent = ctx['local_env']
        self.env = VarEnv(parent, ctx.global_env)
        ctx['local_env'] = self.env
        # check fielddecls
        # reset parent environment
        ctx['local_env'] = parent


@dataclass
class FunctionDeclNode(DeclNode):
    """An AST node representing a function declaration.

    rettype is a node representing the return type, name is the name
    of the function, parameters is a list of parameter declarations,
    and body is the body of the function.
    """

    rettype: BaseTypeNameNode
    name: NameNode
    parameters: List[ParameterNode]
    body: 'BlockNode'  # 'BlockNode' is quoted since it's a forward
    # reference to BlockNode, which is defined in ucstmt.py. We can't
    # import ucstmt since it would result in a circular import --
    # ucstmt.py imports ucbase. See
    # https://www.python.org/dev/peps/pep-0484/#forward-references for
    # more details about forward references.
    func: Optional[ucfunctions.Function] = attribute(
        GlobalEnv.uncomputed_function
    )

    # add your code below
    def find_decls(self, ctx):  # phase1
        self.func = ctx.global_env.add_function(
            ctx.phase, self.position, self.name.raw, self)

    def resolve_types(self, ctx):
        # compute rettype
        self.rettype.resolve_types(ctx)
        self.func.rettype = self.rettype.type
        # compute parameters
        for i in range(len(self.parameters)):
            self.parameters[i].vartype.resolve_types(ctx)
            self.func.param_types.append(self.parameters[i].vartype.type)
        # compute body
        self.body.resolve_types(ctx)

    def check_names(self, ctx):
        # set local environment
        parent = ctx['local_env']
        self.env = VarEnv(parent, ctx.global_env)
        ctx['local_env'] = self.env
        # check parameters
        for param in self.parameters:
            self.env.add_variable(ctx.phase, self.position,
                                  param.name.raw, param.vartype.type)
        # check body
        self.body.check_names(ctx)
        # reset parent environment
        ctx['local_env'] = parent

######################
# Printing Functions #
######################


@functools.singledispatch
def child_str(child):
    """Convert an AST component into a string.

    Converts list elements to strings using str() rather than repr().
    """
    return str(child)


@child_str.register(list)
def child_str_list(child):
    """Convert an AST component into a string.

    Converts list elements to strings using str() rather than repr().
    """
    result = '['
    if child:
        result += child_str(child[0])
    for i in range(1, len(child)):
        result += ', ' + child_str(child[i])
    return result + ']'


@functools.singledispatch
def graph_gen(item, parent_id=None, child_num=None, child_name=None,
              out=sys.stdout):
    """Print a graph representation of the given AST component to out.

    The output is in a format compatible with Graphviz.
    """
    edge = '  {0} -> {{{0}T{1} [label="{2}"]}} [label="{3}"]'
    print(edge.format(parent_id, child_num,
                      str(item).replace('\\', '\\\\').replace('"', '\\"'),
                      child_name),
          file=out)


@graph_gen.register(ASTNode)
def graph_gen_ast(item, parent_id=None, _child_num=None,
                  child_name=None, out=sys.stdout):
    """Print a graph representation of the given AST node to out.

    The output is in a format compatible with Graphviz.
    """
    item.graph_gen(parent_id, child_name, out)


@graph_gen.register(list)
def graph_gen_list(item, parent_id=None, child_num=None,
                   child_name=None, out=sys.stdout):
    """Print a graph representation of the given list to out."""
    edge = '  {0} -> {{{0}L{1} [label="[list]"]}} [label="{2}"]'
    print(edge.format(parent_id, child_num, child_name), file=out)
    for i, child in enumerate(item):
        graph_gen(child, f'{parent_id}L{child_num}', i, i, out)
