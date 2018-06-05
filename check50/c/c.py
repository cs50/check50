import check50

COMPILATION_STRING = "clang ..."

def compile(file_name):
    check50.run(f"{COMPILATION_STRING} {file_name}")
    # throw fail exception if fail
