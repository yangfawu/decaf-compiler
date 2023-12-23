from decaf_ast import AssignExpressionRecord, AutoExpressionRecord, BinaryExpressionRecord, ClassReferenceExpressionRecord, UnaryExpressionRecord

def p_expr_misc(p):
    """
    expr : primary
         | assign
    """
    p[0] = p[1]

def p_expr_addition(p):
    """
    expr : expr PLUS expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "add", p[1], p[3])

def p_expr_subtraction(p):
    """
    expr : expr MINUS expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "sub", p[1], p[3])

def p_expr_multiplication(p):
    """
    expr : expr TIMES expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "mul", p[1], p[3])

def p_expr_division(p):
    """
    expr : expr DIVIDE expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "div", p[1], p[3])

def p_expr_conjunction(p):
    """
    expr : expr AND expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "and", p[1], p[3])

def p_expr_disjunction(p):
    """
    expr : expr OR expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "or", p[1], p[3])

def p_expr_equality(p):
    """
    expr : expr DOUBLE_EQUAL expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "eq", p[1], p[3])

def p_expr_inequality(p):
    """
    expr : expr NOT_EQUAL expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "neq", p[1], p[3])

def p_expr_lte(p):
    """
    expr : expr LESS_EQUAL expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "leq", p[1], p[3])

def p_expr_gte(p):
    """
    expr : expr GREATER_EQUAL expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "geq", p[1], p[3])

def p_expr_lt(p):
    """
    expr : expr LESS expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "lt", p[1], p[3])

def p_expr_gt(p):
    """
    expr : expr GREATER expr
    """
    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = BinaryExpressionRecord((s, t), "gt", p[1], p[3])

def p_expr_not(p):
    """
    expr : NOT expr
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = UnaryExpressionRecord((s, t), "neg", p[2])

def p_expr_unary_minus(p):
    """
    expr : MINUS expr %prec UMINUS
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = UnaryExpressionRecord((s, t), "uminus", p[2])

def p_expr_unary_plus(p):
    """
    expr : PLUS expr %prec UPLUS
    """
    # just directly refer to the expression
    p[0] = p[2]

def p_assign_default(p):
    """
    assign : lhs EQUAL expr
    """
    lhs = p[1]
    rhs = p[3]

    # with our current field_access logic, the lhs can be a class reference
    # this shouldn't be allowed, so this check is here to stop it
    if isinstance(lhs, ClassReferenceExpressionRecord):
        l = p.lineno(1)
        raise Exception(f"Cannot have class reference on the LHS of assignment at line {l}")

    s = p.lineno(1)
    t = p.lineno(3)
    p[0] = AssignExpressionRecord((s, t), lhs, rhs)

def p_assign_post_inc(p):
    """
    assign : lhs DOUBLE_PLUS
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = AutoExpressionRecord((s, t), p[1], "inc", "post")

def p_assign_post_dec(p):
    """
    assign : lhs DOUBLE_MINUS
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = AutoExpressionRecord((s, t), p[1], "dec", "post")

def p_assign_pre_inc(p):
    """
    assign : DOUBLE_PLUS lhs
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = AutoExpressionRecord((s, t), p[1], "inc", "pre")

def p_assign_pre_dec(p):
    """
    assign : DOUBLE_MINUS lhs
    """
    s = p.lineno(1)
    t = p.lineno(2)
    p[0] = AutoExpressionRecord((s, t), p[1], "dec", "pre")
