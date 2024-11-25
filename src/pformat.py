"""
Pretty format

This module serves as pretty formatter for the built-in classes in python
"""

from types import FunctionType, MethodType

def pformat_int(__int: int) -> str:
    return f"{__int:_}"

def pformat_complex(__complex: complex) -> str:
    return f"{__complex.real} {"+" if __complex.imag >= 0 else "-"} {abs(__complex.imag)}i"

def pformat_tuple(__tuple: tuple, indent: int = 0) -> str:
    acc = "(\n"
    for value in __tuple:
            acc += f"{" " * indent} {pformat(value, indent + 3)}\n"
    acc += " " * indent + ")"
    return acc

def pformat_list(__list: list, indent: int = 0) -> str:
    acc = "[\n"
    for value in __list:
            acc += f"{" " * indent} {pformat(value, indent + 3)}\n"
    acc += " " * indent + "]"
    return acc

def pformat_set(__set: set, indent: int = 0) -> str:
    acc = "{\n"
    for value in __set:
            acc += f"{" " * indent} {pformat(value, indent + 3)}\n"
    acc += " " * indent + "}"

def pformat_frozenset(__fset: frozenset, indent: int = 0) -> str:
    acc = "frozenset{\n"
    for value in __fset:
            acc += f"{" " * indent} {pformat(value, indent + 3)}\n"
    acc += " " * indent + "}"
    return acc

def pformat_dict(__dict: dict, indent: int = 0) -> str:
    acc = "{\n"
    for key in __dict:
            acc += f"{" " * indent} {key}: {pformat(__dict[key], indent + 3)}\n"
    acc += " " * indent + "}"
    return acc

def pformat(__obj: object, indent: int = 0) -> str:
    o_type = type(__obj)

    formated = None
    if issubclass(o_type, int):
        return pformat_int(__obj)
    if issubclass(o_type, complex):
        return pformat_complex(__obj)
    if issubclass(o_type, tuple):
        formated = pformat_tuple(__obj, indent)
    elif issubclass(o_type, list):
        formated = pformat_list(__obj, indent)
    elif issubclass(o_type, set):
        formated = pformat_set(__obj, indent)
    elif issubclass(o_type, frozenset):
        formated = pformat_frozenset(__obj, indent)
    elif issubclass(o_type, dict):
        formated = pformat_dict(__obj, indent)
    
    if formated is None:
        return repr(__obj)
    
    if len(formated) < 32:
        formated = formated.replace(" ", "")
        formated_slices = formated.split("\n")
        formated = formated_slices[0] + ", ".join(formated_slices[1:-1]) + formated_slices[-1]
    
    return formated

    
class PP_Repr:
    format_join = "\n"
    format_func = staticmethod(pformat)
    format_indent = 4
    
    def __repr__(self) -> str:
        class_name = self.__class__.__name__

        indent = " " * self.format_indent
        formated_attrs = self.format_join.join(
             indent + f"{attr}: {self.format_func(getattr(self, attr), self.format_indent)}"
             for attr in dir(self) \
                if not attr.startswith("_") \
                    and getattr(PP_Repr, attr, None) is None \
                    and not isinstance(getattr(self, attr), (FunctionType, MethodType))
        )

        return f"{class_name}(\n{formated_attrs}\n{" " * (self.format_indent - 4)})"
    