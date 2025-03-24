"""
ucstmt.py.

This file contains definitions of AST nodes that represent uC
statements.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

from dataclasses import dataclass
from typing import List, Optional
from ucexpr import ExpressionNode
# uncomment this import when you need it
from ucerror import error
import ucbase


@dataclass
class StatementNode(ucbase.ASTNode):
    """The base class for all statement nodes."""

    # add your code below if necessary


@dataclass
class BlockNode(StatementNode):
    """An AST node representing a block of statements.

    statements is a list of statement nodes.
    """

    statements: List[StatementNode]

    # add your code below if necessary
    def resolve_types(self, ctx):  # phase2
        for i in range(len(self.statements)):
            self.statements[i].resolve_types(ctx)

    def check_names(self, ctx):
        # set local environment
        parent = ctx['local_env']
        self.env = ucbase.VarEnv(parent, ctx.global_env)
        ctx['local_env'] = self.env
        # check statements
        for stmnt in self.statements:
            stmnt.check_names(ctx)
        # reset parent environment
        ctx['local_env'] = parent

    def basic_control(self, ctx):
        for stmnt in self.statements:
            stmnt.basic_control(ctx)


@dataclass
class VarDefNode(ucbase.ASTNode):
    """An AST node representing a variable definition.

    vartype is a node representing the type, name is a node
    representing the name, and expr is a node representing the
    initialization.
    """

    vartype: ucbase.BaseTypeNameNode
    name: ucbase.NameNode
    expr: ExpressionNode

    # add your code below if necessary
    def check_names(self, ctx):
        if self.vartype.type is ucbase.GlobalEnv.uncomputed_type:
            self.vartype.resolve_types(ctx)
        self.expr.check_names(ctx)
        ctx['local_env'].add_variable(
            ctx.phase, self.position, self.name.raw, self.vartype.type)


@dataclass
class VarDefStatementNode(StatementNode):
    """An AST node representing a variable definition statement.

    vardef is a node representing the definition itself.
    """

    vardef: VarDefNode

    # add your code below if necessary
    def check_names(self, ctx):
        self.vardef.check_names(ctx)


@dataclass
class IfNode(StatementNode):
    """An AST node representing an if statement.

    test is the condition, then_block is a block representing the then
    case, and else_block is a block representing the else case.
    """

    test: ExpressionNode
    then_block: BlockNode
    else_block: BlockNode

    # add your code below
    def check_names(self, ctx):
        # check test
        if not self.test.is_literal():
            self.test.check_names(ctx)
        # check then_block & else_block
        self.then_block.check_names(ctx)
        self.else_block.check_names(ctx)


@dataclass
class WhileNode(StatementNode):
    """An AST node representing a while statement.

    test is the condition and body is a block representing the body.
    """

    test: ExpressionNode
    body: BlockNode

    # add your code below
    def check_names(self, ctx):
        self.test.check_names(ctx)
        self.body.check_names(ctx)

    def basic_control(self, ctx):
        ctx['in_loop'] = True
        self.body.basic_control(ctx)
        ctx['in_loop'] = False


@dataclass
class ForNode(StatementNode):
    """An AST node representing a for statement.

    init is the initialization, test is the condition, update is the
    update expression, and body is a block representing the body.
    init, test, and update may be None if the corresponding expression
    or initialization is omitted.
    """

    init: Optional[ExpressionNode | VarDefNode]
    test: Optional[ExpressionNode]
    update: Optional[ExpressionNode]
    body: BlockNode

    # add your code below
    def check_names(self, ctx):
        # set local environment
        parent = ctx['local_env']
        self.env = ucbase.VarEnv(parent, ctx.global_env)
        ctx['local_env'] = self.env
        # check names in local environment
        self.init.check_names(ctx)
        self.test.check_names(ctx)
        self.update.check_names(ctx)
        # reset parent environment
        ctx['local_env'] = parent

    def basic_control(self, ctx):
        ctx['in_loop'] = True
        self.body.basic_control(ctx)
        ctx['in_loop'] = False


@dataclass
class BreakNode(StatementNode):
    """An AST node representing a break statement."""

    # add your code below
    def basic_control(self, ctx):
        if 'in_loop' in ctx:
            if not ctx['in_loop']:
                error(ctx.phase, self.position,
                      "break only allowed within a loop")
        error(ctx.phase, self.position, "break only allowed within a loop")


@dataclass
class ContinueNode(StatementNode):
    """An AST node representing a continue statement."""

    # add your code below
    def basic_control(self, ctx):
        if 'in_loop' in ctx:
            if not ctx['in_loop']:
                error(ctx.phase, self.position,
                      "continue only allowed within a loop")
        error(ctx.phase, self.position, "continue only allowed within a loop")


@dataclass
class ReturnNode(StatementNode):
    """An AST node representing a return statement.

    expr is the return expression if there is one, None otherwise.
    """

    expr: Optional[ExpressionNode]

    # add your code below
    def resolve_types(self, ctx):  # phase2
        self.expr.resolve_types(ctx)


@dataclass
class AssertNode(StatementNode):
    """An AST node representing an assert statement.

    test is the condition, test_string is the raw source string for
    the test, and message is either an expression representing the
    assertion message or None.
    """

    test: ExpressionNode
    test_string: str
    message: Optional[ExpressionNode]

    # add your code below if necessary


@dataclass
class ExpressionStatementNode(StatementNode):
    """An AST node representing a statement of just an expression.

    expr is the expression.
    """

    expr: ExpressionNode

    # add your code below if necessary
    def resolve_types(self, ctx):  # phase2
        self.expr.resolve_types(ctx)
