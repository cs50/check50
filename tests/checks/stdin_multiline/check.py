import check50

@check50.check()
def prints_hello_name_non_chaining():
    """prints hello name (non chaining)"""
    check50.run("python3 foo.py").stdin("bar\nbaz").stdout("hello bar").stdout("hello baz")

@check50.check()
def prints_hello_name_non_chaining_prompt():
    """prints hello name (non chaining) (prompt)"""
    check50.run("python3 foo.py").stdin("bar\nbaz", prompt=True).stdout("hello bar").stdout("hello baz")

@check50.check()
def prints_hello_name_chaining():
    """prints hello name (chaining)"""
    check50.run("python3 foo.py").stdin("bar").stdout("hello bar").stdin("baz").stdout("hello baz")

@check50.check()
def prints_hello_name_chaining_order():
    """prints hello name (chaining) (order)"""
    check50.run("python3 foo.py").stdin("bar").stdin("baz").stdout("hello bar").stdout("hello baz")
