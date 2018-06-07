import check50

CC = "clang"
CFLAGS = "-O0 -ggdb3 " # etc.

def compile(file_name, exe_name=None):
    if exe_name is None and file_name.ends_with(".c"):
        exe_name = file_name.split(".c")[0]

    out_flag = f"-o {exe_name}" if exe_name is not None else ""

    check50.run(f"{CC} {file_name} {out_flag} {CFLAGS}")
