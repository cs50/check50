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
    install_requires=["argparse", "bs4", "pexpect>=4.0", "requests", "backports.shutil_which", "six", "termcolor", "submit50>=2.4.5"],
    keywords=["check", "check50"],
    name="check50",
    py_modules=["check50", "config"],
    packages=find_packages(),
    entry_points={
        "console_scripts": ["check50=check50:main"]
    },
    url="https://github.com/cs50/check50",
    version="2.2.3"
)
