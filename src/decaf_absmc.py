from typing import Optional
from decaf_config import CODEGEN_DEBUG
from decaf_util import Counter, NestedStrList


class RegisterGenerator(Counter):
    def __init__(self, prefix: str):
        super().__init__(0)
        self.prefix = prefix

    def next(self) -> str:
        i = super().next()
        return f"{self.prefix}{i}"


class ArgumentRegisterGenerator(RegisterGenerator):
    def __init__(self):
        super().__init__("a")


class TemporaryRegisterGenerator(RegisterGenerator):
    def __init__(self):
        super().__init__("t")


class LabelGenerator:
    gen = RegisterGenerator("L")

    @staticmethod
    def next() -> str:
        """
        Generates an unique label that has not been used in the program yet
        """
        return LabelGenerator.gen.next()

    @staticmethod
    def reset():
        """
        Resets the generator to re-generate temporary registers starting at L0
        NOTE: Do not use this at all cost.
        """
        LabelGenerator.gen.reset()


class GlobalTemporaryRegisterGenerator:
    temp_gen = TemporaryRegisterGenerator()

    @staticmethod
    def next() -> str:
        """
        Generates a new temporary register that has not been used.
        NOTE: The generated register may be used by other parts of the program.
            It is up to the programmer to ensure that the generator is only reset for specific purposes.
        """
        return GlobalTemporaryRegisterGenerator.temp_gen.next()

    @staticmethod
    def reset(new_start: Optional[int] = None):
        """
        Resets all internal generators so that the next temporary and argument registers are t0 and a0.
        """
        GlobalTemporaryRegisterGenerator.temp_gen.reset(new_start)

    @staticmethod
    def get_curr() -> int:
        return GlobalTemporaryRegisterGenerator.temp_gen.curr


def print_code(code: "NestedStrList", file):
    """
    When we generate code, the DS we use ends up looking like lists within lists within lists.
    To output this to a file, we need a DFS crawler to ensure every list is covered.
    """
    for sub_code in code:
        if isinstance(sub_code, str):
            if (
                sub_code.endswith(":")
                or sub_code.startswith(".")
            ):
                print(sub_code, file=file)
            else:
                if sub_code.startswith("#") and not CODEGEN_DEBUG:
                    continue
                print(f"\t{sub_code}", file=file)
                if sub_code.startswith("#"):
                    print(file=file)
        else:
            print_code(sub_code, file)
