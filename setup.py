from setuptools import find_packages, setup


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
    install_requires=["attrs", "bs4", "gitpython", "pexpect", "requests", "termcolor", "submit50>=2.4.5"],
    keywords=["check", "check50"],
    name="check50",
    packages=find_packages(),
    python_requires=">= 3.6",
    entry_points={
        "console_scripts": ["check50=check50.__main__:main",
                            "check50-setup=check50.__main__:setup_main"]
    },
    url="https://github.com/cs50/check50",
    version="3.0.0"
)
