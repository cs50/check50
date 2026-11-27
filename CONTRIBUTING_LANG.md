# Check50 Language Translations
Thank you for your interest in making CS50's tooling more accessible for all. Before contributing, please read this in full to avoid any complications.

## Instructions
CS50 uses GitHub to host code, track issues and feature requests, as well as accept pull requests. Please do not email staff members regarding specific issues or features.

In order to add or edit a language for `check50`, please follow these steps.

1. Fork the `check50` repository.
2. Once in the `check50` directory, run `pip install babel` and `pip install -e .`
3. If the language you are looking to add already exists in `check50/locale/`, please skip to step 6.
    - See all of the 2 letter language codes [here](https://www.loc.gov/standards/iso639-2/php/code_list.php)
4. Generate the template of strings to translate by running `python3 setup.py extract_messages`. This will create a file in `check50/locale/` called `check50.pot`
5. Run `python setup.py init_catalog -l <LANG>`, where `<LANG>` is the 2 letter language code (see [here](https://www.loc.gov/standards/iso639-2/php/code_list.php)), to create a file called `check50.po` located at `check50/locale/<LANG>/LC_MESSAGES/`. This file is where the translations will be inputted.
6. The original English strings are found at every `msgid` occurence. Translations should be inputted directly under at every `msgstr` occurence.
7. To test your translations, run `python3 setup.py compile_catalog` to compile the `check50.po` file into `check50.mo`.
8. `pip3 install .` to install the new version of `check50` containing these translations.

## Design and Formatting
Please follow the formatting of the `msgstr` English strings. For example, if the `msgid` string is

```
msgid ""
"check50 is not intended for use in interactive mode. Some behavior may "
"not function as expected."
```

The `msgstr` string should replicate the spacing of the English string.

Example:
```
msgstr ""
"check50 không thể sử dụng bằng chế độ tương tác, có thể "
"không hoạt động như mong đợi."
```

Instead of:
```
msgstr ""
"check50 không thể sử dụng bằng chế độ tương tác, có thể không hoạt động như mong đợi."
```


## Translation Error Reports


## References
This document was adapted from the open-source contribution guidelines for [Meta's Draft](https://github.com/facebookarchive/draft-js/blob/main/CONTRIBUTING.md)
