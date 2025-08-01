import ast
import re

def rewrite(path: str):
    """
    A function that rewrites all instances of `assert` in a file to our own
    `check50_assert` function that raises our own exceptions.

    :param path: The path to the file you wish to rewrite.
    :type path: str
    """
    with open(path) as f:
        source = f.read()

    # Parse the tree and replace all instance of `assert`.
    tree = ast.parse(source, filename=path)
    transformer = _AssertionRewriter()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    # Insert `from check50.assertions.runtime import check50_assert` only if not already present
    if not any(
        isinstance(stmt, ast.ImportFrom) and stmt.module == "check50.assertions.runtime"
        for stmt in new_tree.body
    ):
        # Create an import statement for check50_assert
        import_stmt = ast.ImportFrom(
            module="check50.assertions.runtime",
            names=[ast.alias(name="check50_assert", asname=None)],
            level=0
        )

        # Prepend to the beginning of the file
        new_tree.body.insert(0, import_stmt)

    modified_source = ast.unparse(new_tree)

    # Write to the file
    with open(path, 'w') as f:
        f.write(modified_source)

def rewrite_enabled(path: str):
    """
    Checks if the first line of the file contains a comment of the form:

    ```
    # ENABLE_CHECK50_ASSERT = 1
    ```

    Ignores whitespace.

    :param path: The path to the file you wish to check.
    :type path: str
    """
    pattern = re.compile(
        r"^#\s*ENABLE_CHECK50_ASSERT\s*=\s*(1|True)$",
        re.IGNORECASE
    )

    with open(path, 'r') as f:
        first_line = f.readline().strip()
        return bool(pattern.match(first_line))


class _AssertionRewriter(ast.NodeTransformer):
    """
    Helper class to to wrap the conditions being tested by `assert` with a
    function called `check50_assert`.
    """
    def visit_Assert(self, node):
        """
        An overwrite of the AST module's visit_Assert to inject our code in
        place of the default assertion logic.

        :param node: The `assert` statement node being visited and transformed.
        :type node: ast.Assert
        """
        self.generic_visit(node)
        cond_type = self._identify_comparison_type(node.test)

        # Begin adding a named parameter that determines the type of condition
        keywords = [ast.keyword(arg="cond_type", value=ast.Constant(value=cond_type))]

        # Extract variable names and build context={"var": var, ...}
        var_names    = self._extract_names(node.test)
        context_dict = self._make_context_dict(var_names)

        if var_names and context_dict.keys:
            keywords.append(ast.keyword(
                arg="context",
                value=context_dict
            ))

        # Set the left and right side of the conditional as strings for later
        # evaluation (used when raising check50.Missing and check50.Mismatch)
        if isinstance(node.test, ast.Compare) and node.test.comparators:
            left_node = node.test.left
            right_node = node.test.comparators[0]

            left_str = ast.unparse(left_node)
            right_str = ast.unparse(right_node)

            # Only add to context if not literal constants
            if not isinstance(left_node, ast.Constant):
                context_dict.keys.append(ast.Constant(value=left_str))
                context_dict.values.append(ast.Constant(value=None))
            if not isinstance(right_node, ast.Constant):
                context_dict.keys.append(ast.Constant(value=right_str))
                context_dict.values.append(ast.Constant(value=None))


            keywords.extend([
                ast.keyword(arg="left", value=ast.Constant(value=left_str)),
                ast.keyword(arg="right", value=ast.Constant(value=right_str))
            ])

        return ast.Expr(
            value=ast.Call(
                # Create a function called check50_assert
                func=ast.Name(id="check50_assert", ctx=ast.Load()),
                # Give it these postional arguments:
                args=[
                    # The string form of the condition
                    ast.Constant(value=ast.unparse(node.test)),
                    # The additional msg or exception that the user provided
                    node.msg or ast.Constant(value=None)
                ],
                # And these named parameters:
                keywords=keywords
            )
        )


    def _identify_comparison_type(self, test_node):
        """
        Checks if a conditional is a comparison between two expressions. If so,
        attempts to identify the comparison operator (e.g., `==`, `in`). Falls
        back to "unknown" if the conditional is not a comparison or if the
        operator is not recognized.

        :param test_node: The AST conditional node that is being identified.
        :type test_node: ast.expr
        """
        if isinstance(test_node, ast.Compare) and test_node.ops:
            op = test_node.ops[0] # the operator in between the comparators
            if isinstance(op, ast.Eq):
                return "eq"
            elif isinstance(op, ast.In):
                return "in"

        return "unknown"

    def _extract_names(self, expr):
        """
        Returns a set of the names of every variable, function
        (including the modules or classes they're located under), and function
        argument in a given AST expression.

        :param expr: An AST expression.
        :type expr: ast.AST
        """
        class NameExtractor(ast.NodeVisitor):
            def __init__(self):
                self.names = set()
                self._in_func_chain = False # flag to track nested Calls and Names

            def visit_Call(self, node):
                # Temporarily store whether we're already in a chain
                already_in_chain = self._in_func_chain

                # If already_in_chain is False, we're at the top-most level of
                # the Call node. Without this guard, callable classes/modules
                # will also be included in the output. For instance,
                # check50.run('./test') AND check50.run('./test').stdout() will
                # be included.
                if not already_in_chain:
                    # Grab the entire dotted function name
                    full_name = self._get_full_func_name(node)
                    self.names.add(full_name)

                # As we travel down the function's subtree, denote this flag as True
                self._in_func_chain = True
                self.visit(node.func)
                self._in_func_chain = already_in_chain # Restore previous state

                # Now visit the arguments of this function
                for arg in node.args:
                    self.visit(arg)
                for kw in node.keywords:
                    self.visit(kw)

            def visit_Name(self, node):
                self.names.add(node.id)

            def _get_full_func_name(self, node):
                """
                Grab the entire function name, including the module or class
                in which the function was located, as well as the function
                arguments.

                For instance, this function would return
                ```
                    "check50.run('./test').stdout()"
                ```
                as opposed to
                ```
                    "stdout"
                ```
                """
                def format_args(call_node):
                    # Positional arguments
                    args = [ast.unparse(arg) for arg in call_node.args]
                    # Keyword arguments
                    kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in call_node.keywords]
                    all_args = args + kwargs
                    return f"({', '.join(all_args)})"

                parts = []
                # Apply the same operations for even nested function calls.
                while isinstance(node, ast.Call):
                    func = node.func
                    arg_string = format_args(node)

                    # Attributes inside of Calls signify a `.` attribute was used
                    if isinstance(func, ast.Attribute):
                        parts.append(func.attr + arg_string)
                        node = func.value  # step into next node in chain
                    elif isinstance(func, ast.Name):
                        parts.append(func.id + arg_string)
                        return ".".join(reversed(parts))
                    else:
                        return f"[DEBUG] failed to grab func name: {ast.unparse(func)}"

                if isinstance(node, ast.Name):
                    parts.append(node.id)

                return ".".join(reversed(parts))

        extractor = NameExtractor()
        extractor.visit(expr)
        return extractor.names

    def _make_context_dict(self, name_set):
        """
        Returns an AST dictionary in which the keys are the names of variables
        and the values are the value from each respective variable.

        :param name_set: A set of known names of variables.
        :type name_set: set[str]
        """
        keys, values = [], []
        for name in name_set:
            keys.append(ast.Constant(value=name))
            # Defer evaluation of the values until later, since we don't have
            # access to function results at this point
            values.append(ast.Constant(value=None))

        return ast.Dict(keys=keys, values=values)


