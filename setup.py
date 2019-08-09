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
    description="This is check50_js, a javascript extension for check50.",
    license="GPLv3",
    install_requires=["python-bond>=1.4,<2", "check50>=3,<4"],
    keywords=["check50_js"],
    name="check50_js",
    python_requires=">= 3.6",
    url="https://github.com/cs50/check50_js",
    version="0.0.1",
    include_package_data=True
)
