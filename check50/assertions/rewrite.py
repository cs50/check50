import ast

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

        keywords = [ast.keyword(arg="cond_type", value=ast.Constant(value=cond_type))]

        # Grab the values from the left and right side of the conditional
        # (used in check50.Missing and check50.Mismatch)
        if isinstance(node.test, ast.Compare) and node.test.comparators:
            left = node.test.left
            right = node.test.comparators[0]
            keywords.extend([
                ast.keyword(arg="left", value=left),
                ast.keyword(arg="right", value=right)
            ])

        # Extract variable names and build context={"var": var, ...}
        var_names    = self._extract_names(node.test)
        context_dict = self._make_context_dict(var_names)

        if var_names and context_dict.keys:
            keywords.append(ast.keyword(
                arg="context",
                value=context_dict
            ))

        return ast.Expr(
            value=ast.Call(
                # Create a function called check50_assert
                func=ast.Name(id="check50_assert", ctx=ast.Load()),
                # Give it these postional arguments:
                args=[
                    # The condition
                    node.test,
                    # The string form of the condition
                    ast.Constant(value=ast.unparse(node.test)),
                    # The additional msg or exception that the user provided
                    node.msg if node.msg is not None else ast.Constant(value=None)
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
        Returns a set of the names of every variable in a given AST expression.

        :param expr: An AST expression.
        :type expr: ast.AST
        """
        class NameExtractor(ast.NodeVisitor):
            def __init__(self):
                self.names = set()

            def visit_Name(self, node):
                self.names.add(node.id)

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
        return ast.Dict(
            keys=[ast.Constant(value=name) for name in name_set],
            values=[ast.Name(id=name, ctx=ast.Load()) for name in name_set]
        )
