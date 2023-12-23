from decaf_ast import (
    ClassReferenceExpressionRecord,
    FieldAccessExpressionRecord,
    MethodCallExpressionRecord,
    NewObjectExpressionRecord,
    SuperExpressionRecord,
    ThisExpressionRecord,
    VarExpressionRecord,
)
from decaf_scope import Scope


# begin primary
def p_primary(p):
    """
    primary : literal
            | lhs
            | method_invocation
    """
    p[0] = p[1]


def p_primary_wrapped_expr(p):
    """
    primary : LPAREN expr RPAREN
    """
    p[0] = p[2]


def p_primary_new_object(p):
    """
    primary : NEW ID LPAREN optional_arguments RPAREN
    """
    class_name = Scope.current.class_name
    s = p.lineno(1)
    t = p.lineno(5)
    p[0] = NewObjectExpressionRecord((s, t), p[2], p[4], class_name)


def p_primary_this(p):
    """
    primary : THIS
    """
    containing_class = Scope.current.class_name

    s = t = p.lineno(1)
    p[0] = ThisExpressionRecord((s, t), containing_class)


def p_primary_super(p):
    """
    primary : SUPER
    """
    containing_class = Scope.current.class_name

    s = t = p.lineno(1)
    p[0] = SuperExpressionRecord((s, t), containing_class)


def p_optional_arguments(p):
    """
    optional_arguments : arguments
                       | empty
    """
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]


# end primary


def p_arguments(p):
    """
    arguments : expr COMMA arguments
              | expr
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[3].insert(0, p[1])
        p[0] = p[3]


def p_lhs(p):
    """
    lhs : field_access
    """
    # array_access excluded
    p[0] = p[1]


def p_field_access(p):
    """
    field_access : primary DOT ID
                 | ID
    """
    if len(p) == 2:
        name = p[1]

        rec = Scope.current.lookup_symbol(name)
        if rec == None:
            # since the symbol doesnt exist in this scope or any preceding scope
            # this symbol is either missing or a class reference
            # we will assume it is a class reference and then perform another check during type checking
            l = p.lineno(1)
            p[0] = ClassReferenceExpressionRecord((l, l), name)
        else:
            s = t = p.lineno(1)
            p[0] = VarExpressionRecord((s, t), rec)
    else:
        class_name = Scope.current.class_name
        s = p.lineno(1)
        t = p.lineno(3)
        p[0] = FieldAccessExpressionRecord((s, t), p[1], p[3], class_name)


def p_method_invocation(p):
    """
    method_invocation : field_access LPAREN optional_arguments RPAREN
    """
    s = p.lineno(1)

    # based on our field_access, this can be a variable record or actual field access
    field_access = p[1]
    if not isinstance(field_access, FieldAccessExpressionRecord):
        raise Exception(
            f"method invocations not allowed with implicit object/class reference at line {s}"
        )

    class_name = Scope.current.class_name
    t = p.lineno(4)
    p[0] = MethodCallExpressionRecord(
        (s, t), field_access.base, field_access.name, p[3], class_name
    )
