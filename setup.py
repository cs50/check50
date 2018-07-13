from setuptools import find_packages, setup
from setuptools.command.install import install


try:
    from babel.messages import frontend as babel
except ImportError:
    cmdclass = {}
else:
    # https://stackoverflow.com/questions/40051076/babel-compile-translation-files-when-calling-setup-py-install
    class InstallWithCompile(install):
        def run(self):
            compiler = babel.compile_catalog(self.distribution)
            option_dict = self.distribution.get_option_dict("compile_catalog")
            compiler.domain = [option_dict["domain"][1]]
            compiler.directory = option_dict["directory"][1]
            compiler.run()
            super().run()
    cmdclass = {
        "compile_catalog": babel.compile_catalog,
        "extract_messages": babel.extract_messages,
        "init_catalog": babel.init_catalog,
        "update_catalog": babel.update_catalog,
        "install": InstallWithCompile
    }

setup(
    author="CS50",
    author_email="sysadmins@cs50.harvard.edu",
    classifiers=[
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
        "Topic :: Utilities"
    ],
    description="This is check50, with which you can check solutions to problems for CS50.",
    license="GPLv3",
    cmdclass=cmdclass,
    message_extractors = {
        'check50': [('**.py', 'python', None),],
    },
    install_requires=["attrs", "babel", "bs4", "pexpect", "push50", "pyyaml", "requests", "termcolor"],
    extras_require = {
        "develop": ["sphinx", "sphinx_rtd_theme"]
    },
    keywords=["check", "check50"],
    name="check50",
    packages=["check50"],
    python_requires=">= 3.6",
    entry_points={
        "console_scripts": ["check50=check50.__main__:main"]
    },
    url="https://github.com/cs50/check50",
    version="3.0.0",
    include_package_data=True,
)
