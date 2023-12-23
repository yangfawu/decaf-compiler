from decaf_ast import (
    IntegerConstantExpressionRecord,
    FloatConstantExpressionRecord,
    StringConstantExpressionRecord,
    NullConstantExpressionRecord,
    BooleanConstantExpressionRecord,
)

# def p_literal(p):
#     """
#     literal : INTEGER_CONSTANT
#             | FLOAT_CONSTANT
#             | STRING
#             | NULL
#             | FALSE
#             | TRUE
#     """
#     s = t = p.lineno(1)
#     p[0] = ConstantExpressionRecord((s, t), p[1])


def p_literal_int(p):
    """
    literal : INTEGER_CONSTANT
    """
    s = t = p.lineno(1)
    p[0] = IntegerConstantExpressionRecord((s, t), p[1])


def p_literal_float(p):
    """
    literal : FLOAT_CONSTANT
    """
    s = t = p.lineno(1)
    p[0] = FloatConstantExpressionRecord((s, t), p[1])


def p_literal_string(p):
    """
    literal : STRING
    """
    s = t = p.lineno(1)
    p[0] = StringConstantExpressionRecord((s, t), p[1])


def p_literal_null(p):
    """
    literal : NULL
    """
    s = t = p.lineno(1)
    p[0] = NullConstantExpressionRecord((s, t))


def p_literal_boolean(p):
    """
    literal : TRUE
            | FALSE
    """
    s = t = p.lineno(1)
    p[0] = BooleanConstantExpressionRecord((s, t), p[1])
