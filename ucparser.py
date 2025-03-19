"""
ucparser.py.

A PLY specification for a uC lexer and parser. Constructs an AST from
uC source code.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

import importlib
import json
from ucbase import *
from ucstmt import *
from ucexpr import *
import ucerror


#####################
# Lexical Structure #
#####################

# Reserved words
reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',
    'struct': 'STRUCT',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'return': 'RETURN',
    'assert': 'ASSERT',
    'true': 'TRUE',
    'false': 'FALSE',
    'new': 'NEW',
    'null': 'NULL'
}


token_type_map = {
    # Literals (identifier, integer, double, string)
    'IDENT': 'identifier', 'INTEGER': 'integer', 'DOUBLE': 'double',
    'STRING': 'string',

    # Operators (+, -, *, /, %, ||, &&, !, <, <=, >, >=, ==, !=, <<, >>)
    'PLUS': 'operator', 'MINUS': 'operator', 'TIMES': 'operator',
    'DIVIDE': 'operator', 'MODULO': 'operator', 'LOR': 'operator',
    'LAND': 'operator', 'LNOT': 'operator', 'LT': 'operator',
    'LE': 'operator', 'GT': 'operator', 'GE': 'operator',
    'EQ': 'operator', 'NE': 'operator', 'PUSH': 'operator',
    'POP': 'operator',

    # Assignment (=)
    'EQUALS': 'operator',

    # Increment/decrement (++,--)
    'INCREMENT': 'operator', 'DECREMENT': 'operator',

    # ID operator (#)
    'ID': 'operator',

    # Delimiters ( ) [ ] { } , . ;
    'LPAREN': 'delimiter', 'RPAREN': 'delimiter',
    'LBRACKET': 'delimiter', 'RBRACKET': 'delimiter',
    'LBRACE': 'delimiter', 'RBRACE': 'delimiter',
    'COMMA': 'delimiter', 'PERIOD': 'delimiter', 'SEMI': 'delimiter',
    'COLON': 'delimiter',
}


token_type_map.update({value: 'keyword' for value in reserved.values()})


tokens = list(token_type_map.keys())


# Operators
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MODULO = r'%'
t_LOR = r'\|\|'
t_LAND = r'&&'
t_LNOT = r'!'
t_LT = r'<'
t_GT = r'>'
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='
t_PUSH = r'<<'
t_POP = r'>>'


# Assignment operator
t_EQUALS = r'='


# Increment/decrement
t_INCREMENT = r'\+\+'
t_DECREMENT = r'--'


# ID operator
t_ID = r'\#'


# Delimiters
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_PERIOD = r'\.'
t_SEMI = r';'
t_COLON = r':'


# Identifiers
def t_IDENT(t):
    r'[a-zA-Z][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENT')  # Check for reserved words
    return t


# Integer literal
t_INTEGER = r'\d+([lL])?'


# Double literal
t_DOUBLE = r'(((\d*\.\d+)|(\d+\.))(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))'


# String literal
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.lexer.lineno += t.value.count('\n')
    return t


# Whitespace
def t_WHITESPACE(t):
    r'\s+'
    t.lexer.lineno += t.value.count('\n')


# Comment (C-Style)
def t_COMMENT(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')


# Comment (C++-Style)
def t_CPPCOMMENT(t):
    r'//.*\n'
    t.lexer.lineno += 1


# Error handling rule
def t_error(t):
    """Handle an error in lexing."""
    line, column = translate_position(t.lexer.lineno, t.lexer.lexpos)
    ucerror.error(0, Position(line, column, line, column + 1),
                  f"discarding unexpected character '{t.value[0]}' "
                  'while lexing')
    t.lexer.skip(1)


# Build lexer
lex = importlib.import_module('lex')
lexer = lex.lex()


# ----------------------------------------------------------------------
# Syntax
# ----------------------------------------------------------------------

precedence = (
    # Artificial precedence to resolve s/r conflict between
    # NameExpression and ArrayPrefix in the case of Name [.
    # We favor ArrayPrefix, and ArrayIndexExpression converts to a
    # NameExpressionNode where necessary.
    ('left', 'NAME'),
    # real precedence categories
    ('left', 'PUSH', 'POP'),
    ('right', 'EQUALS'),
    ('left', 'LOR'),
    ('left', 'LAND'),
    ('nonassoc', 'EQ', 'NE'),
    ('nonassoc', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'PREFIX', 'LNOT', 'INCREMENT', 'DECREMENT', 'ID'),
    ('left', 'PERIOD', 'LBRACKET'),
)


def p_program(p):
    """Program : Declarations"""
    p[0] = ProgramNode(get_position(p, 1), p[1])


def p_declarations(p):
    """Declarations : Declarations Declaration
                    | empty
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[1].append(p[2])
        p[0] = p[1]


def p_declaration(p):
    """Declaration : FunctionDecl
                   | StructDecl
    """
    p[0] = p[1]


def p_structdecl(p):
    """StructDecl : STRUCT Name LBRACE FieldDeclsOpt RBRACE SEMI
                  | STRUCT Name LBRACE FieldDeclsOpt RBRACE"""
    if len(p) == 6:
        ucerror.error(0, get_position(p, 5),
                      'uC requires a semicolon after a struct declaration')
    p[0] = StructDeclNode(get_position(p), p[2], p[4])


def p_structdecl_error(p):
    """StructDecl : STRUCT error RBRACE SEMI"""
    ucerror.error(0, get_position(p),
                  'syntax error in struct declaration')


def p_fielddeclsopt(p):
    """FieldDeclsOpt : FieldDecls
                     | empty
    """
    p[0] = p[1]


def p_fielddecls(p):
    """FieldDecls : FieldDecl
                  | FieldDecls FieldDecl
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]


def p_fielddecl(p):
    """FieldDecl : Type Name SEMI"""
    p[0] = FieldDeclNode(get_position(p), p[1], p[2])


def p_fielddecl_error(p):
    """FieldDecl : error SEMI"""
    ucerror.error(0, get_position(p),
                  'syntax error in field declaration')


def p_type(p):
    """Type : Name
            | ArrayPrefix RBRACKET
    """
    if len(p) == 2:
        p[0] = TypeNameNode(get_position(p), p[1])
    else:
        p[0] = ArrayTypeNameNode(get_position(p), p[1])


def p_name(p):
    """Name : IDENT"""
    p[0] = NameNode(get_position(p), p[1])


def p_arrayprefix(p):
    """ArrayPrefix : Name LBRACKET
                   | ArrayPrefix RBRACKET LBRACKET
    """
    if len(p) == 3:
        p[0] = TypeNameNode(get_child_position(p, 1), p[1])
    else:
        end_line, end_column = translate_position(p.lineno(2), p.lexpos(2))
        p[0] = ArrayTypeNameNode(Position(*get_position(p, 1).start(),
                                          end_line, end_column + 1),
                                 p[1])


def p_parametersopt(p):
    """ParametersOpt : Parameters
                      | empty
    """
    p[0] = p[1]


def p_parameters(p):
    """Parameters : Parameter
                   | Parameters COMMA Parameter
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[3])
        p[0] = p[1]


def p_parameter(p):
    """Parameter : Type Name"""
    p[0] = ParameterNode(get_position(p), p[1], p[2])


def p_functiondecl(p):
    """FunctionDecl : Type Name LPAREN ParametersOpt RPAREN Block"""
    p[0] = FunctionDeclNode(get_position(p), p[1], p[2], p[4], p[6])


def p_functiondecl_error(p):
    """FunctionDecl : error RBRACE"""
    ucerror.error(0, get_position(p),
                  'syntax error in function declaration')


def p_block(p):
    """Block : LBRACE StatementsOpt RBRACE"""
    p[0] = BlockNode(get_position(p), p[2])


def p_block_error(p):
    """Block : LBRACE error RBRACE"""
    ucerror.error(0, get_position(p),
                  'syntax error in block')


def p_statementsopt(p):
    """StatementsOpt : Statements
                     | empty
    """
    p[0] = p[1]


def p_statements(p):
    """Statements : Statement
                  | Statements Statement
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[2])
        p[0] = p[1]


def p_statement(p):
    """Statement : Block
                 | VarDefinitionStatement
                 | IfStatement
                 | WhileStatement
                 | ForStatement
                 | BreakStatement
                 | ContinueStatement
                 | ReturnStatement
                 | AssertStatement
                 | ExpressionStatement
                 | EmptyStatementError
    """
    p[0] = p[1]


def p_statement_error(p):
    """Statement : error SEMI
                 | IF error SEMI
                 | IF error RBRACE
                 | FOR error SEMI
                 | FOR error RBRACE
                 | WHILE error SEMI
                 | WHILE error RBRACE
                 | BREAK error SEMI
                 | CONTINUE error SEMI
                 | RETURN error SEMI
                 | ASSERT error SEMI
    """
    if len(p) == 3:
        ucerror.error(0, get_position(p),
                      f'syntax error: invalid statement')
    else:
        ucerror.error(0, get_position(p),
                      f'syntax error in {p[1]} statement')


def p_vardefinitionstatement(p):
    """VarDefinitionStatement : VarDefinition SEMI"""
    p[0] = VarDefStatementNode(get_position(p), p[1])


def p_vardefinition(p):
    """VarDefinition : Type Name EQUALS Expression"""
    p[0] = VarDefNode(get_position(p), p[1], p[2], p[4])


def p_ifstatement(p):
    """IfStatement : IF LPAREN Expression RPAREN Statement ELSE Statement
                   | IF LPAREN Expression RPAREN Statement
    """
    if not isinstance(p[5], BlockNode):
        ucerror.error(0, get_position(p, 5),
                      'uC requires a block as the body of a then clause')
    if len(p) == 6:
        p[0] = IfNode(get_position(p), p[3], p[5],
                      BlockNode(get_child_position(p, 5), []))
    elif isinstance(p[7], IfNode):
        p[0] = IfNode(get_position(p), p[3], p[5],
                      BlockNode(get_child_position(p, 7), [p[7]]))
    elif not isinstance(p[7], BlockNode):
        ucerror.error(0, get_position(p, 7),
                      'uC requires a block as the body of an else clause')
    else:
        p[0] = IfNode(get_position(p), p[3], p[5], p[7])


def p_ifstatement_error(p):
    """IfStatement : IF LPAREN error RBRACE"""
    ucerror.error(0, get_position(p),
                  'syntax error in if statement')


def p_whilestatement(p):
    """WhileStatement : WHILE LPAREN Expression RPAREN Statement"""
    if not isinstance(p[5], BlockNode):
        ucerror.error(0, get_position(p, 5),
                      'uC requires a block as the body of a while statement')
    else:
        p[0] = WhileNode(get_position(p), p[3], p[5])


def p_whilestatement_error(p):
    """WhileStatement : WHILE LPAREN error RBRACE"""
    ucerror.error(0, get_position(p),
                  'syntax error in while statement')


def p_forstatement(p):
    """ForStatement : FOR LPAREN ForInitialization SEMI ExpressionOpt \
                          SEMI ExpressionOpt RPAREN Statement"""
    if not isinstance(p[9], BlockNode):
        ucerror.error(0, get_position(p, 9),
                      'uC requires a block as the body of a for statement')
    else:
        p[0] = ForNode(get_position(p), p[3], p[5], p[7], p[9])


def p_forstatement_error(p):
    """ForStatement : FOR LPAREN error RBRACE"""
    ucerror.error(0, get_position(p),
                  'syntax error in for statement')


def p_forinitialization(p):
    """ForInitialization : VarDefinition
                         | ExpressionOpt
    """
    p[0] = p[1]


def p_breakstatement(p):
    """BreakStatement : BREAK SEMI"""
    p[0] = BreakNode(get_position(p))


def p_continuestatement(p):
    """ContinueStatement : CONTINUE SEMI"""
    p[0] = ContinueNode(get_position(p))


def p_returnstatement(p):
    """ReturnStatement : RETURN Expression SEMI
                       | RETURN SEMI
    """
    if len(p) == 4:
        p[0] = ReturnNode(get_position(p), p[2])
    else:
        p[0] = ReturnNode(get_position(p), None)


def p_assertstatement(p):
    """AssertStatement : ASSERT Expression SEMI
                       | ASSERT Expression COLON Expression SEMI
    """
    test_string = json.dumps(
        ucerror.error.source[p.lexpos(2): p.lexpos(3)].strip()
    )
    if len(p) == 4:
        p[0] = AssertNode(get_position(p), p[2], test_string, None)
    else:
        p[0] = AssertNode(get_position(p), p[2], test_string, p[4])


def p_expressionstatement(p):
    """ExpressionStatement : Expression SEMI
                           | Type Name SEMI
    """
    if len(p) != 3:
        ucerror.error(0, get_position(p),
                      'uC requires an initialization expression '
                      'in a local-variable definition')
    else:
        p[0] = ExpressionStatementNode(get_position(p), p[1])


def p_emptystatementerror(p):
    """EmptyStatementError : SEMI"""
    ucerror.error(0, get_position(p, 1),
                  'empty statements not allowed in uC')


def p_expression(p):
    """Expression : Literal
                  | NameExpression
                  | ParenthesizedExpression
                  | CallExpression
                  | NewExpression
                  | FieldAccessExpression
                  | ArrayIndexExpression
                  | UnaryPrefixOperation
                  | BinaryOperation
    """
    p[0] = p[1]


def p_expressionopt(p):
    """ExpressionOpt : Expression
                     | empty
    """
    if not p[1]:
        p[0] = None  # replace empty list with None
    else:
        p[0] = p[1]


# separate out literals
def p_literal(p):
    """Literal : IntegerLiteral
               | DoubleLiteral
               | StringLiteral
               | BooleanLiteral
               | NullLiteral
    """
    p[0] = p[1]


def p_integerliteral(p):
    """IntegerLiteral : INTEGER"""
    p[0] = IntegerNode(get_position(p), p[1])
    check_integer_literal(p[0])


def p_doubleliteral(p):
    """DoubleLiteral : DOUBLE"""
    p[0] = DoubleNode(get_position(p), p[1])


def p_stringliteral(p):
    """StringLiteral : STRING"""
    p[0] = StringNode(get_position(p), p[1])


def p_booleanliteral(p):
    """BooleanLiteral : TRUE
                      | FALSE
    """
    p[0] = BooleanNode(get_position(p), p[1])


def p_nullliteral(p):
    """NullLiteral : NULL"""
    p[0] = NullNode(get_position(p))


def p_nameexpression(p):
    """NameExpression : Name %prec NAME"""
    p[0] = NameExpressionNode(get_position(p), p[1])


def p_parenthesizedexpression(p):
    """ParenthesizedExpression : LPAREN Expression RPAREN"""
    p[0] = p[2]


def p_parenthesizedexpression_error(p):
    """ParenthesizedExpression : LPAREN error RPAREN"""
    ucerror.error(0, get_position(p),
                  'syntax error in parenthesized expression')


def p_callexpression(p):
    """CallExpression : Name LPAREN ArgumentsOpt RPAREN"""
    p[0] = CallNode(get_position(p), p[1], p[3])


def p_callexpression_error(p):
    """CallExpression : Name LPAREN error RPAREN"""
    ucerror.error(0, get_position(p),
                  'syntax error in call expression')


def p_argumentsopt(p):
    """ArgumentsOpt : Arguments
                    | empty
    """
    p[0] = p[1]


def p_arguments(p):
    """Arguments : Expression
                 | Arguments COMMA Expression
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[3])
        p[0] = p[1]


def p_newexpression(p):
    """NewExpression : NEW Type LPAREN ArgumentsOpt RPAREN
                     | NEW Type LBRACE ArgumentsOpt RBRACE
    """
    p[0] = NewNode(get_position(p), p[2], p[4])


def p_newexpression_error(p):
    """NewExpression : NEW error RPAREN
                     | NEW error RBRACE
    """
    ucerror.error(0, get_position(p),
                  'syntax error in new expression')


def p_fieldaccessexpression(p):
    """FieldAccessExpression : Expression PERIOD Name"""
    p[0] = FieldAccessNode(get_position(p), p[1], p[3])


def p_arrayindexexpression(p):
    """ArrayIndexExpression : Expression LBRACKET Expression RBRACKET
                            | ArrayPrefix Expression RBRACKET
    """
    if len(p) == 5:
        p[0] = ArrayIndexNode(get_position(p), p[1], p[3])
    elif isinstance(p[1], ArrayTypeNameNode):
        ucerror.error(0, get_child_position(p, 1),
                      'syntax error: invalid receiver for array '
                      'index expression')
        p[0] = ArrayIndexNode(get_position(p), p[1], p[2])
    else:
        p[0] = ArrayIndexNode(get_position(p),
                              NameExpressionNode(p[1].name.position,
                                                 p[1].name),
                              p[2])


def p_arrayindexexpression_error(p):
    """ArrayIndexExpression : error RBRACKET"""
    ucerror.error(0, get_position(p),
                  'syntax error in array index expression')


unary_ops = {
    '+': PrefixPlusNode,
    '-': PrefixMinusNode,
    '!': NotNode,
    '++': PrefixIncrNode,
    '--': PrefixDecrNode,
    '#': IDNode
}


def p_unaryprefixoperation(p):
    """UnaryPrefixOperation : PLUS Expression %prec PREFIX
                            | MINUS Expression %prec PREFIX
                            | LNOT Expression
                            | INCREMENT Expression
                            | DECREMENT Expression
                            | ID Expression
    """
    p[0] = unary_ops[p[1]](get_position(p), p[2])


binary_ops = {
    '+': PlusNode,
    '-': MinusNode,
    '*': TimesNode,
    '/': DivideNode,
    '%': ModuloNode,
    '||': LogicalOrNode,
    '&&': LogicalAndNode,
    '<': LessNode,
    '<=': LessEqualNode,
    '>': GreaterNode,
    '>=': GreaterEqualNode,
    '==': EqualNode,
    '!=': NotEqualNode,
    '=': AssignNode,
    '<<': PushNode,
    '>>': PopNode
}


def p_binaryoperation(p):
    """BinaryOperation : Expression PLUS Expression
                       | Expression MINUS Expression
                       | Expression TIMES Expression
                       | Expression DIVIDE Expression
                       | Expression MODULO Expression
                       | Expression LOR Expression
                       | Expression LAND Expression
                       | Expression LT Expression
                       | Expression LE Expression
                       | Expression GT Expression
                       | Expression GE Expression
                       | Expression EQ Expression
                       | Expression NE Expression
                       | Expression EQUALS Expression
                       | Expression PUSH Expression
                       | Expression POP Expression
    """
    p[0] = binary_ops[p[2]](get_position(p), p[1], p[3])


def p_empty(p):
    """empty :"""
    p[0] = []


def p_error(p):
    """Handle an error in."""
    if p:
        position = Position(
            *translate_position(p.lexer.lineno,
                                p.lexer.lexpos - len(p.value)),
            *translate_position(p.lexer.lineno, p.lexer.lexpos)
        )
        ucerror.error(0, position,
                      'syntax error: unexpected '
                      f"{token_type_map[p.type]} token '{p.value}'")
    else:
        line = len(ucerror.error.source_lines)
        column = len(ucerror.error.source_lines[-1]) + 1
        if ucerror.error.source_lines[-1][-1] == '\n':
            line += 1
            column = 1
        ucerror.error(0, Position(line, column, line, column),
                      'unexpected end of file while parsing')


INT_MIN = -2**31
LONG_MIN = -2**63


def check_integer_literal(inode):
    """Check validity of an integer literal."""
    if inode.text[-1] in 'lL':
        text = inode.text[:-1]
        lower = LONG_MIN
    else:
        text = inode.text
        lower = INT_MIN
    value = int(text)
    if value not in range(0, -lower):
        msg = ('syntax error: integer literal {} outside of valid '
               'range [0, {}]')
        ucerror.error(0, inode.position, msg.format(inode.text, -lower-1))


yacc = importlib.import_module('yacc')
parser = yacc.yacc(errorlog=yacc.NullLogger())


def get_position(p, index=None):
    """Return the position of the given symbol."""
    if index:
        line, column = translate_position(p.lineno(index), p.lexpos(index))
        return Position(line, column, line, column)
    start = translate_position(p.lineno(1), p.lexpos(1))
    last = len(p) - 1
    if isinstance(p[last], ASTNode):
        end = p[last].position.end()
    elif isinstance(p[last], str):
        end = translate_position(p.lineno(last),
                                 p.lexpos(last) + len(p[last]))
    else:
        end = translate_position(p.lineno(last), p.lexpos(last))
    return Position(*start, *end)


def translate_position(lineno, lexpos):
    """Translate the lexer position into a line and column."""
    line_start = ucerror.error.source.rfind('\n', 0, lexpos) + 1
    return lineno, lexpos - line_start + 1


def get_child_position(p, index):
    """Return the position of the given child, checking whether it exists."""
    if p[index]:
        return p[index].position
    return get_position(p, index)


def parse(filename):
    """Read a uC source file, parse it, and return an AST."""
    ucerror.error.source_name = filename
    with open(filename) as f:
        ucerror.error.source_lines = f.readlines()
    ucerror.error.source = ''.join(ucerror.error.source_lines)
    return parser.parse(ucerror.error.source, tracking=True)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('Usage: python3 {0} <filename>'.format(sys.argv[0]))
    else:
        outname = (sys.argv[1] if '.uc' not in sys.argv[1]
                   else sys.argv[1][:-3]) + '.dot'
        ast = parse(sys.argv[1])
        num_errors = ucerror.error_count()
        suffix = 's' if num_errors != 1 else ''
        if num_errors:
            print(f'{num_errors} error{suffix} generated in phase 0.')
            sys.exit(1)
        with open(outname, 'w') as out:
            graph_gen(ast, out=out)
        print('Wrote graph to {0}.'.format(outname))
