from check50 import Failure, Missing, Mismatch
import ast

def check50_assert(cond, src, msg_or_exc=None):
    """
    Asserts a conditional statement. If the condition evaluates to True, 
    nothing happens. Otherwise, it will look for a message or exception that
    follows the condition (seperated by a comma). If the msg_or_exc is not
    a string, an exception, or not provided, then the additional argument is
    silently ignored, raising a check50.Failure. 

    Used for rewriting check files.

    Example usage:
    ```
    assert x in y, check50.Missing(x, y)
    ```
    will be converted to
    ```
    check50_assert(x in y, "x in y", check50.Missing(x, y))
    ```

    :param cond: The conditional statement.
    :type cond: bool
    :param src: The source code string of the conditional expression \
                (e.g., 'x in y'), extracted from the AST.
    :type src: str
    :param msg_or_exc: The message or exception following the conditional in \
                        the assertion statement.
    :type msg_or_exc: str, BaseException, optional

    :raises check50.Failure: if msg_or_exc is a string, if msg_or_exc is not 
                             included, or if both msg_or_exc is not a string and
                             not an exception
    :raises msg_or_exc: if msg_or_exc is an exception
    """
    if cond:
        return
    
    if isinstance(msg_or_exc, str):
        raise Failure(msg_or_exc)
    elif isinstance(msg_or_exc, BaseException):
        raise msg_or_exc
    else:
        raise Failure(f"Assertion failure: {src}")