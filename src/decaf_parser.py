from decaf_tokens import tokens

start = "program"
precedence = (
    ("right", "EQUAL"),
    ("left", "OR"),
    ("left", "AND"),
    ("nonassoc", "DOUBLE_EQUAL", "NOT_EQUAL"),
    ("nonassoc", "LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
    ("right", "UMINUS", "UPLUS", "NOT"),
)


def p_empty(p):
    """
    empty :
    """
    pass


def p_program(p):
    """
    program : class_decl program
            | empty
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[2].insert(0, p[1])
        p[0] = p[2]


from rules.class_declarations import *
from rules.fields import *
from rules.methods_and_constructor import *
from rules.statements import *
from rules.literal import *
from rules.primary import *
from rules.expr import *


def p_error(p):
    if p:
        raise Exception(f"Syntax error at {p}")
    else:
        raise Exception("Syntax error at EOF")
