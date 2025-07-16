from check50 import Failure, Missing, Mismatch
import ast

def check50_assert(cond: bool, src: str):
    """
    Asserts a conditional statement. If the condition evaluates to True, 
    nothing happens. Otherwise, the condition will raise a check50 exception. 
    Used in rewriting check files. Evaluates subconditions in order and raises 
    the first exception it sees. The specific exception raised depends on the
    type of conditional statement (see also `classify_ast`.)

    :param cond: The conditional statement.
    :type cond: bool
    :param src: The source code string of the conditional expression \
                (e.g., 'x in y'), extracted from the AST.
    :type src: str
    
    :raises check50.Missing, check50.Mismatch, or check50.Failure: if the condition fails
    """
    if cond:
        return

    expr = ast.parse(src, mode="eval").body
    exc  = classify_ast(expr) # the exception that should be raised
    raise exc(f"Assertion failed: {src}")
        
def classify_ast(expr):
    """
    Classifies an AST expression to return an exception based on the operator.

    For instance, if the expression was read as "x not in [1,2,3]", the
    function would return a check50.Missing error.

    :param expr: The AST expression.
    :type expr: ast.expr

    :raises check50.Missing: if the comparison operator is one of: \
                             (ast.In, ast.NotIn)
    :raises check50.Mismatch: if the comparison operator is one of: \
                              (ast.Eq, ast.NotEq, ast.Gt, ast.Lt, ast.GtE, \
                              ast.LtE)
    :raises check50.Failure: if not a comparison, or otherwise
    """
    if isinstance(expr, ast.Compare):
        for op in expr.ops:
            if isinstance(op, (ast.In, ast.NotIn)):
                return Missing
            elif isinstance(op, (ast.Eq, ast.NotEq, ast.Gt, ast.Lt, ast.GtE, ast.LtE)):
                return Mismatch
        
    return Failure