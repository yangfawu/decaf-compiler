from typing import Optional
from decaf_ast import VariableRecord


class Scope:
    def __init__(
        self,
        parent_scope: Optional["Scope"] = None,
        share_table_with_child: bool = False,
        block_child: bool = False,
        class_name: Optional[str] = None,
    ):
        """
        Args:
            parent_scope (Scope, optional):
                The parent scope of this scope.
                Defaults to None.
            share_table_with_child (bool, optional):
                Set to True if direct child scopes use this scope's table instead of their own.
                Defaults to False.
            block_child (bool, optional):
                Set to True if child scopes cannot search for symbol in and preceding this scope.
                Defaults to False.
            class_name (str, optional):
                Provide non-null class name that this scope and all sub-scopes will use to determine what class they are inside.
                If kept as None, will use parent scope's class name if there is a parent
        """
        self.parent = parent_scope

        if share_table_with_child and block_child:
            raise Exception("scope cannot share table with child and block them")
        self.share_table_with_child = share_table_with_child
        self.block_child = block_child

        if parent_scope:
            self.symbol_table = (
                {}
                if not parent_scope.share_table_with_child
                else parent_scope.symbol_table
            )
            self.variable_table = parent_scope.variable_table
        else:
            self.symbol_table = {}
            self.variable_table = []

        if class_name:
            self.class_name = class_name
        else:
            if parent_scope:
                self.class_name = parent_scope.class_name
            else:
                self.class_name = None

    def add_symbol(self, ref: "VariableRecord") -> bool:
        """Adds symbol to table if the symbol does not already exists.

        Args:
            ref (`VariableRecord`): the reference to the symbol

        Returns:
            bool: True if symbol was added; False if otherwise
        """
        if ref.name in self.symbol_table:
            return False

        self.symbol_table[ref.name] = ref
        ref.id = len(self.variable_table) + 1
        self.variable_table.append(ref)
        return True

    def lookup_symbol(self, name: str) -> Optional["VariableRecord"]:
        """Looks up symbol in current scope with the name.
        Will search parent and ancestor scopes if symbol does not exist.

        Args:
            name (str): the name of the symbol

        Returns:
            (`VariableRecord`, optional): the reference of the symbol if found; None if otherwise
        """
        if name in self.symbol_table:
            return self.symbol_table[name]
        if self.parent and not self.parent.block_child:
            return self.parent.lookup_symbol(name)
        return None

    current: "Scope" = None

    @staticmethod
    def enter_new_scope(
        share_table_with_child=False,
        block_child=False,
        class_name=None,
    ):
        """
        Args:
            share_table_with_child (bool, optional):
                Set to True if direct child scopes use this scope's table instead of their own.
                Defaults to False.
            block_child (bool, optional):
                Set to True if child scopes cannot search for symbol in and preceding this scope.
                Defaults to False.
            class_name (str, optional):
                Provide non-null class name that this scope and all sub-scopes will use to determine what class they are inside.
                If kept as None, will use parent scope's class name if there is a parent
        """
        Scope.current = Scope(
            parent_scope=Scope.current,
            share_table_with_child=share_table_with_child,
            block_child=block_child,
            class_name=class_name,
        )

    @staticmethod
    def exit_scope():
        if not Scope.current:
            return
        Scope.current = Scope.current.parent
