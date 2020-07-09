import check50
from check50.internal import RemoteCheckError

json = {
    "slug": "jelleas/foo/master",
    "error": {
        "type": "InvalidSlugError",
        "value": "foo",
        "traceback": [
            "Traceback (most recent call last):\n",
            "bar\n"
        ],
        "actions": {
            "show_traceback": True,
            "message": "foo"
        },
        "data": {}
    },
    "version": "3.1.1"
}

raise RemoteCheckError(json)
