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
        # Create an import statement for the check50_assert
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
    Helper class to to wrap the conditions being tested by assert with a
    function called `check50_assert`.
    """
    
    def visit_Assert(self, node):
        """
        An overwrite of the AST module's visit_Assert to inject our code in
        place of the default assertion logic.

        :param node: An AST node.
        :type node: ast.node
        """
        self.generic_visit(node)
        return ast.Expr(
            value=ast.Call(
                func=ast.Name(id="check50_assert", ctx=ast.Load()),
                args=[
                    node.test,
                    ast.Constant(value=ast.unparse(node.test)),
                    node.msg if node.msg is not None else ast.Constant(value=None)
                ],
                keywords=[]
            )
        )