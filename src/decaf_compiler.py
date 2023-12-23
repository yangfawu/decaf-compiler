import sys
from pathlib import Path
import traceback
from typing import List
import ply.lex as lex
import ply.yacc as yacc
from decaf_absmc import print_code
from decaf_ast import ClassRecord
from decaf_codegen import resolve_sizes_and_offsets
import decaf_lexer
import decaf_parser
from decaf_config import *
from decaf_typecheck import type_check
from decaf_util import NestedStrList


def get_filename():
    fn = sys.argv[1] if len(sys.argv) > 1 else ""
    if fn == "":
        print("Missing file name for source program.")
        print("USAGE: python3 decaf_checker.py <decaf_source_file_name>")
        sys.exit()
    return fn


def create_lexer():
    return lex.lex(module=decaf_lexer, debug=LEXER_DEBUG)


def create_parser():
    return yacc.yacc(module=decaf_parser, debug=PARSER_DEBUG)


def get_file(filename: str):
    fh = open(filename, "r")
    source = fh.read()
    fh.close()
    return source


def get_output_path(filename: str):
    pobj = Path(filename)
    nobj = pobj.with_suffix(".ami")
    return nobj.name


def print_classes(classes: List["ClassRecord"], file):
    print(LINE, file=file)
    for c in classes:
        print(c, file=file)
        print(LINE, file=file)

def main():
    file_path = get_filename()
    source = get_file(file_path)

    lexer = create_lexer()
    parser = create_parser()

    classes: List["ClassRecord"] = None
    try:
        # tracking enabled to support p.lineno(n)
        classes = parser.parse(source, lexer=lexer, debug=PARSER_DEBUG, tracking=True)
    except Exception as e:
        print("parser encountered problem!!!")
        # print(traceback.format_exc())
        print(e)
        exit(1)

    if len(classes) < 1:
        print("no classes read")
        exit(1)

    try:
        type_check(classes)
    except Exception as e:
        print("type checker encountered problem!!!")
        print(traceback.format_exc())
        print(e)
        exit(1)
    
    # out_name = get_output_path(file_path)
    # with open(out_name, "w") as file:
    #     print_classes(classes, file)
    # return

    abcmc: "NestedStrList" = None
    try:
        static_slots = resolve_sizes_and_offsets(classes)
        abcmc = [c.generate_code() for c in classes]
        abcmc.append(f".static_data {static_slots}")
    except Exception as e:
        print("code generator encountered problem!!!")
        print(traceback.format_exc())
        print(e)
        exit(1)

    out_name = get_output_path(file_path)
    with open(out_name, "w") as file:
        print_code(abcmc, file)


if __name__ == "__main__":
    main()
