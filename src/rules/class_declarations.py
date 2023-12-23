from decaf_ast import ClassRecord
from enum import Enum
from decaf_scope import Scope


class BodyDecl(Enum):
    FIELD = "F"
    METHOD = "M"
    CONSTRUCTOR = "C"


def p_class_decl(p):
    """
    class_decl : enter_class optional_extends LBRACE at_least_one_class_body_decl RBRACE
    """
    name = p[1]
    super_class_name = p[2]
    declarations = p[4]

    if name == super_class_name:
        raise Exception(f"class {name} cannot extend itself")

    # order the body declarations into their respective buckets
    buckets = {key: [] for key in BodyDecl}
    for key, decl in declarations:
        buckets[key].append(decl)

    # the field bucket currently contains list of fields
    # we need to flatten the bucket out so that is a flat list of fields
    # this is also when we set the containing class attribute
    fields = []
    for field_arr in buckets[BodyDecl.FIELD]:
        for f in field_arr:
            fields.append(f)

    Scope.exit_scope()
    p[0] = ClassRecord(
        name=name,
        super_class_name=super_class_name,
        constructors=buckets[BodyDecl.CONSTRUCTOR],
        methods=buckets[BodyDecl.METHOD],
        fields=fields,
    )


def p_enter_class(p):
    """
    enter_class : CLASS ID
    """
    name = p[2]

    Scope.enter_new_scope(block_child=True, class_name=name)

    p[0] = name


def p_optional_extends(p):
    """
    optional_extends : EXTENDS ID
                     | empty
    """
    # store the super class name, if any
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None


def p_at_least_one_class_body_decl(p):
    """
    at_least_one_class_body_decl : class_body_decl at_least_one_class_body_decl
                                 | class_body_decl
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[2].insert(0, p[1])
        p[0] = p[2]


# def p_class_body_decl(p):
#     """
#     class_body_decl : field_decl
#                     | method_decl
#                     | constructor_decl
#     """


def p_class_body_decl_field(p):
    """
    class_body_decl : field_decl
    """
    p[0] = (BodyDecl.FIELD, p[1])


def p_class_body_decl_method(p):
    """
    class_body_decl : method_decl
    """
    p[0] = (BodyDecl.METHOD, p[1])


def p_class_body_decl_constructor(p):
    """
    class_body_decl : constructor_decl
    """
    p[0] = (BodyDecl.CONSTRUCTOR, p[1])
