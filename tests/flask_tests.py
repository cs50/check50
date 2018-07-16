import pathlib
import os
import sys
import tempfile
import unittest
import check50
import check50.flask

try:
    import flask
    FLASK_INSTALLED = True
except ModuleNotFoundError:
    FLASK_INSTALLED = False
CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"

class Base(unittest.TestCase):
    def setUp(self):
        if not FLASK_INSTALLED:
            raise unittest.SkipTest("flask not installed")

        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()

class TestApp(Base):
    def test_app(self):
        src = \
"""from flask import Flask
app = Flask(__name__)

@app.route('/')
def root():
    return ''"""
        with open("hello.py", "w") as f:
            f.write(src)

        app = check50.flask.app("hello.py")
        self.assertIsInstance(app, check50.flask.app)

    def test_no_app(self):
        with self.assertRaises(check50.Failure):
            check50.flask.app("doesnt_exist.py")



class TestFlask(Base):
    def test_status(self):
        src = \
"""from flask import Flask
app = Flask(__name__)

@app.route('/')
def root():
    return ''"""
        with open("hello.py", "w") as f:
            f.write(src)

        app = check50.flask.app("hello.py")
        app.get("/").status(200)
        app.get("/foo").status(404)
        app.post("/").status(405)

    def test_raw_content(self):
        src = \
"""from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'hello world'"""
        with open("hello.py", "w") as f:
            f.write(src)

        app = check50.flask.app("hello.py")
        app.get("/").raw_content("hello world")

        with self.assertRaises(check50.Failure):
            app.get("/").raw_content("foo")

    def test_content(self):
        src = \
"""from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return '<head>foo</head><body>bar</body>'"""
        with open("hello.py", "w") as f:
            f.write(src)

        app = check50.flask.app("hello.py")
        app.get("/").content("foo")

        with self.assertRaises(check50.Failure):
            app.get("/").content("foo", name="body")

        app.get("/").content("bar")

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
