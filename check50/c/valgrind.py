import check50
import check50.internal_api

def valgrind(command):
    check50.internal_api.register_after(lambda : check50.log("valgrind inspection"))
    return check50.run(f"valgrind {command}")
