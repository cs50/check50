import os
import pathlib
import tempfile
import unittest

import check50
from check50.assertions.rewrite import rewrite
from check50.assertions.runtime import check50_assert, substitute_expressions


class Base(unittest.TestCase):
    """
    Runs check source through the real assertion rewriter and executes it, so
    `check50_assert` receives exactly the arguments `rewrite.py` generates.
    """

    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.working_directory.name) / "check.py"

    def tearDown(self):
        self.working_directory.cleanup()

    def run_check(self, source, **names):
        """Rewrite `source` and exec it with `names` as globals; return the globals."""
        self.path.write_text("# ENABLE_CHECK50_ASSERT = 1\n" + source)
        rewrite(str(self.path))
        namespace = dict(names)
        exec(compile(self.path.read_text(), str(self.path), "exec"), namespace)
        return namespace

    def assertCheckRaises(self, exc_type, source, **names):
        with self.assertRaises(exc_type) as cm:
            self.run_check(source, **names)
        return cm.exception


class Stub:
    """Stand-in for check50.run(...) results."""

    def __init__(self, out="bar"):
        self.out = out

    def stdout(self):
        return self.out


class TestSingleEvaluation(Base):
    def test_side_effecting_call_runs_exactly_once(self):
        calls = []

        def run(cmd):
            calls.append(cmd)
            return Stub("bar")

        exc = self.assertCheckRaises(
            check50.Mismatch, "assert run('pwd').stdout() == 'foo'", run=run
        )
        self.assertEqual(calls, ["pwd"])
        self.assertEqual(exc.payload["actual"], '"bar"')
        self.assertIn("checked: run('pwd').stdout() == 'foo'", exc.payload["help"])
        self.assertIn("where run('pwd').stdout() = 'bar'", exc.payload["help"])

    def test_repeated_expression_evaluated_once(self):
        calls = []

        def f(a):
            calls.append(a)
            return a

        self.run_check("assert f(1) == f(1)", f=f)
        self.assertEqual(calls, [1])

    def test_passing_assert_is_silent(self):
        self.run_check("assert run('pwd').stdout() == 'bar'", run=lambda cmd: Stub("bar"))

    def test_assert_inside_function_uses_function_locals(self):
        source = (
            "def check():\n"
            "    x = 0\n"
            "    assert x == 1\n"
            "check()\n"
        )
        exc = self.assertCheckRaises(check50.Mismatch, source)
        self.assertEqual(exc.payload["actual"], '"0"')


class TestExceptionPropagation(Base):
    def test_check50_failure_inside_expression_propagates(self):
        def run(cmd):
            raise check50.Failure("command timed out", help="try again")

        exc = self.assertCheckRaises(
            check50.Failure, "assert run('./foo').stdout() == 'x'", run=run
        )
        self.assertIs(type(exc), check50.Failure)
        self.assertEqual(str(exc), "command timed out")
        self.assertEqual(exc.payload["help"], "try again")

    def test_check50_failure_fails_negated_checks(self):
        def run(cmd):
            raise check50.Failure("command timed out")

        for source in (
            "assert run('./foo').stdout() != 'x'",
            "assert 'x' not in run('./foo').stdout()",
            "assert run('./foo').stdout() is not None",
        ):
            with self.subTest(source=source):
                exc = self.assertCheckRaises(check50.Failure, source, run=run)
                self.assertEqual(str(exc), "command timed out")

    def test_native_exception_is_reported_in_where_text(self):
        def run(cmd):
            raise ValueError("boom")

        exc = self.assertCheckRaises(
            check50.Mismatch, "assert run('./foo') == 'x'", run=run
        )
        self.assertIn("where run('./foo') = '[error evaluating: boom]'", exc.payload["help"])

    def test_short_circuit_shape_still_passes(self):
        self.run_check("assert x is None or x.strip() == 'a'", x=None)


class TestMsgOrExc(Base):
    def test_string_message_raises_failure(self):
        exc = self.assertCheckRaises(check50.Failure, "assert x == 1, 'custom message'", x=0)
        self.assertIs(type(exc), check50.Failure)
        self.assertEqual(str(exc), "custom message")

    def test_exception_instance_is_reraised_unchanged(self):
        custom = check50.Mismatch("a", "b")
        exc = self.assertCheckRaises(check50.Mismatch, "assert x == 1, custom", x=0, custom=custom)
        self.assertIs(exc, custom)


class TestFalsyValues(Base):
    def test_falsy_left_values_raise_mismatch(self):
        for value, raw in ((0, '"0"'), ("", '""'), (False, '"False"'), (None, '"None"')):
            with self.subTest(value=value):
                exc = self.assertCheckRaises(check50.Mismatch, "assert x == 1", x=value)
                self.assertEqual(exc.payload["actual"], raw)
                self.assertEqual(exc.payload["expected"], '"1"')
        # Lists are rendered by check50.Mismatch itself; only the type matters here.
        self.assertCheckRaises(check50.Mismatch, "assert x == 1", x=[])

    def test_none_returning_function_raises_mismatch(self):
        exc = self.assertCheckRaises(check50.Mismatch, "assert qux() == 1", qux=lambda: None)
        self.assertEqual(exc.payload["actual"], '"None"')
        self.assertIn("where qux() = None", exc.payload["help"])

    def test_falsy_collections_raise_missing(self):
        for value in ("", [], {}):
            with self.subTest(value=value):
                self.assertCheckRaises(check50.Missing, "assert 'a' in s", s=value)

    def test_non_comparison_raises_failure(self):
        exc = self.assertCheckRaises(check50.Failure, "assert x", x=0)
        self.assertIs(type(exc), check50.Failure)
        self.assertEqual(str(exc), "check did not pass: x\n    where x = 0")


class TestWhereText(Base):
    def test_variables_inside_matched_call_are_shown(self):
        exc = self.assertCheckRaises(check50.Mismatch, "assert len(z) == 3", z=[1, 2])
        self.assertEqual(exc.payload["actual"], '"2"')
        self.assertEqual(exc.payload["help"], "checked: len(z) == 3\n    where z = [1, 2]")

    def test_variable_argument_of_user_function_is_shown(self):
        exc = self.assertCheckRaises(check50.Mismatch, "assert str(x) == 'q'", x=7)
        self.assertEqual(exc.payload["help"], "checked: str(x) == 'q'\n    where x = 7")

    def test_modules_and_functions_are_not_shown(self):
        exc = self.assertCheckRaises(
            check50.Mismatch, "assert os.sep == 'zz'", os=os
        )
        self.assertEqual(exc.payload["help"], "checked: os.sep == 'zz'\n    where os.sep = '/'")
        self.assertNotIn("os = <module", exc.payload["help"])

    def test_where_omitted_when_nothing_to_show(self):
        exc = self.assertCheckRaises(check50.Mismatch, "assert 'a' == 'b'")
        self.assertEqual(exc.payload["help"], "checked: 'a' == 'b'")


class TestAttributePosition(Base):
    def test_variable_named_like_attribute_does_not_break_eval(self):
        class Obj:
            x = 5

        exc = self.assertCheckRaises(
            check50.Failure, "assert x > 0 and obj.x > 10", x=1, obj=Obj()
        )
        self.assertIs(type(exc), check50.Failure)
        self.assertTrue(str(exc).startswith("check did not pass: x > 0 and obj.x > 10"))


def squash(source):
    """`tokenize.untokenize` chooses its own spacing; compare without it."""
    return "".join(source.split())


class TestSubstituteExpressions(unittest.TestCase):
    def test_longest_match_wins_regardless_of_key_order(self):
        keys = ["check50", "check50.run('pwd')", "check50.run('pwd').stdout()"]
        for order in (keys, list(reversed(keys)), [keys[1], keys[0], keys[2]]):
            with self.subTest(order=order):
                eval_src, mapping = substitute_expressions("check50.run('pwd').stdout() == 'foo'", order)
                self.assertEqual(squash(eval_src), "__expr0=='foo'")
                self.assertEqual(mapping, {"check50.run('pwd').stdout()": "__expr0"})

    def test_quote_style_is_normalized(self):
        eval_src, mapping = substitute_expressions("check50.run('pwd') == 'x'", ['check50.run("pwd")'])
        self.assertEqual(squash(eval_src), "__expr0=='x'")
        self.assertEqual(mapping, {'check50.run("pwd")': "__expr0"})

    def test_repeated_key_shares_placeholder(self):
        eval_src, mapping = substitute_expressions("f(a) == f(a)", ["f(a)", "a", "f"])
        self.assertEqual(squash(eval_src), "__expr0==__expr0")
        self.assertEqual(mapping, {"f(a)": "__expr0"})

    def test_attribute_position_is_not_substituted(self):
        eval_src, mapping = substitute_expressions("x > 0 and foo.x > 10", ["x", "foo"])
        self.assertEqual(squash(eval_src), "__expr0>0and__expr1.x>10")
        self.assertEqual(mapping, {"x": "__expr0", "foo": "__expr1"})

    def test_unmatched_keys_are_not_in_mapping(self):
        eval_src, mapping = substitute_expressions("len(z) == 3", ["len(z)", "z", "len"])
        self.assertEqual(squash(eval_src), "__expr0==3")
        self.assertEqual(mapping, {"len(z)": "__expr0"})

    def test_no_keys_returns_source_unchanged(self):
        eval_src, mapping = substitute_expressions("1 == 1", [])
        self.assertEqual(squash(eval_src), "1==1")
        self.assertEqual(mapping, {})


class TestDirectCall(unittest.TestCase):
    def test_kwargs_shape_generated_by_rewriter(self):
        """The exact call shape `rewrite.py` emits for `assert run('pwd').stdout() == 'foo'`."""
        calls = []

        def run(cmd):
            calls.append(cmd)
            return Stub("bar")

        with self.assertRaises(check50.Mismatch) as cm:
            check50_assert(
                "run('pwd').stdout() == 'foo'",
                None,
                cond_type="eq",
                context={"run": None, "run('pwd').stdout()": None},
                left="run('pwd').stdout()",
                right="'foo'",
            )
        self.assertEqual(calls, ["pwd"])
        self.assertEqual(cm.exception.payload["actual"], '"bar"')


if __name__ == "__main__":
    unittest.main()
