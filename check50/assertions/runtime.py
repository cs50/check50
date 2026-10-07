from check50 import Failure, Missing, Mismatch
import inspect
import tokenize
import types, builtins
from io import StringIO
import ast
from dataclasses import dataclass
from collections import defaultdict

@dataclass(frozen=True)
class TokenSeq:
    kind: int                      # e.g. OP, NAME, STRING
    text: str                      # e.g. 'foo', '(', ')'

@dataclass(frozen=True)
class KeyPattern:
    string: str                    # key's string representation
    tokens: tuple[TokenSeq, ...]   # normalized token sequence

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
        Exceptions from the `check50` library are preferred, since they will be
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
    if context is None:
        context = {}

    # Grab the global and local variables as of now
    caller_frame = inspect.currentframe().f_back
    caller_globals = caller_frame.f_globals
    caller_locals = caller_frame.f_locals

    # Build the list of candidate keys
    candidate_keys = list(context.keys()) if context else []

    # Plan substitutions and learn which keys are actually used
    eval_src, key_to_placeholder = substitute_expressions(src, candidate_keys)

    # Only evaluate the keys that were actually matched
    evaluated = {}
    for expr_str in key_to_placeholder.keys():
        try:
            evaluated[expr_str] = eval(expr_str, caller_globals, caller_locals)
        except Exception as e:
            evaluated[expr_str] = f"[error evaluating: {e}]"

    # Build the eval_context for placeholders
    eval_context = {
        placeholder: evaluated[key]
        for key, placeholder in key_to_placeholder.items()
    }

    # Merge locals and globals with expression context for evaluation
    eval_globals = caller_globals.copy(); eval_globals.update(eval_context)
    eval_locals  = caller_locals.copy();  eval_locals.update(eval_context)
    cond = eval(eval_src, eval_globals, eval_locals)

    # Finally, quit if the condition evaluated to True.
    if cond:
        return

    # Filter out modules, functions, and built-ins, which is needed to avoid
    # overwriting function definitions in evaluaton and avoid useless string
    # output
    def is_irrelevant_value(v):
        return isinstance(v, (
            types.ModuleType,
            types.FunctionType,
            types.BuiltinFunctionType
        ))
    def is_builtin_name(name):
        name = name.split("(")[0] # grab `len` from `len(...)`
        return name in dir(builtins)

    filtered_context = {
        k: v for k, v in evaluated.items()
        if not is_irrelevant_value(v) and not is_builtin_name(k)
    }

    # Produces a string like "var1 = ..., var2 = ..., foo() = ..."
    context_str = ", ".join(f"{k} = {repr(v)}" for k, v in filtered_context.items()) or None

    # If `right` or `left` were evaluatable objects, their actual
    # value will be stored in `evaluated`.
    if right in evaluated:
        right = evaluated[right]
    if left in evaluated:
        left = evaluated[left]

    # Raise check50-specific/user-passed exceptions.
    if isinstance(msg_or_exc, str):
        raise Failure(msg_or_exc)
    elif isinstance(msg_or_exc, BaseException):
        raise msg_or_exc
    elif cond_type == 'eq' and left is not None and right is not None:
        help_msg = f"checked: {src}"
        help_msg += f"\n    where {context_str}" if context_str else ""
        raise Mismatch(right, left, help=help_msg)
    elif cond_type == 'in' and left is not None and right is not None:
        help_msg = f"checked: {src}"
        help_msg += f"\n    where {context_str}" if context_str else ""
        raise Missing(left, right, help=help_msg)
    else:
        help_msg = f"\n    where {context_str}" if context_str else ""
        raise Failure(f"check did not pass: {src}" + help_msg)

def _tokenize_normalized(code: str):
    """
    Tokenize and normalize:
      - drop ENCODING, NL, NEWLINE, INDENT, DEDENT, ENDMARKER
      - for STRING tokens, normalize to their Python value (so "'pwd'" == "\"pwd\"")
      - return both normalized tokens and the original raw tokens (1:1 positions)

    Outputs a normalized and raw tokenization (raw, excluding dropped) of the
    code.

    For instance, the code input "foo.bar()" might output a `norm` of `TokenSeq`s:
    ```
    [
        TokenSeq(NAME, "foo"), TokenSeq(OP, "."), TokenSeq(NAME, "bar"),
        TokenSeq(OP, "("), TokenSeq(OP, ")")
    ]
    ```
    In this case, there were no strings to normalize, so `raw` would
    output the same thing.
    """
    drop = {
        tokenize.ENCODING, tokenize.NL, tokenize.NEWLINE,
        tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER
    }

    norm, raw = [], []
    for tok in tokenize.generate_tokens(StringIO(code).readline):
        # Extract type and string representation from token
        tok_type, tok_string, *_ = tok

        # Ignore certain encoding types
        if tok_type in drop:
            continue

        raw.append(TokenSeq(tok_type, tok_string))

        # Normalize STRING tokens to their Python value
        if tok_type == tokenize.STRING:
            try:
                val = ast.literal_eval(tok_string)
                norm.append(TokenSeq(tok_type, repr(val)))
            except Exception:
                norm.append(TokenSeq(tok_type, tok_string))
        else:
            norm.append(TokenSeq(tok_type, tok_string))

    return norm, raw


def substitute_expressions(src: str, keys: list[str]) -> tuple[str, dict]:
    """
    Rewrites `src` by replacing known `keys` (from `context`) with a placeholder
    variable name, and builds a new context dict where those names map to
    pre-evaluated values.

    For instance, let `src` be the string representation of
    ```
    assert check50.run("./foo.c").stdout() == "OK"
    ```
    The `keys` might look like
    ```
    ["check50.run("./foo.c")", "check50.run("./foo.c").stdout()"]
    ```
    We would want to find the longest match from these keys and output:
    ```
    expr_str:           assert __expr0 == "OK"
    key_to_placeholder: { "check50.run("./foo.c").stdout()": "__expr0" }
    ```
    """
    # Tokenize/normalize the source once
    src_norm, src_raw = _tokenize_normalized(src)

    # Store a list of KeyPatterns
    patterns = []
    for key in keys:
        key_norm, _ = _tokenize_normalized(key)
        if key_norm:
            patterns.append(KeyPattern(key, tuple(key_norm)))

    # Stores a TokenSeq and every KeyPattern that starts with that TokenSeq
    patterns_by_start_token = defaultdict(list)
    for pattern in patterns:
        start_token = pattern.tokens[0]
        patterns_by_start_token[start_token].append(pattern)

    # Prefer longest matches first (e.g. foo.bar.baz() is preferred over foo.bar)
    for candidates in patterns_by_start_token.values():
        candidates.sort(key=lambda p: len(p.tokens), reverse=True)

    key_to_placeholder = {}
    def get_placeholder(key_str):
        """Return a placeholder `__expr{i}` for a given key."""
        if key_str not in key_to_placeholder:
            key_to_placeholder[key_str] = f"__expr{len(key_to_placeholder)}"
        return key_to_placeholder[key_str]

    def longest_match_at(i):
        """Return the longest KeyPattern that matches `src_norm` starting at `i`"""
        if i >= len(src_norm):
            return None

        candidates = patterns_by_start_token.get(src_norm[i], [])

        # Iterate through the possible candidates for the longest match
        for pattern in candidates:
            L = len(pattern.tokens)

            # Skip if i + L would run past the end and then check for match
            if i + L <= len(src_norm) and tuple(src_norm[i:i+L]) == pattern.tokens:
                return pattern

        # No match
        return None

    output = []
    i = 0
    while i < len(src_norm):
        # Find a longest pattern, if exists
        pattern = longest_match_at(i)
        if pattern is not None:
            # Create a placeholder var for this specific match
            placeholder = get_placeholder(pattern.string)
            output.append((tokenize.NAME, placeholder))
            # Move forward by the number of tokens in this pattern
            i += len(pattern.tokens)
        else:
            # Preserve original lex for unmatched regions
            token = src_raw[i]
            output.append((token.kind, token.text))
            # Move forward by 1 token
            i += 1

    eval_src = tokenize.untokenize(output)
    return eval_src, key_to_placeholder
