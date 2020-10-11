import re


def decimal(number):
    """
    Create a regular expression to match the number exactly:

    In case of a positive number::

        (?<![\d\-])number(?!(\.?\d))

    In case of a negative number::

        number(?!(\.?\d))

    :code:`(?<![\d\-])` = negative lookbehind, \
        asserts that there are no digits and no - in front of the number.

    :code:`(?!(\.?\d))` = negative lookahead, \
        asserts that there are no digits and no additional . followed by digits after the number.

    :param number: the number to match in the regex
    :type number: any numbers.Number (such as int, float, ...)
    :rtype: str

    Example usage::

        # Check that 7.0000 is printed with 5 significant figures
        check50.run("./prog").stdout(check50.regex.decimal("7.0000"))

    """
    negative_lookbehind = fr"(?<![\d\-])" if number >= 0 else ""
    return fr"{negative_lookbehind}{re.escape(str(number))}(?!(\.?\d))"
