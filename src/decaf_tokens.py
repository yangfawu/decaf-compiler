reserved_words = {
    k: k.upper()
    for k in (
        "boolean",
        "break",
        "continue",
        "class",
        # "do",
        "else",
        "extends",
        "false",
        "float",
        "for",
        "if",
        "int",
        "new",
        "null",
        "private",
        "public",
        "return",
        "static",
        "super",
        "this",
        "true",
        "void",
        "while",
    )
}

SCOPES = (
    "LBRACE",
    "RBRACE",
    "LPAREN",
    "RPAREN",
)

OPERATORS = (
    "NOT",
    "TIMES",
    "DIVIDE",
    "DOUBLE_PLUS",
    "DOUBLE_MINUS",
    "PLUS",
    "MINUS",
    "LESS_EQUAL",
    "GREATER_EQUAL",
    "LESS",
    "GREATER",
    "DOUBLE_EQUAL",
    "NOT_EQUAL",
    "AND",
    "OR",
    "EQUAL",
)

tokens = (
    ("ID", "SEMICOLON", "COMMA", "STRING", "DOT", "INTEGER_CONSTANT", "FLOAT_CONSTANT")
    + SCOPES
    + OPERATORS
    + tuple(reserved_words.values())
)
