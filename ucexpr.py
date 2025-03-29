"""
ucexpr.py.

This file contains definitions of AST nodes that represent uC
expressions.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

from dataclasses import dataclass
from typing import List, Optional
from ucbase import attribute, GlobalEnv
import ucbase
# uncomment this import when you need it
from ucerror import error
import ucfunctions
import uctypes


#############################
# Base Node for Expressions #
#############################

@dataclass
class ExpressionNode(ucbase.ASTNode):
    """The base class for all nodes representing expressions.

    type is a reference to the computed uctypes.Type of this
    expression.
    """

    type: Optional[uctypes.Type] = attribute(GlobalEnv.uncomputed_type)

    def is_lvalue(self):
        """Return whether or not this node produces an l-value."""
        self.type.is_integral()  # style fix
        return False

    # add your code below if necessary
    def get_type(self):
        """Get type of ExpressionNode."""
        return self.type

    def is_literal(self):
        """Check whether ExpressionNode is a literal."""
        self.type.is_integral()  # style fix
        return False


############
# Literals #
############

@dataclass
class LiteralNode(ExpressionNode):
    """The base class for all nodes representing literals.

    text is the textual representation of the literal for code
    generation.
    """

    text: str

    # add your code below if necessary
    def is_literal(self):
        """Check whether ExpressionNode is a literal."""
        return True


@dataclass
class IntegerNode(LiteralNode):
    """An AST node representing an integer (int or long) literal."""

    # add your code below
    def resolve_types(self, ctx):
        """Type check for IntergerNode."""
        if self.text[-1] == "L":
            self.type = ctx.global_env.lookup_type(
                ctx.phase, self.position, 'long')
            return True
        if '.' in self.text:
            self.type = ctx.global_env.lookup_type(
                ctx.phase, self.position, 'double')
            return True
        self.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, 'int')
        return True


@dataclass
class DoubleNode(LiteralNode):
    """An AST node representing a double literal."""

    # add your code below
    def resolve_types(self, ctx):
        """Type check for DoubleNode."""
        self.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, 'double')


@dataclass
class StringNode(LiteralNode):
    """An AST node representing a string literal."""

    # add your code below
    def resolve_types(self, ctx):
        """Type check for StringNode."""
        self.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, 'string')


@dataclass
class BooleanNode(LiteralNode):
    """An AST node representing a boolean literal."""

    # add your code below
    def resolve_types(self, ctx):
        """Type check for BooleanNode."""
        self.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, 'boolean')


@dataclass
class NullNode(LiteralNode):
    """An AST node representing the null literal."""

    text: str = 'nullptr'

    # add your code below
    def resolve_types(self, ctx):
        """Type check for NullNode."""
        self.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, 'null')


###################
# Name Expression #
###################

@dataclass
class NameExpressionNode(ExpressionNode):
    """An AST node representing a name expression.

    name is an AST node denoting the actual name.
    """

    name: ucbase.NameNode

    # add your code below
    def check_names(self, ctx):
        """Check name in NameExpressionNode."""
        self.type = ctx['local_env'].get_type(
            ctx.phase, self.position, self.name.raw)


#######################
# Calls and Accessors #
#######################

@dataclass
class CallNode(ExpressionNode):
    """An AST node representing a function-call expression.

    name is an AST node representing the name of the function and args
    is a list of argument expressions to the function. func is a
    reference to the ucfunctions.Function named by this call.
    """

    name: ucbase.NameNode
    args: List[ExpressionNode]
    func: Optional[ucfunctions.Function] = attribute(
        GlobalEnv.uncomputed_function
    )

    # add your code below
    def resolve_types(self, ctx):
        """Resolve types for args in CallNode."""
        for arg in self.args:
            arg.resolve_types(ctx)

    def check_names(self, ctx):
        """Check names in CallNode."""
        for arg in self.args:
            if not arg.is_literal():
                arg.check_names(ctx)

    def resolve_calls(self, ctx):
        """Resolve calls in CallNode and set func."""
        for arg in self.args:
            arg.resolve_calls(ctx)
        self.func = ctx.global_env.lookup_function(
            ctx.phase, self.position, self.name.raw)

    def type_check(self, ctx):
        """Type check for CallNode."""
        # get callNode type
        self.type = self.func.rettype
        # get args type
        self.resolve_types(ctx)
        self.check_names(ctx)
        for arg in self.args:
            arg.type_check(ctx)
        # type check on args
        self.func.check_args(ctx.phase, self.position, self.args)
        return True


@dataclass
class NewNode(ExpressionNode):
    """An AST node representing a new expression.

    typename is an AST node representing the type of the object and
    args is a list of argument expressions to the constructor.
    """

    typename: ucbase.BaseTypeNameNode
    args: List[ExpressionNode]

    # add your code below
    def resolve_types(self, ctx):
        """Resolve type of NewNode."""
        self.typename.resolve_types(ctx)
        self.type = self.typename.type
        for arg in self.args:
            arg.resolve_types(ctx)

    def type_check(self, ctx):
        """Check types in NewNode."""
        self.type.check_args(ctx.phase, self.position, self.args)


@dataclass
class FieldAccessNode(ExpressionNode):
    """An AST node representing access to a field of an object.

    receiver is an expression representing the object whose field is
    being accessed and field is is an AST node representing the name
    of the field.
    """

    receiver: ExpressionNode
    field: ucbase.NameNode

    # add your code below
    def is_lvalue(self):
        """Return whether or not this node produces an l-value."""
        return True

    def resolve_types(self, ctx):
        """Resolve types in FieldAccessNode."""
        self.receiver.resolve_types(ctx)
        self.field.resolve_types(ctx)

    def check_names(self, ctx):
        """Check names in FieldAccessNode."""
        self.receiver.check_names(ctx)
        self.field.check_names(ctx)

    def type_check(self, ctx):
        """Check types in FieldAccessNode."""
        self.resolve_types(ctx)
        self.check_names(ctx)
        self.type = self.receiver.type.lookup_field(
            ctx.phase, self.position, self.field.raw, ctx.global_env)


@dataclass
class ArrayIndexNode(ExpressionNode):
    """An AST node representing indexing into an array.

    receiver is an expression representing the array and index the
    index expression.
    """

    receiver: ExpressionNode
    index: ExpressionNode

    # add your code below
    def resolve_types(self, ctx):
        """Resolve types in ArrayIndexNode."""
        self.receiver.resolve_types(ctx)
        self.index.resolve_types(ctx)

    def check_names(self, ctx):
        """Check names in ArrayIndexNode."""
        self.receiver.check_names(ctx)
        self.index.check_names(ctx)

    def type_check(self, ctx):
        """Check types in ArrayIndexNode."""
        self.resolve_types(ctx)
        self.check_names(ctx)
        # check receiver type
        self.type = self.receiver.type
        if not hasattr(self.receiver.type, 'elem_type'):
            error(ctx.phase, self.position, "Cannot index into non-array.")
            return False
        self.type = self.receiver.type.elem_type
        # check index type
        if not self.index.type.is_integral():
            error(ctx.phase, self.position,
                  f"Cannot index non-integer {self.index.type} into array.")
            return False
        return True


#####################
# Unary Expressions #
#####################

@dataclass
class UnaryPrefixNode(ExpressionNode):
    """A base AST node that represents a unary prefix operation.

    expr is the expression to which the operation is being applied and
    op_name is the string representation of the operator.
    """

    expr: ExpressionNode
    op_name: str

    # add your code below if necessary
    def get_type(self):
        """Get type of expr in UnaryPrefixNodes."""
        return self.expr.get_type()

    def resolve_types(self, ctx):
        """Resolve type in UnaryPrefixNodes."""
        self.expr.resolve_types(ctx)


@dataclass
class PrefixSignNode(UnaryPrefixNode):
    """A base AST node representing a prefix sign operation."""

    # add your code below if necessary


@dataclass
class PrefixPlusNode(PrefixSignNode):
    """An AST node representing a prefix plus operation."""

    op_name: str = '+'

    # add your code below if necessary


@dataclass
class PrefixMinusNode(PrefixSignNode):
    """An AST node representing a prefix minus operation."""

    op_name: str = '-'

    # add your code below if necessary


@dataclass
class NotNode(UnaryPrefixNode):
    """An AST node representing a not operation."""

    op_name: str = '!'

    # add your code below if necessary


@dataclass
class PrefixIncrDecrNode(UnaryPrefixNode):
    """A base AST node representing a prefix {in,de}crement operation."""

    # add your code below if necessary


@dataclass
class PrefixIncrNode(PrefixIncrDecrNode):
    """An AST node representing a prefix increment operation."""

    op_name: str = '++'

    # add your code below if necessary


@dataclass
class PrefixDecrNode(PrefixIncrDecrNode):
    """An AST node representing a prefix decrement operation.

    expr is the operand expression.
    """

    op_name: str = '--'

    # add your code below if necessary


@dataclass
class IDNode(UnaryPrefixNode):
    """An AST node representing an id operation."""

    op_name: str = '#'

    # add your code below if necessary


######################
# Binary Expressions #
######################

# Base classes

@dataclass
class BinaryOpNode(ExpressionNode):
    """A base AST node that represents a binary infix operation.

    lhs is the left-hand side expression, rhs is the right-hand side
    expression, and op_name is the name of the operator.
    """

    lhs: ExpressionNode
    rhs: ExpressionNode
    op_name: str

    # add your code below if necessary
    def type_error(self, expect, got):
        """Make type error message in BinaryOpNode."""
        return f"binary {self.op_name} operator expects {expect}, got {got}"

    def resolve_types(self, ctx):
        """Type check for IntergerNode."""
        self.type = ctx.global_env.lookup_type(
            ctx.phase, self.position, 'boolean')
        self.lhs.resolve_types(ctx)
        self.rhs.resolve_types(ctx)
        return True

    def check_names(self, ctx):
        """Check names in BinaryOpNode and children."""
        if not self.lhs.is_literal():
            self.lhs.check_names(ctx)
        if not self.rhs.is_literal():
            self.rhs.check_names(ctx)

    def type_check(self, ctx):
        """Check type of rhs & lhs in BinaryOpNode."""
        self.rhs.type_check(ctx)
        self.lhs.type_check(ctx)


@dataclass
class BinaryArithNode(BinaryOpNode):
    """A base AST node representing a binary arithmetic operation."""

    # add your code below if necessary
    def type_check(self, ctx):
        """Type check in BinaryArithNode."""
        super().type_check(ctx)
        if not self.lhs.type.is_numeric():
            mssg = self.type_error("int, long, or double", self.lhs.type)
            error(ctx.phase, self.lhs.position, mssg)
        if not self.rhs.type.is_numeric():
            mssg = self.type_error("int, long, or double", self.rhs.type)
            error(ctx.phase, self.rhs.position, mssg)
        self.type = self.lhs.type
        return True


@dataclass
class BinaryLogicNode(BinaryOpNode):
    """A base AST node representing a binary logic operation."""

    # add your code below if necessary


@dataclass
class BinaryCompNode(BinaryOpNode):
    """A base AST node representing binary comparison operation."""

    # add your code below if necessary


@dataclass
class EqualityTestNode(BinaryOpNode):
    """A base AST node representing an equality comparison."""

    # add your code below if necessary


# Arithmetic operations

@dataclass
class PlusNode(BinaryArithNode):
    """An AST node representing a binary plus operation."""

    op_name: str = '+'

    # add your code below
    def type_check(self, ctx):
        """Type check for PlusNode with string concatenation."""
        # TODO: add all cases from spec
        self.rhs.type_check(ctx)
        self.lhs.type_check(ctx)
        if self.lhs.type.is_numeric():
            super().type_check(ctx)

        if str(self.lhs.type) == 'string':
            self.type = self.lhs.type
            return True

        if self.lhs.type is not self.rhs.type:
            mssg = self.type_error(self.lhs.type, self.rhs.type)
            error(ctx.phase, self.position, mssg)
            return False

        self.type = self.lhs.type
        return True


@dataclass
class MinusNode(BinaryArithNode):
    """An AST node representing a binary minus operation."""

    op_name: str = '-'

    # add your code below if necessary


@dataclass
class TimesNode(BinaryArithNode):
    """An AST node representing a binary times operation."""

    op_name: str = '*'

    # add your code below if necessary


@dataclass
class DivideNode(BinaryArithNode):
    """An AST node representing a binary divide operation."""

    op_name: str = '/'

    # add your code below if necessary


@dataclass
class ModuloNode(BinaryArithNode):
    """An AST node representing a binary modulo operation."""

    op_name: str = '%'

    # add your code below if necessary


# Logical operations

@dataclass
class LogicalOrNode(BinaryLogicNode):
    """An AST node representing a logical or operation."""

    op_name: str = '||'

    # add your code below if necessary


@dataclass
class LogicalAndNode(BinaryLogicNode):
    """An AST node representing a logical and operation."""

    op_name: str = '&&'

    # add your code below if necessary


# Arithmetic comparisons

@dataclass
class LessNode(BinaryCompNode):
    """An AST node representing a less than operation."""

    op_name: str = '<'

    # add your code below if necessary


@dataclass
class LessEqualNode(BinaryCompNode):
    """An AST node representing a less than or equal operation.

    lhs is the left-hand operand and rhs is the right-hand operand.
    """

    op_name: str = '<='

    # add your code below if necessary


@dataclass
class GreaterNode(BinaryCompNode):
    """An AST node representing a greater than operation."""

    op_name: str = '>'

    # add your code below if necessary


@dataclass
class GreaterEqualNode(BinaryCompNode):
    """An AST node representing a greater than or equal operation."""

    op_name: str = '>='

    # add your code below if necessary


# Equality comparisons

@dataclass
class EqualNode(EqualityTestNode):
    """An AST node representing an equality comparison."""

    op_name: str = '=='

    # add your code below if necessary


@dataclass
class NotEqualNode(EqualityTestNode):
    """An AST node representing an inequality comparison."""

    op_name: str = '!='

    # add your code below if necessary


# Other binary operations

@dataclass
class AssignNode(BinaryOpNode):
    """An AST node representing an assignment operation."""

    op_name: str = '='

    # add your code below
    def type_check(self, ctx):
        """Check types in AssignNode."""
        super().type_check(ctx)
        if not self.lhs.is_lvalue():
            mssg = "assignment operator expects l-value on left-hand side" + \
                f", got {self.lhs.type}"
            error(ctx.phase, self.position, mssg)
            return False
        self.type = self.lhs.type
        return True


@dataclass
class PushNode(BinaryOpNode):
    """An AST node representing an array insertion operation."""

    op_name: str = '<<'

    # add your code below


@dataclass
class PopNode(BinaryOpNode):
    """An AST node representing an array extraction operation."""

    op_name: str = '>>'

    # add your code below
