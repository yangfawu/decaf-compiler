from typing import List
from decaf_ast import (
    BuiltInTypeRecordCollection,
    FieldRecord,
    UserTypeRecord,
    VariableRecord,
)
from decaf_scope import Scope


def p_field_decl(p):
    """
    field_decl : modifier var_decl
    """
    modifier = p[1]
    variable_records: List["VariableRecord"] = p[2]

    scope_class_name = Scope.current.class_name

    # this is removed it will be checked during ClassRecord construction
    # for v in variable_records:
    #     if not Scope.current.add_symbol(v):
    #         l = p.lineno(1)
    #         raise Exception(f"Duplicate field name in class: {v.name} at line {l}")

    p[0] = [
        FieldRecord(
            visibility=modifier["visibility"],
            applicability="static" if modifier["is_static"] else "instance",
            type=v.type,
            name=v.name,
            containing_class=scope_class_name,
        )
        for v in variable_records
    ]


# begin modifier
def p_modifier(p):
    """
    modifier : optional_public_or_private optional_static
    """
    p[0] = {"visibility": p[1], "is_static": p[2]}


def p_optional_public_or_private(p):
    """
    optional_public_or_private : PUBLIC
                               | PRIVATE
                               | empty
    """
    if p[1] == None:
        p[0] = "private"  # by default
    else:
        p[0] = p[1]


def p_optional_static(p):
    """
    optional_static : STATIC
                    | empty
    """
    if p[1] == None:
        p[0] = False
    else:
        p[0] = True


# end modifier


def p_var_decl(p):
    """
    var_decl : type variables SEMICOLON
    """
    name_list = p[2]
    p[0] = [
        VariableRecord(type=p[1], variable_kind="local", name=name)
        for name in name_list
    ]


# def p_type(p):
#     """
#     type : INT
#          | FLOAT
#          | BOOLEAN
#          | ID
#          | VOID
#          | NULL
#     """
#     p[0] = TypeRecord(p[1])
# removing NULL because NULL is not a type, it is a value


def p_type_int(p):
    """
    type : INT
    """
    p[0] = BuiltInTypeRecordCollection.INT


def p_type_float(p):
    """
    type : FLOAT
    """
    p[0] = BuiltInTypeRecordCollection.FLOAT


def p_type_boolean(p):
    """
    type : BOOLEAN
    """
    p[0] = BuiltInTypeRecordCollection.BOOLEAN


def p_type_void(p):
    """
    type : VOID
    """
    p[0] = BuiltInTypeRecordCollection.VOID


def p_type_id(p):
    """
    type : ID
    """
    p[0] = UserTypeRecord(p[1])


def p_variables(p):
    """
    variables : variable
              | variable COMMA variables
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[3].insert(0, p[1])
        p[0] = p[3]


def p_variable(p):
    """
    variable : ID
    """
    p[0] = p[1]
