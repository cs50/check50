from check50 import Failure, Missing, Mismatch

def check50_assert(cond, src, msg_or_exc=None, cond_type="unknown", left=None, right=None, context=None):
    """
    Asserts a conditional statement. If the condition evaluates to True,
    nothing happens. Otherwise, it will look for a message or exception that
    follows the condition (seperated by a comma). If the msg_or_exc is not
    a string, an exception, or it was not provided, it is silently ignored.

    In such cases, we attempt to determine which exception should be raised
    based on the type of the conditional. If recognized, it raises either
    check50.Mismatch or check50.Missing. If the conditional type is unknown or
    unhandled, check50.Failure is raised with a default message.

    Used for rewriting assertion statements in check files.

    Note:
        Exceptions from the check50 library are preferred, since they will be
        handled gracefully and integrated into the check output. Native Python
        exceptions are technically supported, but check50 will immediately
        terminate on the user's end if the assertion fails.

    Example usage:
        ```
        assert x in y
        ```
        will be converted to
        ```
        check50_assert(x in y, "x in y", None, "in", x, y)
        ```

    :param cond: The evaluated conditional statement.
    :type cond: bool
    :param src: The source code string of the conditional expression \
                (e.g., 'x in y'), extracted from the AST.
    :type src: str
    :param msg_or_exc: The message or exception following the conditional in \
                       the assertion statement.
    :type msg_or_exc: str | BaseException | None
    :param cond_type: The type of conditional, one of {"eq", "in", "unknown"}
    :type cond_type: str
    :param left: The left side of the conditional, if applicable
    :type left: Any
    :param right: The right side of the conditional, if applicable
    :type right: Any
    :param context: A collection of the conditional's variable names and values.
    :type context: dict

    :raises msg_or_exc: If msg_or_exc is an exception.
    :raises check50.Mismatch: If no exception is provided and cond_type is "eq".
    :raises check50.Missing: If no exception is provided and cond_type is "in".
    :raises check50.Failure: If msg_or_exc is a string, or if cond_type is \
                             unrecognized.
    """
    if cond:
        return

    context_str = None
    if context and isinstance(context, dict):
        context_str = ", ".join(f"{k} = {repr(v)}" for k, v in (context or {}).items())

    if isinstance(msg_or_exc, str):
        raise Failure(msg_or_exc)
    elif isinstance(msg_or_exc, BaseException):
        raise msg_or_exc
    elif cond_type == 'eq' and left and right:
        help_msg = f"checked: {src}"
        help_msg += f"\n    where {context_str}" if context_str else ""
        raise Mismatch(right, left, help=help_msg)
    elif cond_type == 'in' and left and right:
        help_msg = f"checked: {src}"
        help_msg += f"\n    where {context_str}" if context_str else ""
        raise Missing(left, right, help=help_msg)
    else:
        help_msg = f"\n    where {context_str}" if context_str else ""
        raise Failure(f"check did not pass: {src}" + help_msg)
