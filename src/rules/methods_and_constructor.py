from decaf_ast import MethodRecord, ConstructorRecord, VariableRecord
from decaf_scope import Scope


def p_enter_function_scope(p):
    """
    enter_function_scope : LPAREN
    """
    # we skip next enter because the rule has the nonterminal block
    # block enters a new scope by default, but we want to include the block's root level variables
    # with the formal variables
    Scope.enter_new_scope(True)


# def p_method_decl(p):
#     """
#     method_decl : modifier type ID enter_function_scope optional_formals RPAREN block
#                 | modifier VOID ID enter_function_scope optional_formals RPAREN block
#     """
# the second is going away because we have added VOID to type


def p_method_decl(p):
    """
    method_decl : modifier type ID enter_function_scope optional_formals RPAREN block
    """
    modifier = p[1]

    scope_class_name = Scope.current.class_name
    variable_table = Scope.current.variable_table
    Scope.exit_scope()

    p[0] = MethodRecord(
        name=p[3],
        visibility=modifier["visibility"],
        applicability="static" if modifier["is_static"] else "instance",
        parameters=p[5],
        return_type=p[2],
        body=p[7],
        variable_table=variable_table,
        containing_class=scope_class_name
    )


def p_constructor_decl(p):
    """
    constructor_decl : modifier ID enter_function_scope optional_formals RPAREN block
    """
    constructor_name = p[2]
    scope_class_name = Scope.current.class_name
    if constructor_name != scope_class_name:
        raise Exception(f"Expected only constructor for {scope_class_name}, but got {constructor_name}")

    variable_table = Scope.current.variable_table
    Scope.exit_scope()

    p[0] = ConstructorRecord(
        visibility=p[1]["visibility"],
        parameters=p[4],
        body=p[6],
        containing_class=scope_class_name,
        variable_table=variable_table,
    )


def p_optional_formals(p):
    """
    optional_formals : formals
                     | empty
    """
    if p[1] == None:
        p[0] = []
    else:
        p[0] = p[1]


def p_formals(p):
    """
    formals : formal_param COMMA formals
            | formal_param
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[3].insert(0, p[1])
        p[0] = p[3]


def p_formal_param(p):
    """
    formal_param : type variable
    """
    rec = VariableRecord(type=p[1], variable_kind="formal", name=p[2])

    # we should be currently inside a Method scope
    # we will try to add the form variable
    if not Scope.current.add_symbol(rec):
        l = p.lineno(2)
        raise Exception(f"Duplicate formal variable name: {rec.name} at line {l}")

    p[0] = rec
