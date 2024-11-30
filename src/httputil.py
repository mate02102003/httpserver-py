import warnings

from functools import wraps

def optional(cls: object | None = None):
    @wraps(cls)
    def wrap(*args, **kwds):
        warnings.warn(f"{cls.__qualname__} is optional", OptionalWarning, stacklevel=2)

        return cls

    return wrap

class OptionalWarning(UserWarning):
    pass