import json
import sys
import traceback

import lib50
import termcolor

from . import internal, __version__
from .contextmanagers import nullcontext

class Error(Exception):
    """Exception for internal check50 errors."""
    pass


class RemoteCheckError(Error):
    """An exception for errors that happen in check50's remote operation."""
    def __init__(self, remote_json):
        super().__init__("check50 ran into an error while running checks! Please contact sysadmins@cs50.harvard.edu!")
        self.payload = {"remote_json": remote_json}


class ExceptHook:
    def __init__(self, outputs=("ansi",), output_file=None):
        self.outputs = outputs
        self.output_file = output_file

    def __call__(self, cls, exc, tb):
        # If an error happened remotely, grab its traceback and message
        if issubclass(cls, RemoteCheckError) and "error" in exc.payload["remote_json"]:
            formatted_traceback = exc.payload["remote_json"]["error"]["traceback"]
            show_traceback = exc.payload["remote_json"]["error"]["actions"]["show_traceback"]
            message = exc.payload["remote_json"]["error"]["actions"]["message"]
        # Otherwise, create the traceback and message from this error
        else:
            formatted_traceback = traceback.format_exception(cls, exc, tb)
            show_traceback = False

            if (issubclass(cls, Error) or issubclass(cls, lib50.Error)) and exc.args:
                message = str(exc)
            elif issubclass(cls, FileNotFoundError):
                message = _("{} not found").format(exc.filename)
            elif issubclass(cls, KeyboardInterrupt):
                message = _("check cancelled")
            elif not issubclass(cls, Exception):
                # Class is some other BaseException, better just let it go
                return
            else:
                show_traceback = True
                message = _("Sorry, something is wrong! check50 ran into an error.\n" \
                            "Please let CS50 know by emailing the error above to sysadmins@cs50.harvard.edu.")

        # Output exception as json
        if "json" in self.outputs:
            ctxmanager = open(self.output_file, "w") if self.output_file else nullcontext(sys.stdout)
            with ctxmanager as output_file:
                json.dump({
                    "slug": internal.slug,
                    "error": {
                        "type": cls.__name__,
                        "value": str(exc),
                        "traceback": formatted_traceback,
                        "actions": {
                            "show_traceback": show_traceback,
                            "message": message
                        },
                        "data" : exc.payload if hasattr(exc, "payload") else {}
                    },
                    "version": __version__
                }, output_file, indent=4)
                output_file.write("\n")

        # Output exception to stderr
        if "ansi" in self.outputs or "html" in self.outputs:
            if show_traceback:
                for line in formatted_traceback:
                    termcolor.cprint(line, end="", file=sys.stderr)
            termcolor.cprint(message, "red", file=sys.stderr)

        sys.exit(1)

    @classmethod
    def initialize(cls, *args, **kwargs):
        sys.excepthook = cls(*args, **kwargs)
