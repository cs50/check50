from check50 import Failure, Missing, Mismatch

def check50_assert(src, msg_or_exc=None, cond_type="unknown", left=None, right=None, context=None):
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

    :param src: The source code string of the conditional expression \
                (e.g., 'x in y'), extracted from the AST.
    :type src: str
    :param msg_or_exc: The message or exception following the conditional in \
                       the assertion statement.
    :type msg_or_exc: str | BaseException | None
    :param cond_type: The type of conditional, one of {"eq", "in", "unknown"}
    :type cond_type: str
    :param left: The left side of the conditional, if applicable
    :type left: str | None
    :param right: The right side of the conditional, if applicable
    :type right: str | None
    :param context: A collection of the conditional's variable names as keys.
    :type context: dict

    :raises msg_or_exc: If msg_or_exc is an exception.
    :raises check50.Mismatch: If no exception is provided and cond_type is "eq".
    :raises check50.Missing: If no exception is provided and cond_type is "in".
    :raises check50.Failure: If msg_or_exc is a string, or if cond_type is \
                             unrecognized.
    """
    # Evaluate all variables and functions within the context dict and generate
    # a string of these values
    context_str = None
    if context or (left and right):
        import inspect
        for expr_str in context:
            try:
                # Grab the global and local variables as of now
                caller_frame = inspect.currentframe().f_back
                context[expr_str] = eval(expr_str, caller_frame.f_globals, caller_frame.f_locals)
            except Exception as e:
                context[expr_str] = f"[error evaluating: {e}]"

        # produces a string like "var1 = ..., var2 = ..., foo() = ..."
        context_str = ", ".join(f"{k} = {repr(v)}" for k, v in (context or {}).items())

    # Since we've memoized the functions and variables once, now try and
    # evaluate the conditional by substituting the function calls/vars with
    # their results
    eval_src, eval_context = substitute_expressions(src, context)
    cond = eval(eval_src, {}, eval_context)

    # Finally, quit if the condition evaluated to True.
    if cond:
        return

    # If `right` or `left` were evaluatable objects, their actual value will be stored in `context`.
    # Otherwise, they're still just literals.
    right = context.get(right) or right
    left  = context.get(left) or left

    # Since the condition didn't evaluate to True, now, we can raise special
    # exceptions.
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
        raise Failure(f"check did not pass: {src} {context}" + help_msg)

def substitute_expressions(src: str, context: dict) -> tuple[str, dict]:
    """
    Rewrites `src` by replacing each key in `context` with a placeholder variable name,
    and builds a new context dict where those names map to pre-evaluated values.

    For instance, given a `src`:
    ```
    check50.run('pwd').stdout() == actual
    ```
    it will create a new `eval_src` as
    ```
    __expr0 == __expr1
    ```
    and use the given context to define these variables:
    ```
    eval_context = {
        '__expr0': context['check50.run('pwd').stdout()'],
        '__expr1': context['actual']
    }
    ```
    """
    new_src = src
    new_context = {}

    for i, expr in enumerate(sorted(context.keys(), key=len, reverse=True)):
        placeholder = f"__expr{i}"
        new_src = new_src.replace(expr, placeholder)
        new_context[placeholder] = context[expr]

    return new_src, new_context
