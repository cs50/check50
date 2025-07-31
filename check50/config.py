class Config:
    """
    Configuration for `check50` behavior.

    This class stores user-defined configuration options that influence
    check50's output formatting.

    For developers of `check50`, you can extend the `Config` class by adding new
    variables to the `__init__`, which will automatically generate new "setter"
    functions to modify the default values. Additionally, if the new
    configuration needs to be validated before the user can modify it, add your
    validation into the `_validators` dictionary.
    """

    def __init__(self):
        self.truncate_len = 10
        self.dynamic_truncate = True

        # Create boolean validators for your variables here (if needed):
        # A help message is not required.
        self._validators = {
            "truncate_len": (lambda val: isinstance(val, int) and val >= 1,
                             "truncate_len must be a positive integer"),
            "dynamic_truncate": (lambda val: isinstance(val, bool),
                                 "dynamic_truncate must be a boolean")
        }

        # Dynamically generates setter functions based on variable names and
        # the type of the default values
        self._generate_setters()

    def _generate_setters(self):
        def make_setter(attr):
            """Factory for making functions like `set_<attr_name>(arg)`"""

            def setter(self, value):
                # Get the entry in the dict of validators.
                # Check to see if the value passes the validator, and if it
                # didn't, display the help message, if any.
                validator_entry = self._validators.get(attr)

                if validator_entry:
                    if isinstance(validator_entry, tuple):
                        validator, help = validator_entry
                    else:
                        validator, help = validator_entry, None

                    if not validator(value):
                        error_msg = f"invalid value for {attr}: {value}"
                        if help:
                            error_msg += f", {help}"
                        raise ValueError(error_msg)

                setattr(self, attr, value)
            return setter

        # Iterate through the names of every instantiated variable
        for attribute_name in self.__dict__:
            if attribute_name.startswith('_'):
                continue  # skip "private" attributes (denoted with a prefix `_`)
            value = getattr(self, attribute_name)
            if callable(value):
                continue  # skip functions/methods

            # Create a class method with the given name and function
            setattr(self.__class__, f"set_{attribute_name}", make_setter(attribute_name))


config = Config()
