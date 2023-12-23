from typing import List
from decaf_ast import (
    IfStatementRecord,
    VariableDeclarationStatementRecord,
    VariableRecord,
    WhileStatementRecord,
    ForStatementRecord,
    ReturnStatementRecord,
    ExprStatementRecord,
    BlockStatementRecord,
    BreakStatementRecord,
    ContinueStatementRecord,
    SkipStatementRecord,
)
from decaf_scope import Scope


def p_enter_normal_scope(p):
    """
    enter_normal_scope : LBRACE
    """
    Scope.enter_new_scope()


def p_block(p):
    """
    block : enter_normal_scope stmt_list RBRACE
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BlockStatementRecord((s, t), stmt_seq=p[2])
    Scope.exit_scope()


def p_stmt_list(p):
    """
    stmt_list : stmt stmt_list
              | empty
    """
    if len(p) == 2:
        p[0] = []
    else:
        stmt = p[1]
        # we need to include this inside the AST, but not during prinint
        # if not isinstance(stmt, VariableDeclarationStatementRecord):
        #     p[2].insert(0, stmt)
        p[2].insert(0, stmt)
        p[0] = p[2]


# def p_stmt(p):
#     """
#     stmt : IF LPAREN expr RPAREN stmt ELSE stmt
#          | IF LPAREN expr RPAREN stmt
#          | WHILE LPAREN expr RPAREN stmt
#          | FOR LPAREN optional_stmt_expr SEMICOLON optional_expr SEMICOLON optional_stmt_expr RPAREN stmt
#          | RETURN optional_expr SEMICOLON
#          | stmt_expr SEMICOLON
#          | BREAK SEMICOLON
#          | CONTINUE SEMICOLON
#          | block
#          | var_decl
#          | SEMICOLON
#     """


def p_stmt_var_decl(p):
    """
    stmt : var_decl
    """
    variables: List["VariableRecord"] = p[1]

    l = p.lineno(1)
    for v in variables:
        if not Scope.current.add_symbol(v):
            raise Exception(f"Duplicate variable name in scope: {v.name} at line {l}")

    s = t = l
    p[0] = VariableDeclarationStatementRecord((s, t), variables)


def p_skip_stmt(p):
    """
    stmt : SEMICOLON
    """
    s = t = p.lineno(1)
    p[0] = SkipStatementRecord((s, t))


def p_block_stmt(p):
    """
    stmt : block
    """
    p[0] = p[1]


def p_continue_stmt(p):
    """
    stmt : CONTINUE SEMICOLON
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = ContinueStatementRecord((s, t))


def p_break_stmt(p):
    """
    stmt : BREAK SEMICOLON
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = BreakStatementRecord((s, t))


def p_expr_stmt(p):
    """
    stmt : stmt_expr SEMICOLON
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = ExprStatementRecord((s, t), expr=p[1])


def p_return_stmt(p):
    """
    stmt : RETURN optional_expr SEMICOLON
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = ReturnStatementRecord((s, t), return_value=p[2])


def p_for_stmt(p):
    """
    stmt : FOR LPAREN optional_stmt_expr SEMICOLON optional_expr SEMICOLON optional_stmt_expr RPAREN stmt
    """
    s = p.lineno(1)
    t = p.lineno(9)
    p[0] = ForStatementRecord(
        (s, t), init_expr=p[3], loop_condition=p[5], update_expr=p[7], loop_body=p[9]
    )


def p_if_stmt(p):
    """
    stmt : IF LPAREN expr RPAREN stmt
         | IF LPAREN expr RPAREN stmt ELSE stmt
    """
    s = p.lineno(1)
    if len(p) == 8:
        t = p.lineno(7)
        p[0] = IfStatementRecord((s, t), if_expr=p[3], then_stmt=p[5], else_stmt=p[7])
    else:
        t = p.lineno(5)
        p[0] = IfStatementRecord((s, t), if_expr=p[3], then_stmt=p[5], else_stmt=None)


def p_while_stmt(p):
    """
    stmt : WHILE LPAREN expr RPAREN stmt
    """
    s = p.lineno(1)
    t = p.lineno(5)
    p[0] = WhileStatementRecord((s, t), while_condition=p[3], while_body=p[5])


def p_optional_stmt_expr(p):
    """
    optional_stmt_expr : stmt_expr
                       | empty
    """
    p[0] = p[1]


def p_optional_expr(p):
    """
    optional_expr : expr
                  | empty
    """
    p[0] = p[1]


def p_stmt_expr(p):
    """
    stmt_expr : assign
              | method_invocation
    """
    p[0] = p[1]
