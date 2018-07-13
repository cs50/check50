from setuptools import find_packages, setup

import glob
import os
import subprocess

def create_mo_files():
    """Compiles .po files in local/LANG to .mo files and returns them as array of data_files"""
    for prefix in glob.glob("locale/*/LC_MESSAGES/*.po"):
        for _,_,files in os.walk(prefix):
            for file in files:
                po_file = Path(prefix) / po_file
                mo_file = po_file.parent / po_file.stem + ".mo"
                subprocess.call(["msgfmt", "-o", mo_file, po_file])

create_mo_files()

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
    install_requires=["attrs", "bs4", "pexpect", "push50", "pyyaml", "requests", "termcolor"],
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
