def log(line):
    _log.add(line)

class Log:
    def __init__(self):
        self._content = []

    def add(self, line):
        self._content.append(line)

    def __str__(self):
        return "\n".join(self._content)

_log = Log()
