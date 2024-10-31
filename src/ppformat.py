def ppformat_tuple(__tuple: tuple, indent: int = 0) -> str:
    acc = "(\n"
    for value in __tuple:
            acc += f"{" " * indent} {ppformat(__tuple[value], indent + len(str(value)) + 3)}\n"
    acc += " " * indent + ")"
    return acc

def ppformat_dict(__dict: dict, indent: int = 0) -> str:
    acc = "{\n"
    for key in __dict:
            acc += f"{" " * indent} {key}: {ppformat(__dict[key], indent + len(str(key)) + 3)}\n"
    acc += " " * indent + "}"
    return acc

def ppformat(__obj: object, indent: int = 0) -> str:
    o_type = type(__obj)

    if issubclass(o_type, tuple):
        return ppformat_tuple(__obj, indent)
    if issubclass(o_type, dict):
        return ppformat_dict(__obj, indent)
    return repr(__obj)
    
class PP_Repr:
    format_join = "\n"
    format_func = staticmethod(ppformat)
    format_indent = 4
    
    def __repr__(self) -> str:
        class_name = self.__class__.__name__

        indent = " " * self.format_indent
        formated_attrs = self.format_join.join(
             f"{indent}{attr}: {self.format_func(getattr(self, attr),self.format_indent)}"
             for attr in dir(self) if not attr.startswith("_") and getattr(PP_Repr, attr, None) is None
        )

        return f"{class_name}(\n{formated_attrs}\n{" " * (self.format_indent - 4)})"
    