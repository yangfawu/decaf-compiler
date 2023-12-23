from typing import List
from decaf_ast import (
    BuiltInTypeRecord,
    ClassRecord,
    DependencyTree,
)

# NOTE: due to circular imports and implementation, the code for name resolution is placed with decaf_ast.py


def type_check(classes: List["ClassRecord"]):
    for class_rec in classes:
        # register class into dependency tree
        # we can use the tree to figure out if a class name is valid
        # we can use it to do name resolution that requires searching super classes
        DependencyTree.register_class(class_rec)

        # for each field, we need to check their type
        # if the type is not primitive, it needs to be a class that we have seen
        for field_rec in class_rec.fields:
            if isinstance(field_rec.type, BuiltInTypeRecord):
                continue
            target_class_name = field_rec.type.type
            if not DependencyTree.get_class_record(target_class_name):
                raise Exception(
                    f"field `{field_rec.name}` uses `{target_class_name}`, but it does not exist when parsing `{class_rec.name}`"
                )

        # type check every constructor
        for cons_rec in class_rec.constructors:
            # verify each parameter type
            for var_vec in cons_rec.parameters:
                if isinstance(var_vec.type, BuiltInTypeRecord):
                    continue
                target_class_name = var_vec.type.type
                if not DependencyTree.get_class_record(target_class_name):
                    raise Exception(
                        f"constructor argument `{var_vec.name}` uses `{target_class_name}`, but it does not exist when parsing `{class_rec.name}`"
                    )

            # type check the body
            if not cons_rec.body.resolve_type_correct(method_type="constructor"):
                raise Exception(
                    f"constructor in class `{class_rec.name}` has errors in its body"
                )

        for method_rec in class_rec.methods:
            # check the return type first
            return_type = method_rec.return_type
            if not isinstance(return_type, BuiltInTypeRecord):
                target_class_name = return_type.type
                if not DependencyTree.get_class_record(target_class_name):
                    raise Exception(
                        f"return type for method `{method_rec.name}` uses `{target_class_name}`, but it does not exist when parsing `{class_rec.name}`"
                    )

            # check each parameter next
            for var_vec in method_rec.parameters:
                if isinstance(var_vec.type, BuiltInTypeRecord):
                    continue
                target_class_name = var_vec.type.type
                if not DependencyTree.get_class_record(target_class_name):
                    raise Exception(
                        f"argument `{var_vec.name}` for method `{method_rec.name}` uses `{target_class_name}`, but it does not exist when parsing `{class_rec.name}`"
                    )

            # type check the body
            if not method_rec.body.resolve_type_correct(
                method_type="method", method_return_type=return_type
            ):
                raise Exception(
                    f"method `{method_rec.name}` in class `{class_rec.name}` has errors in its body"
                )
