_help_message = ""

def set_help(message):
    global _help_message
    _help_message = message

def help():
    return _help_message
