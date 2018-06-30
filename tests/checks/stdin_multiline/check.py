import check50

@check50.check()
def prints_hello_name_non_chaining():
    """prints hello name (non chaining)"""
    check50.run("python3 foo.py").stdin("bar\nbaz", prompt=False).stdout("hello bar").stdout("hello baz")

@check50.check()
def prints_hello_name_non_chaining_prompt():
    """prints hello name (non chaining) (prompt)"""
    check50.run("python3 foo.py").stdin("bar\nbaz").stdout("hello bar").stdout("hello baz")

@check50.check()
def prints_hello_name_chaining():
    """prints hello name (chaining)"""
    check50.run("python3 foo.py").stdin("bar", prompt=False).stdout("hello bar").stdin("baz", prompt=False).stdout("hello baz")

@check50.check()
def prints_hello_name_chaining_order():
    """prints hello name (chaining) (order)"""
    check50.run("python3 foo.py").stdin("bar", prompt=False).stdin("baz", prompt=False).stdout("hello bar").stdout("hello baz")
