from typing import Dict, List, Literal, Optional, Tuple, Union
from decaf_absmc import (
    ArgumentRegisterGenerator,
    GlobalTemporaryRegisterGenerator,
    LabelGenerator,
    TemporaryRegisterGenerator,
)
from decaf_util import Counter, NestedStrList


class TypeRecord:
    """
    Assigned: @BrianShao123
    """

    def __init__(self, type: str):
        self.type = type

    def __repr__(self):
        # purposely added here because sub-classes are supposed to implement this
        raise Exception("Not implemented")


class BuiltInTypeRecord(TypeRecord):
    def __init__(self, type: str):
        super().__init__(type)

    def __repr__(self):
        return self.type


class BuiltInTypeRecordCollection:
    """
    This collection contains a bunch of built-in types the program recognizes.
    Whenever we need a BuiltInTypeRecord, we use the ones from this collection.
    This will help with == checks during type checking.
    """

    INT = BuiltInTypeRecord("int")
    FLOAT = BuiltInTypeRecord("float")
    BOOLEAN = BuiltInTypeRecord("boolean")
    STRING = BuiltInTypeRecord("string")
    VOID = BuiltInTypeRecord("void")
    NULL = BuiltInTypeRecord("null")
    ERROR = BuiltInTypeRecord("error")


class UserTypeRecord(TypeRecord):
    """
    You use this record to represent T where T is the class.
    Ex: The bob in bob.some_instance_method() has type T.
    """

    def __init__(self, type: str):
        super().__init__(type)

    def __repr__(self):
        return f"user({self.type})"


class ClassLiteralTypeRecord(TypeRecord):
    """
    You use this record to represent Class<T> where T is the class.
    Ex: The A in A.some_static_method() has type Class<A>.
    """

    def __init__(self, type: str):
        super().__init__(type)

    def __repr__(self):
        return f"class-literal({self.type})"


class ClassRecord:
    def __init__(
        self,
        name: str,
        super_class_name: Optional[str],
        constructors: List["ConstructorRecord"],
        methods: List["MethodRecord"],
        fields: List["FieldRecord"],
    ):
        self.name = name
        self.super_class_name = super_class_name

        # NOTE: due to A04 constraints, there is <= 1 constructor
        self.constructors = constructors
        if len(constructors) > 1:
            raise Exception(
                f"A04 constraints does not allow `{name}` more than 1 constructor"
            )

        self.methods = methods
        self.method_map: Dict[str, "MethodRecord"] = {}
        for m in methods:
            key = f"{m.applicability}:{m.name}"
            if key in self.method_map:
                raise Exception(
                    f"A04 constraints do not allow overloaded method: {key}"
                )
            self.method_map[key] = m

        self.fields = fields
        self.field_map: Dict[str, "FieldRecord"] = {}
        for f in fields:
            key = f"{f.applicability}:{f.name}"
            if key in self.field_map:
                raise Exception(f"duplicate field name: {key}")
            self.field_map[key] = f

        # this field represents the total # of slots required to fit an instance of this class
        # the total # includes slots to fit super and super... classes
        # this will be computed during code generation
        self.size: int = None

    def generate_code(self, **context) -> "NestedStrList":
        out = []

        for c in self.constructors:
            out.append(c.generate_code(**context))

        for m in self.methods:
            out.append(m.generate_code(**context))

        return out

    def __repr__(self):
        return "\n".join(
            [
                f"Class Name: {self.name}",
                f"Superclass Name: {self.super_class_name or ''}",
                "Fields:",
                *map(repr, self.fields),
                "Constructors:",
                *map(repr, self.constructors),
                "Methods:",
                *map(repr, self.methods),
            ]
        )


class DependencyTreeNode:
    def __init__(self, record: "ClassRecord"):
        self.parent: Optional["DependencyTreeNode"] = None
        self.record = record
        self.subclasses: List["DependencyTreeNode"] = []


class DependencyTree:
    BUILTIN_SUBTYPES = {
        BuiltInTypeRecordCollection.INT: [],
        BuiltInTypeRecordCollection.FLOAT: [BuiltInTypeRecordCollection.INT],
        BuiltInTypeRecordCollection.BOOLEAN: [],
        BuiltInTypeRecordCollection.STRING: [],
    }

    DEPENDENCY_TREE_ROOT = DependencyTreeNode(None)
    CLASS_NAME_TO_NODE: Dict[str, "DependencyTreeNode"] = {}

    @staticmethod
    def register_class(record: "ClassRecord"):
        """
        Takes a ClassRecord and attempts to add it to a dependency tree.
        Raises Exception if class name is already taken.
        Raises Exception if class extends an unregistered class.
        """

        name = record.name
        if name in DependencyTree.CLASS_NAME_TO_NODE:
            raise Exception(f"duplicate class name: {name}")

        parent = DependencyTree.DEPENDENCY_TREE_ROOT
        super_class_name = record.super_class_name
        if super_class_name != None:
            if super_class_name in DependencyTree.CLASS_NAME_TO_NODE:
                parent = DependencyTree.CLASS_NAME_TO_NODE[super_class_name]
            else:
                raise Exception(
                    f"class {name} cannot extend unknown class: {super_class_name}"
                )

        node = DependencyTreeNode(record)
        node.parent = parent
        parent.subclasses.append(node)
        DependencyTree.CLASS_NAME_TO_NODE[name] = node

    @staticmethod
    def __builtin_is_subtype(a: "BuiltInTypeRecord", b: "BuiltInTypeRecord") -> bool:
        if a == b:
            return True
        return a in DependencyTree.BUILTIN_SUBTYPES[b]

    @staticmethod
    def __classname_is_subtype(a: str, b: str) -> bool:
        if a not in DependencyTree.CLASS_NAME_TO_NODE:
            raise Exception(f"unknown class name: {a}")
        if b not in DependencyTree.CLASS_NAME_TO_NODE:
            raise Exception(f"unknown class name: {b}")

        curr = DependencyTree.CLASS_NAME_TO_NODE[a]
        target = DependencyTree.CLASS_NAME_TO_NODE[b]
        while curr != None:
            if curr == target:
                return True
            curr = curr.parent
        return False

    @staticmethod
    def is_subtype(a: "TypeRecord", b: "TypeRecord") -> bool:
        """
        Returns True if `a` is a subtype of `b`. Returns False otherwise.
        """
        if a == BuiltInTypeRecordCollection.ERROR:
            return False
        if b == BuiltInTypeRecordCollection.ERROR:
            return False

        if isinstance(a, BuiltInTypeRecord):
            if isinstance(b, BuiltInTypeRecord):
                return DependencyTree.__builtin_is_subtype(a, b)
            elif isinstance(b, UserTypeRecord):
                return a == BuiltInTypeRecordCollection.NULL
        elif isinstance(a, UserTypeRecord) and isinstance(b, UserTypeRecord):
            return DependencyTree.__classname_is_subtype(a.type, b.type)
        elif isinstance(a, ClassLiteralTypeRecord) and isinstance(
            b, ClassLiteralTypeRecord
        ):
            return DependencyTree.__classname_is_subtype(a.type, b.type)

        return False

    @staticmethod
    def get_class_record(name: str) -> Optional["ClassRecord"]:
        """
        Takes a class name that returns the class record if any.
        """
        if name in DependencyTree.CLASS_NAME_TO_NODE:
            return DependencyTree.CLASS_NAME_TO_NODE[name].record
        return None

    @staticmethod
    def __resolve_field(
        class_node: "DependencyTreeNode", key: str
    ) -> Optional["FieldRecord"]:
        if class_node == DependencyTree.DEPENDENCY_TREE_ROOT:
            return None

        if key in class_node.record.field_map:
            return class_node.record.field_map[key]

        return DependencyTree.__resolve_field(class_node.parent, key)

    @staticmethod
    def resolve_field(
        class_name: str, field_name: str, is_static: bool
    ) -> Optional["FieldRecord"]:
        if class_name in DependencyTree.CLASS_NAME_TO_NODE:
            app = "static" if is_static else "instance"
            key = f"{app}:{field_name}"
            field = DependencyTree.__resolve_field(
                DependencyTree.CLASS_NAME_TO_NODE[class_name], key
            )
            if field != None and field.applicability != app:
                raise Exception(
                    f"illegal program state - expected {app} but got a field with {field.applicability} instead"
                )
            return field
        return None

    @staticmethod
    def __resolve_method(
        class_node: "DependencyTreeNode", key: str
    ) -> Optional["MethodRecord"]:
        if class_node == DependencyTree.DEPENDENCY_TREE_ROOT:
            return None

        if key in class_node.record.method_map:
            return class_node.record.method_map[key]

        return DependencyTree.__resolve_method(class_node.parent, key)

    @staticmethod
    def resolve_method(
        class_name: str, method_name: str, is_static: bool
    ) -> Optional["MethodRecord"]:
        if class_name in DependencyTree.CLASS_NAME_TO_NODE:
            app = "static" if is_static else "instance"
            key = f"{app}:{method_name}"
            method = DependencyTree.__resolve_method(
                DependencyTree.CLASS_NAME_TO_NODE[class_name], key
            )
            if method != None and method.applicability != app:
                raise Exception(
                    f"illegal program state - expected {app} but got a method_name with {method.applicability} instead"
                )
            return method
        return None


class ConstructorRecord:
    id_gen = Counter(1)

    def __init__(
        self,
        visibility: Literal["public", "private"],
        parameters: List["VariableRecord"],
        body: "StatementRecord",
        variable_table: List["VariableRecord"],
        containing_class: str,
    ):
        self.id = ConstructorRecord.id_gen.next()
        self.visibility = visibility
        self.parameters = parameters
        self.body = body
        self.variable_table = variable_table
        self.containing_class = containing_class

    def get_label(self) -> str:
        return f"C_{self.id}"

    def generate_code(self, **context) -> "NestedStrList":
        # we need fresh pool of registers
        GlobalTemporaryRegisterGenerator.reset()

        self_l = self.get_label()

        arg_gen = ArgumentRegisterGenerator()

        # assign $a0 with the new object reference
        this_a = arg_gen.next()

        # assign the parameters with argument registers
        for v in self.parameters:
            if v.value_reg != None:
                raise Exception("argument somehow got assigned with register already")
            v.value_reg = arg_gen.next()

        # we dont use **{**context, ...} because it is not expected for self_t to be specified in context already
        body_code = self.body.generate_code(**context, self_t=this_a)

        # NOTE: A05 contraints state that constructors do not have return statements
        #   so we need to add one to make sure the control stack is actually updated once the procedure finishes
        return [
            f"# {self.containing_class} constructor",
            f"{self_l}:",
            body_code,
            "ret",
        ]

    def __repr__(self):
        params = ", ".join(map(lambda r: str(r.id), self.parameters))
        return "\n".join(
            [
                f"CONSTRUCTOR: {self.id}, {self.visibility}",
                f"Constructor Parameters: {params}",
                "Variable Table:",
                *map(lambda v: v.get_table_details(), self.variable_table),
                "Constructor Body:",
                repr(self.body),
            ]
        )


ExprRange = Tuple[int, int]


class ExpressionRecord:
    def __init__(self, location: ExprRange, type: Optional["TypeRecord"]):
        self.location = location
        self.type = type

        # this is the register that stores the value of the expression
        # this is expected to set during code generation
        self.value_reg: str = None

    def compute_type(self, **context) -> "TypeRecord":
        """
        Override this method to determine the type during type checking
        """
        raise Exception("not implemented")

    def resolve_type(self, **context) -> "TypeRecord":
        if self.type != None:
            return self.type

        self.type = self.compute_type(**context)
        if self.type == BuiltInTypeRecordCollection.ERROR:
            raise Exception(f"uncaught type error at lines {self.location}")

        return self.type

    def generate_code(self, **context) -> "NestedStrList":
        # subclasses need to implement this to support code generation
        # remember to set self.value_reg
        raise Exception("not implemented")

    def get_value_register(self) -> str:
        if self.value_reg == None:
            raise Exception(f"tried to use register, but it is not set - {self}")
        return self.value_reg

    def __repr__(self):
        # purposely added here because sub-classes are supposed to implement this
        raise Exception("not implemented")


class ConstantExpressionRecord(ExpressionRecord):
    def __init__(
        self,
        location: ExprRange,
        value: Union[int, float, str, bool, None],
        type: "BuiltInTypeRecord",
    ):
        super().__init__(location, type)
        self.value = value

    def get_value_string(self) -> str:
        # purposely added here because sub-classes are supposed to implement this
        raise Exception("not implemented")

    def __repr__(self):
        return f"Constant({self.get_value_string()})"


class NullConstantExpressionRecord(ConstantExpressionRecord):
    def __init__(self, location: ExprRange):
        super().__init__(location, None, BuiltInTypeRecordCollection.NULL)

    def get_value_string(self):
        return "Null"

    def generate_code(self, **context):
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        return [
            f"move_immed_i {out_t}, 0",
            f"# {out_t} = null",
        ]


class StringConstantExpressionRecord(ConstantExpressionRecord):
    def __init__(self, location: ExprRange, value: str):
        super().__init__(location, value, BuiltInTypeRecordCollection.STRING)

    def get_value_string(self):
        # use repr to keep escaped characters
        return f"String-constant({repr(self.value)})"

    def generate_code(self, **context):
        raise Exception("A05 constraints does not support strings")


class FloatConstantExpressionRecord(ConstantExpressionRecord):
    def __init__(self, location: ExprRange, value: float):
        super().__init__(location, value, BuiltInTypeRecordCollection.FLOAT)

    def get_value_string(self):
        return f"Float-constant({str(self.value)})"

    def generate_code(self, **context):
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        return [f"move_immed_f {out_t}, {self.value}", f"# {out_t} = {self.value}"]


class IntegerConstantExpressionRecord(ConstantExpressionRecord):
    def __init__(self, location: ExprRange, value: int):
        super().__init__(location, value, BuiltInTypeRecordCollection.INT)

    def get_value_string(self):
        return f"Integer-constant({str(self.value)})"

    def generate_code(self, **context):
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        return [f"move_immed_i {out_t}, {self.value}", f"# {out_t} = {self.value}"]


class BooleanConstantExpressionRecord(ConstantExpressionRecord):
    CODE_TRUE = 1
    CODE_FALSE = 0

    def __init__(self, location: ExprRange, value: bool):
        super().__init__(location, value, BuiltInTypeRecordCollection.BOOLEAN)

    def get_value_string(self):
        return str(self.value)

    def generate_code(self, **context):
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        b = (
            BooleanConstantExpressionRecord.CODE_TRUE
            if self.value
            else BooleanConstantExpressionRecord.CODE_FALSE
        )

        return [
            f"move_immed_i {out_t}, {b}",
            f"# {out_t} = {self.value}",
        ]


class VarExpressionRecord(ExpressionRecord):
    def __init__(self, location: ExprRange, variable: "VariableRecord"):
        super().__init__(location, variable.type)
        self.value = variable.id

        # NOTE: regarding code generation
        #   Even though we have access to the variable record, we cannot assign the expression register right now.
        #   This is because it is occupying any register during the initialization of this record.
        #   Instead, we conduct the assignment during code generation.
        self.variable = variable

    def generate_code(self, **context):
        # we do not create new temporary register
        # we want to share the same register as the referenced variable
        self.value_reg = self.variable.get_value_register()

        # no code needed to set register
        return [
            f"# ref {self.value_reg} for {self.variable} aka {self.variable.name}",
        ]

    def __repr__(self):
        return f"Variable({self.value})"


class UnaryExpressionRecord(ExpressionRecord):
    def __init__(
        self,
        location: ExprRange,
        operator: Literal["uminus", "neg"],
        expr: "ExpressionRecord",
    ):
        # we initially treat type as None because ExpressionRecord has no known type
        super().__init__(location, None)
        self.operator = operator
        self.expr = expr

    def compute_type(self, **context):
        e_type = self.expr.resolve_type(**context)

        # handle uminus case
        if self.operator == "uminus":
            if e_type in (
                BuiltInTypeRecordCollection.INT,
                BuiltInTypeRecordCollection.FLOAT,
            ):
                return e_type
            raise Exception(
                f"unary minus expected an integer or float at lines {self.location}"
            )

        # handle neg case
        if e_type == BuiltInTypeRecordCollection.BOOLEAN:
            return e_type
        raise Exception(f"negation expected a boolean at lines {self.location}")

    def generate_code(self, **context):
        expr_code = self.expr.generate_code(**context)
        expr_t = self.expr.get_value_register()

        offset_t = GlobalTemporaryRegisterGenerator.next()

        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t
        if self.operator == "unminus":
            if self.expr.type == BuiltInTypeRecordCollection.INT:
                return [
                    expr_code,
                    f"move_immed_i {offset_t}, -1",
                    f"# {offset_t} = -1",
                    f"imul {out_t}, {offset_t}, {expr_t}",
                    f"# {out_t} = -{expr_t}",
                ]
            else:
                # if not INT, then must be a float
                return [
                    expr_code,
                    f"move_immed_f {offset_t}, -1.0",
                    f"# {offset_t} = -1.0",
                    f"fmul {out_t}, {offset_t}, {expr_t}",
                    f"# {out_t} = -{expr_t}",
                ]

        # if not uminus, then must be negation
        return [
            expr_code,
            f"move_immed_i {offset_t}, 1",
            f"# {offset_t} = 1",
            f"isub {out_t}, {offset_t}, {expr_t}",
            f"# {out_t} = !{expr_t}",
        ]

    def __repr__(self):
        return f"Unary({self.operator}, {self.expr})"


class BinaryExpressionRecord(ExpressionRecord):
    def __init__(
        self,
        location: ExprRange,
        operator: Literal[
            "add",
            "sub",
            "mul",
            "div",
            "and",
            "or",
            "eq",
            "neq",
            "lt",
            "leq",
            "gt",
            "geq",
        ],
        left: "ExpressionRecord",
        right: "ExpressionRecord",
    ):
        super().__init__(location, None)
        self.operator = operator
        self.left = left
        self.right = right

    def compute_type(self, **context):
        left_type = self.left.resolve_type(**context)
        right_type = self.right.resolve_type(**context)
        allowed_num_types = (
            BuiltInTypeRecordCollection.INT,
            BuiltInTypeRecordCollection.FLOAT,
        )
        match self.operator:
            case "add" | "sub" | "mul" | "div":
                if left_type in allowed_num_types and right_type in allowed_num_types:
                    if BuiltInTypeRecordCollection.FLOAT in (left_type, right_type):
                        return BuiltInTypeRecordCollection.FLOAT
                    else:
                        return BuiltInTypeRecordCollection.INT
                raise Exception(
                    f"`{self.operator}` operation only expected integers and floats at lines {self.location}"
                )
            case "and" | "or":
                if (
                    left_type == BuiltInTypeRecordCollection.BOOLEAN
                    and right_type == BuiltInTypeRecordCollection.BOOLEAN
                ):
                    return BuiltInTypeRecordCollection.BOOLEAN
                raise Exception(
                    f"`{self.operator}` operation only expected booleans at lines {self.location}"
                )
            case "lt" | "leq" | "gt" | "geq":
                if left_type in allowed_num_types and right_type in allowed_num_types:
                    return BuiltInTypeRecordCollection.BOOLEAN
                raise Exception(
                    f"`{self.operator}` operation only expected integers and floats at lines {self.location}"
                )
            case "eq" | "neq":
                if DependencyTree.is_subtype(
                    left_type, right_type
                ) or DependencyTree.is_subtype(right_type, left_type):
                    return BuiltInTypeRecordCollection.BOOLEAN
                raise Exception(
                    f"`{self.operator}` operation expected one of the operands to be a subtype of the other at lines {self.location}"
                )

    def generate_code(self, **context):
        out = [
            self.left.generate_code(**context),
            self.right.generate_code(**context),
        ]
        left_t = self.left.get_value_register()
        right_t = self.right.get_value_register()

        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t
        match self.operator:
            case "add" | "sub" | "mul" | "div":
                if self.type == BuiltInTypeRecordCollection.INT:
                    # the result is INT, which means both operands are INT
                    return [
                        out,
                        f"i{self.operator} {out_t}, {left_t}, {right_t}",
                        f"# {out_t} = {left_t} {self.operator} {right_t}",
                    ]
                else:
                    # the result is FLOAT, which means 1-2 operands are FLOAT

                    # if an operand is INT, we need an extra instruction for casting
                    if self.left.type == BuiltInTypeRecordCollection.INT:
                        out.append(
                            [
                                f"itof {left_t}, {left_t}",
                                f"# {left_t} = (float) {left_t}",
                            ]
                        )
                    if self.right.type == BuiltInTypeRecordCollection.INT:
                        out.append(
                            [
                                f"itof {right_t}, {right_t}",
                                f"# {right_t} = (float) {right_t}",
                            ]
                        )

                    return [
                        out,
                        f"f{self.operator} {out_t}, {left_t}, {right_t}",
                        f"# {out_t} = {left_t} {self.operator} {right_t}",
                    ]
            case "and":
                # we can use multiplication to mimic and
                # 0 * 0 = 0
                # 0 * 1 = 0
                # 1 * 0 = 0
                # 1 * 1 = 1
                return [
                    out,
                    f"imul {out_t}, {left_t}, {right_t}",
                    f"# {out_t} = {left_t} AND {right_t}",
                ]
            case "or":
                # we can use addition to mimic or
                # 0 + 0 = 0
                # 0 + 1 = 1
                # 1 + 0 = 1
                # 1 + 1 = 2
                # however, if both are true, the result is 2 (invalid boolean value)

                zero_t = GlobalTemporaryRegisterGenerator.next()
                return [
                    out,
                    f"iadd {out_t}, {left_t}, {right_t}",
                    f"# {out_t} = {left_t} + {right_t}" f"move_immed_i {zero_t}, 0",
                    f"# {zero_t} = 0",
                    f"igt {out_t}, {out_t}, {zero_t}",
                    f"# {out_t} = {left_t} OR {right_t}",
                ]
            case "lt" | "leq" | "gt" | "geq":
                if self.left.type == self.right.type:
                    # both operands are either INT or FLOAT
                    if self.left.type == BuiltInTypeRecordCollection.INT:
                        return [
                            out,
                            f"i{self.operator} {out_t}, {left_t}, {right_t}",
                            f"# {out_t} = {left_t} {self.operator} {right_t}",
                        ]
                    else:
                        return [
                            out,
                            f"f{self.operator} {out_t}, {left_t}, {right_t}",
                            f"# {out_t} = {left_t} {self.operator} {right_t}",
                        ]
                else:
                    # one or both operands are FLOAT

                    # if an operand is INT, we need an extra instruction for casting
                    if self.left.type == BuiltInTypeRecordCollection.INT:
                        out.append(
                            [
                                f"itof {left_t}, {left_t}",
                                f"# {left_t} = (float) {left_t}",
                            ]
                        )
                    if self.right.type == BuiltInTypeRecordCollection.INT:
                        out.append(
                            [
                                f"itof {right_t}, {right_t}",
                                f"# {right_t} = (float) {right_t}",
                            ]
                        )

                    return [
                        out,
                        f"f{self.operator} {out_t}, {left_t}, {right_t}",
                        f"# {out_t} = {left_t} {self.operator} {right_t}",
                    ]
            case "eq" | "neq":
                # we know from type checking that one of the operand is a subtype of the other
                # we assume left is subtype of right
                a, b = self.left, self.right

                # use check to change if needed
                if DependencyTree.is_subtype(self.right.type, self.left.type):
                    a, b = b, a
                # NOTE: since there is a swap, we cannot trust left_t and right_t anymore

                # register to store a < b
                less_comp_t = GlobalTemporaryRegisterGenerator.next()

                # register to store a > b
                more_comp_t = GlobalTemporaryRegisterGenerator.next()

                # compute the values of t1 and t2
                a_t = a.get_value_register()
                b_t = b.get_value_register()
                if b.type == BuiltInTypeRecordCollection.FLOAT:
                    # [a] can be an INT, so we need to cast if needed
                    if a.type == BuiltInTypeRecordCollection.INT:
                        out.append(
                            [
                                f"itof {a_t}, {a_t}",
                                f"# {a_t} = (float) {a_t}",
                            ]
                        )
                    out.append(
                        [
                            f"flt {less_comp_t}, {a_t}, {b_t}",
                            f"# {less_comp_t} = {a_t} < {b_t}",
                            f"fgt {more_comp_t}, {a_t}, {b_t}",
                            f"# {more_comp_t} = {a_t} > {b_t}",
                        ]
                    )
                else:
                    # both operands are INT or addresses (so technically INT)
                    out.append(
                        [
                            f"ilt {less_comp_t}, {a_t}, {b_t}",
                            f"# {less_comp_t} = {a_t} < {b_t}",
                            f"igt {more_comp_t}, {a_t}, {b_t}",
                            f"# {more_comp_t} = {a_t} > {b_t}",
                        ]
                    )

                # compute (t1 or t2) to determine !=
                zero_t = GlobalTemporaryRegisterGenerator.next()
                out.append(
                    [
                        f"iadd {out_t}, {less_comp_t}, {more_comp_t}",
                        f"# {out_t} = {less_comp_t} + {more_comp_t}"
                        f"move_immed_i {zero_t}, 0",
                        f"# {zero_t} = 0",
                        f"igt {out_t}, {out_t}, {zero_t}",
                        f"# {out_t} = {less_comp_t} OR {more_comp_t}"
                        f"# {out_t} = {a_t} != {b_t}",
                    ]
                )

                if self.operator == "neq":
                    return out

                # handle eq operator
                # we need to flip the result of !=

                one_t = GlobalTemporaryRegisterGenerator.next()
                return [
                    out,
                    f"move_immed_i {one_t}, 1",
                    f"# {one_t} = 1",
                    f"isub {out_t}, {one_t}, {out_t}",
                    f"# {out_t} = !{out_t}",
                    f"# {out_t} = {a_t} == {b_t}",
                ]

    def __repr__(self):
        return f"Binary({self.operator}, {self.left}, {self.right})"


class AssignExpressionRecord(ExpressionRecord):
    def __init__(
        self, location: ExprRange, left: "ExpressionRecord", right: "ExpressionRecord"
    ):
        super().__init__(location, None)
        self.left = left
        self.right = right

    def compute_type(self, **context):
        left_type = self.left.resolve_type(**context)
        right_type = self.right.resolve_type(**context)
        if DependencyTree.is_subtype(right_type, left_type):
            return right_type
        raise Exception(
            f"assignment at lines {self.location} expected the RHS to be a subtype of LHS"
        )

    def generate_code(self, **context):
        right_code = self.right.generate_code(**context)
        right_t = self.right.get_value_register()

        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        # NOTE:
        # we already know from type checking that the RHS is a subtype of LHS
        #   unlike Java where the result type is that of LHS, it is the RHS in Decaf
        #   for this reason, this expression's value register should store RHS's register

        out = [
            right_code,
            f"move {out_t}, {right_t}",
            f"# {out_t} = {right_t} ({out_t} is the result of the assignment)",
        ]

        # out = [right_code]

        # NOTE:
        # however, for the actual assignment, we have to consider casting if dealing with built-in types
        if self.left.type == BuiltInTypeRecordCollection.FLOAT:
            if self.right.type == BuiltInTypeRecordCollection.INT:
                out.append(
                    [
                        f"itof {right_t}, {right_t}",
                        f"# {right_t} = (float) {right_t}",
                    ]
                )
            else:
                # no need to do casting because RHS type has to be float
                pass

        # NOTE:
        # we also need to consider if LHS is field or a regular variable
        #   if regular variable, then we just need to copy RHS's value into LHS's register
        #   if field, then we need to actuall update the heap where the field is located
        if isinstance(self.left, FieldAccessExpressionRecord):
            # through type checking, we already know that the base of the access is either an object or class

            offset_t = GlobalTemporaryRegisterGenerator.next()
            out.append(
                [
                    f"move_immed_i {offset_t}, {self.left.field.offset}",
                    f"# {offset_t} = {self.left.field.offset}",
                ]
            )

            if isinstance(self.left.base.type, ClassLiteralTypeRecord):
                # if base is a class, we don't need to compute any base address
                # we can just rely on the field to determine where to store
                return [
                    out,
                    f"hstore sap, {offset_t}, {right_t}",
                    f"# {self.left.base.type.type}.{self.left.name} = {right_t}",
                ]

            # we now know that the base is an object
            # we need to run the code of the base to determine the base address
            base_code = self.left.base.generate_code(**context)
            base_t = self.left.base.get_value_register()
            return [
                out,
                base_code,
                f"hstore {base_t}, {offset_t}, {right_t}",
                f"# {base_t}.{self.left.name} = {right_t}",
            ]

        # handle regular variable LHS case
        left_code = self.left.generate_code(**context)
        left_t = self.left.get_value_register()
        return [out, left_code, f"move {left_t}, {right_t}", f"# {left_t} = {right_t}"]

    def __repr__(self):
        return f"Assign({self.left}, {self.right}, {self.left.type}, {self.right.type})"


# TODO
class AutoExpressionRecord(ExpressionRecord):
    def __init__(
        self,
        location: ExprRange,
        expr: "ExpressionRecord",
        operation: Literal["inc", "dec"],
        position: Literal["pre", "post"],
    ):
        super().__init__(location, None)
        self.expr = expr
        self.operation = operation
        self.position = position

    def compute_type(self, **context):
        expr_type = self.expr.resolve_type(**context)
        if expr_type in (
            BuiltInTypeRecordCollection.INT,
            BuiltInTypeRecordCollection.FLOAT,
        ):
            return expr_type
        raise Exception(
            f"auto expression expected inner expression to be an integer or float at lines {self.location}"
        )

    def generate_code(self, **context):
        expr_code = self.expr.generate_code(**context)
        expr_t = self.expr.get_value_register()

        out = [expr_code]

        # compute new value
        one_t = GlobalTemporaryRegisterGenerator.next()
        new_value_t = GlobalTemporaryRegisterGenerator.next()

        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t
        if self.expr.type == BuiltInTypeRecordCollection.INT:
            out.append([f"move_immed_i {one_t}, 1", f"# {one_t} = 1"])
            if self.operation == "inc":
                out.append(
                    [
                        f"iadd {new_value_t}, {expr_t}, {one_t}",
                        f"# {new_value_t} = {expr_t} add {one_t}",
                    ]
                )
            else:
                out.append(
                    [
                        f"isub {new_value_t}, {expr_t}, {one_t}",
                        f"# {new_value_t} = {expr_t} sub {one_t}",
                    ]
                )
        else:
            out.append([f"move_immed_f {one_t}, 1.0", f"# {one_t} = 1.0"])
            if self.operation == "inc":
                out.append(
                    [
                        f"fadd {new_value_t}, {expr_t}, {one_t}",
                        f"# {new_value_t} = {expr_t} add {one_t}",
                    ]
                )
            else:
                out.append(
                    [
                        f"fsub {new_value_t}, {expr_t}, {one_t}",
                        f"# {new_value_t} = {expr_t} sub {one_t}",
                    ]
                )

        # store the correct value into THIS expression's register

        if self.position == "pre":
            out.append([f"move {out_t}, {new_value_t}", f"# {out_t} = {new_value_t}"])
        else:
            out.append([f"move {out_t}, {expr_t}", f"# {out_t} = {new_value_t}"])

        # NOTE:
        # we now also need to update the register of the old expression with the new value

        if isinstance(self.expr, FieldAccessExpressionRecord):
            # if the old expression is a field access, we need to update the heap

            offset_t = GlobalTemporaryRegisterGenerator.next()
            out.append(
                [
                    f"move_immed_i {offset_t}, {self.expr.field.offset}",
                    f"# {offset_t} = {self.expr.field.offset}",
                ]
            )

            if isinstance(self.expr.base.type, ClassLiteralTypeRecord):
                # if base is a class, we don't need to compute any base address
                # we can just rely on the field to determine where to store
                return [out, f"hstore sap, {offset_t}, {new_value_t}"]

            # we now know that the base is an object
            # we need to run the code of the base to determine the base address

            # NOTE:
            # base_code = self.left.base.generate_code() # this line not needed because we called self.expr.generate_code() already
            #   doing so already generated the code for the base as well
            #   which means we can just use the assigned register directly
            base_t = self.expr.base.get_value_register()
            return [out, f"hstore {base_t}, {offset_t}, {new_value_t}"]

        # we now know we don't have to update heap
        return [out, f"move {expr_t}, {new_value_t}", f"# {expr_t} = {new_value_t}"]

    def __repr__(self):
        return f"Auto({self.expr}, {self.operation}, {self.position})"


class FieldAccessExpressionRecord(ExpressionRecord):
    def __init__(
        self,
        location: ExprRange,
        base: "ExpressionRecord",
        name: str,
        containing_class: str,
    ):
        super().__init__(location, None)
        self.base = base
        self.name = name
        self.containing_class = containing_class

        # set this during type resolving
        self.field: "FieldRecord" = None

    def compute_type(self, **context):
        base_type = self.base.resolve_type(**context)

        field = None
        if isinstance(base_type, UserTypeRecord):
            field = DependencyTree.resolve_field(base_type.type, self.name, False)
        elif isinstance(base_type, ClassLiteralTypeRecord):
            field = DependencyTree.resolve_field(base_type.type, self.name, True)

        if field == None:
            raise Exception(
                f"unknown field access using `{self.name}` at lines {self.location}"
            )

        if (
            field.visibility == "private"
            and field.containing_class != self.containing_class
        ):
            raise Exception(
                f"found field access for `{self.name}`, but the field is private and is being used outside its class at lines {self.locations}"
            )

        self.field = field
        return field.type

    def generate_code(self, **context):
        """
        NOTE: this should only be used if you want to generate code that will help you get the actual field value
        """
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        offset_t = GlobalTemporaryRegisterGenerator.next()
        out = [
            f"move_immed_i {offset_t}, {self.field.offset}",
            f"# {offset_t} = {self.field.offset}",
        ]

        if isinstance(self.base.type, ClassLiteralTypeRecord):
            # if base is a class, we don't need to compute any base address
            # we can just rely on the field to determine where to store
            return [out, f"hload {out_t}, sap, {offset_t}"]

        # we now know that the base is an object
        # we need to run the code of the base to determine the base address
        base_code = self.base.generate_code(**context)
        base_t = self.base.get_value_register()
        return [out, base_code, f"hload {out_t}, {base_t}, {offset_t}"]

    def __repr__(self):
        return f"Field-access({self.base}, {self.name}, {self.field.id})"


class MethodCallExpressionRecord(ExpressionRecord):
    def __init__(
        self,
        location: ExprRange,
        base: "ExpressionRecord",
        name: str,
        arguments: List["ExpressionRecord"],
        containing_class: str,
    ):
        super().__init__(location, None)
        self.base = base
        self.name = name
        self.arguments = arguments
        self.containing_class = containing_class

        # set this during type resolving
        self.method: Optional["MethodRecord"] = None

    def compute_type(self, **context):
        base_type = self.base.resolve_type(**context)

        # determine the method being referenced using name resolution
        method = None
        if isinstance(base_type, UserTypeRecord):
            method = DependencyTree.resolve_method(base_type.type, self.name, False)
        elif isinstance(base_type, ClassLiteralTypeRecord):
            method = DependencyTree.resolve_method(base_type.type, self.name, True)

        # determine the type of this expression from reference
        if method == None:
            raise Exception(
                f"unknown method call using `{self.name}` at lines {self.location}"
            )

        if (
            method.visibility == "private"
            and method.containing_class != self.containing_class
        ):
            raise Exception(
                f"found method call for `{self.name}`, but the method is private and is being used outside its class at lines {self.location}"
            )

        if len(method.parameters) != len(self.arguments):
            raise Exception(
                f"found method call for `{self.name}`, but the method expects {len(method.parameters)} arguments instead of {len(self.arguments)} at lines {self.location}"
            )

        for i, (p, a) in enumerate(zip(method.parameters, self.arguments)):
            a_type = a.resolve_type(**context)
            if not DependencyTree.is_subtype(a_type, p.type):
                raise Exception(
                    f"found method call for `{self.name}`, but the argument at index {i} is incompatible at lines {a.location}"
                )

        self.method = method
        return method.return_type

    def generate_code(self, **context):
        out = []

        # NOTE: before we start evaluating the expressions
        #   we need to understand that the registers created after this point does not need to be saved
        #       this is because they will be copied to a0 ... a_m where m is the number of arguments needed for calling the method
        #   for this reason, we can reset the temporary generator to the point BEFORE the procedure call
        #       so that we can re-use all those temporary registers used while evaluating expressions AFTER procedure call
        seed = GlobalTemporaryRegisterGenerator.get_curr()

        # from type checking, we already know that each argument is a subtype of its corresponding parameter
        # thus, we need to handle casting of ints to floats, if necessary
        # everything else does not need casting
        for p, a in zip(self.method.parameters, self.arguments):
            out.append(a.generate_code(**context))
            if (
                p.type == BuiltInTypeRecordCollection.FLOAT
                and a.type == BuiltInTypeRecordCollection.INT
            ):
                arg_t = a.get_value_register()
                out.append(f"itof {arg_t}, {arg_t}")

        # we now have every argument computed and casted

        # we now need to save every $a register we are about to modify
        saved_regs: List[str] = []

        a_needed = len(self.method.parameters)
        if self.method.applicability == "instance":
            a_needed += 1
        arg_gen = ArgumentRegisterGenerator()
        while a_needed > 0:
            arg_a = arg_gen.next()
            saved_regs.append(arg_a)
            out.append(f"save {arg_a}")
            a_needed -= 1

        # we then need to save all temporary registers that have been used
        t_needed = seed
        temp_gen = TemporaryRegisterGenerator()
        while t_needed > 0:
            temp_t = temp_gen.next()
            saved_regs.append(temp_t)
            out.append(f"save {temp_t}")
            t_needed -= 1

        # we now need to transfer the contents of the relevant registers into argument registers
        arg_gen = ArgumentRegisterGenerator()

        # if this method is not static, then $a0 is dedicated to holding a value of the base object address
        if self.method.applicability == "instance":
            base_a = arg_gen.next()
            base_code = self.base.generate_code(**context)
            base_t = self.base.get_value_register()
            out.append(
                [base_code, f"move {base_a}, {base_t}", f"# {base_a} = {base_t}"]
            )
        else:
            # if the method is static, then we don't need to generate any code for the base
            # the method reference alone gives us enough information
            pass

        # copy over the rest of arguments
        for a in self.arguments:
            pass_a = arg_gen.next()
            arg_t = a.get_value_register()
            out.append([f"move {pass_a}, {arg_t}", f"# {pass_a} = {arg_t}"])

        # we now need to call the method
        method_l = self.method.get_label()
        out.append(f"call {method_l}")

        # methods can return stuff in $a0, so we need to store it before restoring

        # NOTE: as mentioned earlier, we used more temporaries to compute the arguments before calling the procedure
        #   after the procedure call, those temporaries are obsolutely useless, so we can rest the generator to reuse them
        GlobalTemporaryRegisterGenerator.reset(seed)
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        if self.method.return_type == BuiltInTypeRecordCollection.VOID:
            # if the method returns void, then we don't need to expect anything inside $a0
            # we will just use a default 0 value
            out.append([f"move_immed_i {out_t}, 0", f"# {out_t} = 0"])
        else:
            # the method returns non-void and we need to capture that
            out.append([f"move {out_t}, a0", f"# {out_t} = a0"])

        # we now to restore all registers that were previously active before procedure call
        # NOTE: the registers need to be restored in reverse because they were pushed onto the stack
        for reg in reversed(saved_regs):
            out.append(f"restore {reg}")

        return out

    def __repr__(self):
        args = ", ".join(map(repr, self.arguments))
        return ", ".join(
            [
                f"Method-call({self.base}",
                f"{self.name}",
                f"[{args}])",
            ]
        )


class NewObjectExpressionRecord(ExpressionRecord):
    def __init__(
        self,
        location: ExprRange,
        class_name: str,
        arguments: List["ExpressionRecord"],
        containing_class: str,
    ):
        super().__init__(location, None)
        self.class_name = class_name
        self.arguments = arguments
        self.containing_class = containing_class

        # set this during type resolving
        self.constructor: "ConstructorRecord" = None

    def compute_type(self, **context):
        rec = DependencyTree.get_class_record(self.class_name)
        if rec == None:
            raise Exception(
                f"cannot create a new object using an unseen class while parsing class `{self.containing_class}` at lines {self.location}"
            )

        if len(rec.constructors) < 1:
            raise Exception(
                f"the class `{rec.name}` has no constructors, but one is being used at lines {self.location}"
            )

        # due to A04 constrainsts, there will always be <= 1 constructor
        cons = rec.constructors[0]
        if (
            cons.visibility == "private"
            and cons.containing_class != self.containing_class
        ):
            raise Exception(
                f"found constructor, but it is private and is being used outside its class at lines {self.location}"
            )

        if len(cons.parameters) != len(self.arguments):
            raise Exception(
                f"found constructor, but it expects {len(cons.parameters)} arguments instead of {len(self.arguments)} at lines {self.location}"
            )

        for i, (p, a) in enumerate(zip(cons.parameters, self.arguments)):
            a_type = a.resolve_type(**context)
            if not DependencyTree.is_subtype(a_type, p.type):
                raise Exception(
                    f"found constructor, but the argument at index {i} is incompatible at lines {a.location}"
                )

        self.constructor = cons
        return UserTypeRecord(self.class_name)

    def generate_code(self, **context):
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t

        class_rec = DependencyTree.get_class_record(self.constructor.containing_class)
        if class_rec == None:
            raise Exception(
                f"illegal program state - expected class record for `{self.constructor.containing_class}` to be defined"
            )

        # generate code for allocating space for new object
        out = [f"halloc {out_t}, {class_rec.size}"]

        # NOTE: before we start evaluating the expressions
        #   we need to understand that the registers created after this point does not need to be saved
        #       this is because they will be copied to a0 ... a_m where m is the number of arguments needed for calling the method
        #   for this reason, we can reset the temporary generator to the point BEFORE the procedure call
        #       so that we can re-use all those temporary registers used while evaluating expressions AFTER procedure call
        seed = GlobalTemporaryRegisterGenerator.get_curr()

        # from type checking, we already know that each argument is a subtype of its corresponding parameter
        # thus, we need to handle casting of ints to floats, if necessary
        # everything else does not need casting
        for p, a in zip(self.constructor.parameters, self.arguments):
            out.append(a.generate_code(**context))
            if (
                p.type == BuiltInTypeRecordCollection.FLOAT
                and a.type == BuiltInTypeRecordCollection.INT
            ):
                arg_t = a.get_value_register()
                out.append(f"itof {arg_t}, {arg_t}")

        # we now have the base address and every argument computed and casted
        saved_regs: List[str] = []

        a_needed = (
            len(self.constructor.parameters) + 1
        )  # +1 for the base address in $a0
        arg_gen = ArgumentRegisterGenerator()
        while a_needed > 0:
            arg_a = arg_gen.next()
            saved_regs.append(arg_a)
            out.append(f"save {arg_a}")
            a_needed -= 1

        # we now need to save all temporary registers that have been used
        t_needed = seed
        temp_gen = TemporaryRegisterGenerator()
        while t_needed > 0:
            temp_t = temp_gen.next()
            saved_regs.append(temp_t)
            out.append(f"save {temp_t}")
            t_needed -= 1

        # we now need to transfer the contents of the relevant registers into argument registers
        # we use our own generator because we need to start at a0
        #   we also don't want to mark these as active registers
        arg_gen = ArgumentRegisterGenerator()

        # copy over base address into $a0
        base_t = arg_gen.next()
        out.append([f"move {base_t}, {out_t}", f"# {base_t} = {out_t}"])

        # copy over the rest of arguments
        for a in self.arguments:
            pass_t = arg_gen.next()
            arg_t = a.get_value_register()
            out.append([f"move {pass_t}, {arg_t}", f"# {pass_t} = {arg_t}"])

        # we now need to call the constructor
        con_l = self.constructor.get_label()
        out.append(f"call {con_l}")

        # NOTE: as mentioned earlier, we used more temporaries to compute the arguments before calling the procedure
        #   after the procedure call, those temporaries are obsolutely useless, so we can rest the generator to reuse them
        GlobalTemporaryRegisterGenerator.reset(seed)

        # we don't expect anything to return from the constructor so we just restore the registers
        # NOTE: the registers need to be restored in reverse because they were pushed onto the stack
        for reg in reversed(saved_regs):
            out.append(f"restore {reg}")

        return out

    def __repr__(self):
        args = ", ".join(map(repr, self.arguments))
        return ", ".join(
            [
                f"New-object({self.class_name}",
                f"[{args}])",
            ]
        )


class ThisExpressionRecord(ExpressionRecord):
    def __init__(self, location: ExprRange, containing_class: str):
        super().__init__(location, UserTypeRecord(containing_class))

    def generate_code(self, **context):
        self_t: Optional[str] = context["self_t"]
        if self_t == None:
            raise Exception(
                "expected caller to provide a register that stores address of current object"
            )

        # even though we are just using the register passed through context
        #   we need to make sure that this register cannot be modified no matter what
        #   so we just make a copy
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t
        return [f"move {out_t}, {self_t}", f"# {out_t} = {self_t}"]

    def __repr__(self):
        return "This"


class SuperExpressionRecord(ExpressionRecord):
    def __init__(self, location: ExprRange, containing_class: str):
        # even though we know the current class name, we do not know if its super class record exists
        super().__init__(location, None)
        self.containing_class = containing_class

    def compute_type(self, **context):
        rec = DependencyTree.get_class_record(self.containing_class)
        if rec == None:
            raise Exception(
                "illegal program state: current class record should exist during type resolving"
            )

        if rec.super_class_name == None:
            raise Exception(
                f"cannot use super inside class `{self.containing_class}` because it doesn't extend anything at lines {self.location}"
            )

        rec = DependencyTree.get_class_record(rec.super_class_name)
        if rec == None:
            raise Exception(
                f"cannot use super inside class `{self.containing_class}` because its super class does not exist at lines {self.location}"
            )

        return UserTypeRecord(rec.name)

    def generate_code(self, **context):
        # NOTE: this is the same implementation as that of ThisExpressionRecord
        #   the reason is that the base object address being referred by "super" is no different from that of "this"
        #   the super is just here to help us identify what access level we have during type-checking

        self_t: Optional[str] = context["self_t"]
        if self_t == None:
            raise Exception(
                "expected caller to provide a register that stores address of current object"
            )

        # even though we are just using the register passed through context
        #   we need to make sure that this register cannot be modified no matter what
        #   so we just make a copy
        out_t = GlobalTemporaryRegisterGenerator.next()
        self.value_reg = out_t
        return [f"move {out_t}, {self_t}", f"# {out_t} = {self_t}"]

    def __repr__(self):
        return "Super"


class ClassReferenceExpressionRecord(ExpressionRecord):
    def __init__(self, location: ExprRange, class_name: str):
        # even though we have the name, we will use None
        # we want to resolve this name during type checking to ensure the name is a valid class name
        super().__init__(location, None)
        self.class_name = class_name

    def compute_type(self, **context):
        if DependencyTree.get_class_record(self.class_name) == None:
            raise Exception(
                f"cannot use class reference to `{self.class_name}` because it has not been seen by the parser at lines {self.location}"
            )
        return ClassLiteralTypeRecord(self.class_name)

    def generate_code(self, **context):
        # because this is a class reference, we don't need any code
        # we also don't need any registers
        # code that depend on this knows to use an offset from the $sap
        return []

    def __repr__(self):
        return f"Class-reference({self.class_name})"


class FieldRecord:
    id_gen = Counter(1)

    def __init__(
        self,
        name: str,
        visibility: Literal["public", "private"],
        applicability: Literal["static", "instance"],
        type: "TypeRecord",
        containing_class: str,
    ):
        self.name = name
        self.id = FieldRecord.id_gen.next()
        self.visibility = visibility
        self.applicability = applicability
        self.type = type
        self.containing_class = containing_class

        # this field contains the offset required to access this field
        # if the field is static, then it is simply an offset from the base $sap
        # if the field is instance, then it is an offset from base address of the object record
        # -- this means it takes into consideration of the # slots needed for super & super... classes
        self.offset: int = None

    def __repr__(self):
        return ", ".join(
            [
                f"FIELD {self.id}",
                f"{self.name}",
                f"{self.containing_class}",
                f"{self.visibility}",
                f"{self.applicability}",
                f"{self.type}",
            ]
        )


class MethodRecord:
    id_gen = Counter(1)

    def __init__(
        self,
        name: str,
        visibility: Literal["public", "private"],
        applicability: Literal["static", "instance"],
        parameters: List["VariableRecord"],
        return_type: "TypeRecord",
        body: "StatementRecord",
        variable_table: List["VariableRecord"],
        containing_class: str,
    ):
        self.name = name
        self.id = MethodRecord.id_gen.next()
        self.visibility = visibility
        self.applicability = applicability
        self.parameters = parameters
        self.return_type = return_type
        self.body = body
        self.variable_table = variable_table
        self.containing_class = containing_class

    def get_label(self) -> str:
        return f"M_{self.name}_{self.id}"

    def generate_code(self, **context) -> "NestedStrList":
        # we need fresh pool of registers
        GlobalTemporaryRegisterGenerator.reset()

        self_l = self.get_label()

        arg_gen = ArgumentRegisterGenerator()

        # this will store the register for the current object reference if any
        this_a: Optional[str] = None

        if self.applicability == "instance":
            this_a = arg_gen.next()

        # assign the parameters with argument registers
        for v in self.parameters:
            if v.value_reg != None:
                raise Exception("argument somehow got assigned with register already")
            v.value_reg = arg_gen.next()

        # we dont use **{**context, ...} because it is not expected for self_t to be specified in context already
        #   this_a may be None, but that's ok because static methods will not complain
        body_code = self.body.generate_code(**context, self_t=this_a)

        # NOTE: A05 constraints state that methods will always have a return
        #   so we do not need to add a safety ret at the end
        return [
            f"{self_l}:",
            body_code,
        ]

    def __repr__(self):
        header = ", ".join(
            [
                str(self.id),
                f"{self.name}",
                f"{self.containing_class}",
                f"{self.visibility}",
                f"{self.applicability}",
                repr(self.return_type),
            ]
        )
        params = ", ".join(map(lambda p: str(p.id), self.parameters))
        return "\n".join(
            [
                f"METHOD: {header}",
                f"Method Parameters: {params}",
                f"Variable Table:",
                *map(lambda v: v.get_table_details(), self.variable_table),
                f"Method Body:",
                f"{self.body}",
            ]
        )


StmtRange = Tuple[int, int]


class StatementRecord:
    def __init__(self, location: StmtRange):
        self.location = location

        # by default, assume the statement is type correct
        # overwrite this field if there is a different way of determining type_correct
        self.type_correct = True
        self.resolved_correctness = False

    def compute_type_correct(self, **context) -> bool:
        """
        Override this method to compute your own type correctness.
        """
        raise Exception("not implemented")

    def resolve_type_correct(self, **context) -> bool:
        if self.resolved_correctness:
            return self.type_correct

        self.type_correct = self.compute_type_correct(**context)
        self.resolved_correctness = True
        return self.type_correct

    def generate_code(self, **context) -> "NestedStrList":
        # subclasses need to implement this to support code generation
        raise Exception("not implemented")

    def __repr__(self):
        # purposely added here because sub-classes are supposed to implement this
        raise Exception("Not implemented")


class IfStatementRecord(StatementRecord):
    def __init__(
        self,
        location: StmtRange,
        if_expr: "ExpressionRecord",
        then_stmt: "StatementRecord",
        else_stmt: Optional["StatementRecord"],
    ):
        super().__init__(location)
        self.if_expr = if_expr
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    def compute_type_correct(self, **context):
        if self.if_expr.resolve_type(**context) != BuiltInTypeRecordCollection.BOOLEAN:
            raise Exception(
                f"expected the if-statement condition to be a boolean at lines {self.if_expr.location}"
            )

        if self.then_stmt.resolve_type_correct(**context):
            if self.else_stmt == None:
                return True
            return self.else_stmt.resolve_type_correct(**context)
        return False

    def generate_code(self, **context):
        condition_code = self.if_expr.generate_code(**context)
        condition_t = self.if_expr.get_value_register()

        end_l = LabelGenerator.next()

        then_code = self.then_stmt.generate_code(**context)

        if self.else_stmt == None:
            return [
                condition_code,
                f"bz {condition_t}, {end_l}",
                then_code,
                f"{end_l}:",
            ]

        # handle the case where there is an else statement
        else_code = self.then_stmt.generate_code(**context)
        else_l = LabelGenerator.next()

        return [
            condition_code,
            f"bz {condition_t}, {else_l}",
            then_code,
            f"jmp {end_l}",
            f"{else_l}:",
            else_code,
            f"{end_l}:",
        ]

    def __repr__(self):
        if self.else_stmt != None:
            return f"If( {self.if_expr}, {self.then_stmt}, {self.else_stmt} )"
        return f"If( {self.if_expr}, {self.then_stmt} )"


class WhileStatementRecord(StatementRecord):
    def __init__(
        self,
        location: StmtRange,
        while_condition: "ExpressionRecord",
        while_body: "StatementRecord",
    ):
        super().__init__(location)
        self.while_condition = while_condition
        self.while_body = while_body

    def compute_type_correct(self, **context):
        if (
            self.while_condition.resolve_type(**context)
            != BuiltInTypeRecordCollection.BOOLEAN
        ):
            raise Exception(
                f"expected the while-statement condition to be a boolean at lines {self.while_condition.location}"
            )
        return self.while_body.resolve_type_correct(**context)

    def generate_code(self, **context):
        condition_code = self.while_condition.generate_code(**context)
        condition_t = self.while_condition.get_value_register()

        loop_test_l = LabelGenerator.next()
        loop_end_l = LabelGenerator.next()

        body_code = self.while_body.generate_code(
            **{**context, "loop_test_l": loop_test_l, "loop_end_l": loop_end_l}
        )

        return [
            f"{loop_test_l}:",
            condition_code,
            f"bz {condition_t}, {loop_end_l}",
            body_code,
            f"jmp {loop_test_l}",
            f"{loop_end_l}:",
        ]

    def __repr__(self):
        return f"While( {self.while_condition}, {self.while_body} )"


class ForStatementRecord(StatementRecord):
    def __init__(
        self,
        location: StmtRange,
        init_expr: "ExpressionRecord",
        loop_condition: "ExpressionRecord",
        update_expr: "ExpressionRecord",
        loop_body: "StatementRecord",
    ):
        super().__init__(location)
        self.init_expr = init_expr
        self.loop_condition = loop_condition
        self.update_expr = update_expr
        self.loop_body = loop_body

    def compute_type_correct(self, **context):
        if (
            self.loop_condition.resolve_type(**context)
            != BuiltInTypeRecordCollection.BOOLEAN
        ):
            raise Exception(
                f"expected the for-statement condition to be a boolean at lines {self.loop_condition.location}"
            )

        self.init_expr.resolve_type(**context)
        self.update_expr.resolve_type(**context)
        return self.loop_body.resolve_type_correct(**context)

    def generate_code(self, **context):
        init_code = self.init_expr.generate_code(**context)

        condition_code = self.loop_condition.generate_code(**context)
        condition_t = self.loop_condition.get_value_register()

        loop_test_l = LabelGenerator.next()
        loop_end_l = LabelGenerator.next()

        body_code = self.loop_body.generate_code(
            **{**context, "loop_test_l": loop_test_l, "loop_end_l": loop_end_l}
        )

        update_code = self.update_expr.generate_code(**context)

        return [
            init_code,
            f"{loop_test_l}:",
            condition_code,
            f"bz {condition_t}, {loop_end_l}",
            body_code,
            update_code,
            f"jmp {loop_test_l}",
            f"{loop_end_l}:",
        ]

    def __repr__(self):
        return ", ".join(
            [
                f"For( {self.init_expr}",
                f"{self.loop_condition}",
                f"{self.update_expr}",
                f"{self.loop_body} )",
            ]
        )


class ReturnStatementRecord(StatementRecord):
    def __init__(self, location: StmtRange, return_value: Optional["ExpressionRecord"]):
        super().__init__(location)
        self.return_value = return_value

        # this needs to be set during type checking
        self.expected_return_type: "TypeRecord" = None

    def compute_type_correct(self, **context):
        method_type: Literal["method", "constructor"] = context["method_type"]
        if method_type == "constructor":
            raise Exception("return statement not expected inside constructor")

        expected_return_type: Optional["TypeRecord"] = context["method_return_type"]
        if expected_return_type == None:
            raise Exception("expected return type in context")
        self.expected_return_type = expected_return_type

        if self.return_value == None:
            # if the current return value is None, then the expected return type should be None
            if expected_return_type == BuiltInTypeRecordCollection.VOID:
                return True

            # otherwise, it is a problem
            raise Exception(
                f"expected the return-statement to return something non-void for a non-void method at lines {self.location}"
            )
        else:
            # if there is a non-void return value, then the expected return type should not be void
            if expected_return_type == BuiltInTypeRecordCollection.VOID:
                raise Exception(
                    f"expected the return-statement to return nothing for a void method at lines {self.location}"
                )
            # if the expected return type is not void, then we may be fine

        if not DependencyTree.is_subtype(
            self.return_value.resolve_type(**context), expected_return_type
        ):
            raise Exception(
                f"expected the return-statement to return a compatible subtype at lines {self.location}"
            )

        return True

    def generate_code(self, **context):
        # NOTE:
        # through type checking, we know that this return statement
        #   - is not inside a constructor
        #   - and it either returns void or a value

        # if the return value is None, then we can just call return
        if self.return_value == None:
            return ["ret"]

        # now we know that a value must be returned
        # through type checking, we already determined what the return type should be
        out = [self.return_value.generate_code(**context)]
        value_t = self.return_value.get_value_register()

        # NOTE: the return value is definitely a subtype of the expected return type
        #   so we need to do casting if necessary
        if (
            self.expected_return_type == BuiltInTypeRecordCollection.FLOAT
            and self.return_value.type == BuiltInTypeRecordCollection.INT
        ):
            out.append(f"itof {value_t}, {value_t}")

        return [out, f"move a0, {value_t}", f"# a0 = {value_t}", "ret"]

    def __repr__(self):
        return f"Return( {self.return_value} )"


class ExprStatementRecord(StatementRecord):
    def __init__(self, location: StmtRange, expr: "ExpressionRecord"):
        super().__init__(location)
        self.expr = expr

    def compute_type_correct(self, **context):
        self.expr.resolve_type(**context)
        return True

    def generate_code(self, **context):
        return self.expr.generate_code(**context)

    def __repr__(self):
        return f"Expr( {self.expr} )"


class BlockStatementRecord(StatementRecord):
    def __init__(self, location: StmtRange, stmt_seq: List["StatementRecord"]):
        super().__init__(location)
        self.stmt_seq = stmt_seq

    def compute_type_correct(self, **context):
        for stmt in self.stmt_seq:
            if not stmt.resolve_type_correct(**context):
                return False
        return True

    def generate_code(self, **context):
        return [stmt.generate_code(**context) for stmt in self.stmt_seq]

    def __repr__(self):
        if len(self.stmt_seq) < 1:
            return "Block([])"

        stmts = ", ".join(map(repr, self.stmt_seq))
        return "\n".join(["Block([", stmts, "])"])


class BreakStatementRecord(StatementRecord):
    def __init__(self, location: StmtRange):
        super().__init__(location)

    def compute_type_correct(self, **context):
        return True

    def generate_code(self, **context):
        loop_end_l = context["loop_end_l"]
        if loop_end_l == None:
            raise Exception("expected a label for loop_end to be passed")
        return [f"jmp {loop_end_l}"]

    def __repr__(self):
        return "Break"


class ContinueStatementRecord(StatementRecord):
    def __init__(self, location: StmtRange):
        super().__init__(location)

    def compute_type_correct(self, **context):
        return True

    def generate_code(self, **context):
        loop_test_l = context["loop_test_l"]
        if loop_test_l == None:
            raise Exception("expected a label for loop_post_test to be passed")
        return [f"jmp {loop_test_l}"]

    def __repr__(self):
        return "Continue"


class SkipStatementRecord(StatementRecord):
    def __init__(self, location: StmtRange):
        super().__init__(location)

    def compute_type_correct(self, **context):
        return True

    def generate_code(self, **context):
        # no code needed because this statement is meant to be skipped
        return []

    def __repr__(self):
        return "Skip"


class VariableDeclarationStatementRecord(StatementRecord):
    """
    this class does absolutely nothing, but helps us filter declarations from body during printing
    """

    def __init__(self, location: StmtRange, variables: List["VariableRecord"]):
        super().__init__(location)
        self.variables = variables

    def compute_type_correct(self, **context):
        return True

    def generate_code(self, **context):
        # NOTE:
        # unlike ast printing or type checking where nothing is done
        # in code generation, we actually do something

        # no code is actually needed but we need to assign registers to these variables
        #   this way, variable expressions that reference a variable has a register to look at
        # for v in self.variables:
        #     if v.value_reg != None:
        #         raise Exception("variable is already somehow assigned a register")
        #     v.value_reg = GlobalTemporaryRegisterGenerator.next()
        return []

    def __repr__(self):
        names = ", ".join([f"({v.name}, {v.id})" for v in self.variables])
        return f"VariableDecl({names})"


class VariableRecord:
    """
    Assigned: @BrianShao123
    """

    def __init__(
        self, type: "TypeRecord", variable_kind: Literal["formal", "local"], name: str
    ):
        self.name = name
        self.variable_kind = variable_kind
        self.type = type

        # this will be assigned by the MethodScope
        # because FieldRecords also use VariableRecord during parsing, but uses their own ID system
        self.id: int = None

        # this will hold the register that stores the value of this particular variable
        # this only be set during code generation inside the context of a function
        self.value_reg: str = None

    def get_table_details(self):
        return ", ".join(
            [f"VARIABLE {self.id}", self.name, self.variable_kind, repr(self.type)]
        )

    def __repr__(self):
        return f"Variable({self.id})"

    def get_value_register(self) -> str:
        if self.value_reg == None:
            # raise Exception(
            #     f"tried to get register for Var[id={self.id}, name={self.name}], but it is not set"
            # )
            self.value_reg = GlobalTemporaryRegisterGenerator.next()
        return self.value_reg
