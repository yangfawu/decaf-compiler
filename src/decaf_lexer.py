from decaf_tokens import tokens, reserved_words

states = (("mlcomment", "exclusive"),)


# begin COMMENTS
def t_start_mlcomment(t):
    r"/\*"
    if not hasattr(t.lexer, "comment_depth"):
        t.lexer.comment_depth = 0
    t.lexer.comment_depth += 1
    t.lexer.push_state("mlcomment")


def t_mlcomment_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_mlcomment_end(t):
    r"\*/"
    t.lexer.comment_depth -= 1
    if t.lexer.comment_depth != 0:
        raise SyntaxError("Nested multi-line comments are not allowed.")
    t.lexer.pop_state()


def t_mlcomment_content(t):
    r"[^*]+(\*(?!/)[^*]*)*"
    pass


# we dont ignore anything because spacing is important for distinguishing between "*/" and "* /"
t_mlcomment_ignore = ""


def t_mlcomment_error(t):
    print("Illegal character", t)


def t_COMMENT(t):
    r"//.*"
    pass


# end COMMENTS

t_LBRACE = r"{"
t_RBRACE = r"}"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_SEMICOLON = r";"
t_COMMA = r","
t_DOT = r"\."
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_EQUAL = r"="
t_DOUBLE_PLUS = r"\+\+"
t_DOUBLE_MINUS = r"--"
t_AND = r"&&"
t_OR = r"\|\|"
t_NOT = r"!"
t_DOUBLE_EQUAL = r"=="
t_NOT_EQUAL = r"!="
t_LESS = r"<"
t_LESS_EQUAL = r"<="
t_GREATER = r">"
t_GREATER_EQUAL = r">="

def t_ID(t):
    r"[a-zA-z][a-zA-Z0-9_]*"

    t.type = reserved_words.get(t.value, "ID")
    match t.type:
        case "NULL":
            t.value = None
        case "TRUE":
            t.value = True
        case "FALSE":
            t.value = False
        case _:
            pass

    return t

def t_FLOAT_CONSTANT(t):
    r"[0-9]+\.[0-9]+"
    t.value = float(t.value)
    return t

def t_INTEGER_CONSTANT(t):
    r"[0-9]+"
    t.value = int(t.value)
    return t

def t_STRING(t):
    r"\"[^\"]*\" "
    return t

def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)

t_ignore = " \t"

def t_error(t):
    print("Illegal character", t)
