"""A setuptools based setup module.
Copyright 2023 Rivian Automotive, Inc.
"""

# Basic Python
import glob
import os
import shutil
from pathlib import Path
from setuptools import setup, find_packages

# Get the long description from the README file
with open(Path("README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(Path("requirements.txt")) as fh:
    install_requires = []
    for line in fh:
        if "index-url" not in line:
            install_requires.append(line)

version = "0.0.1"


setup(
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    # $ pip install raical
    name="plin",
    # version number
    version=version,
    # This should be a valid link to your project's main homepage.
    url="",
    # Your name or the name of the organization which owns the project
    author="William Zhang",
    # A valid email address corresponding to the author listed above
    author_email="williamzhang@rivian.com",
    # This is a one-line description or tagline of what your project does.
    description="Python PEAK LIN Library",
    # Longer description of your project that users will see
    # when they visit PyPI. Currently set to be the same as the README file
    long_description=long_description,
    # Denotes that our long_description is in Markdown
    # long_description_content_type="text/markdown",
    # Specify directory that package in located in (seems necessary for `package_data`)
    #package_dir={'ral': 'ral'},
    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=["contrib", "docs", "tests", "upload", "examples"]),
    # Supplemental non-python data needed for the package
    #package_data={'ral': glob.glob(os.path.join(dirname, '**', '*'), recursive=True)},
    entry_points={},
    # Specify which Python versions you support. 'pip install' will check this
    # and refuse to install the project if the version does not match.
    python_requires=">=3.7, <4",
    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    install_requires=install_requires,
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # Classifiers help users find your project by categorizing it.
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[
        # How mature is this project? Common values are
        #   2 - Pre-Alpha
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 2 - Pre-Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        #"Topic :: Software Development :: Build Tools",
        # Pick your license as you wish
        # Specify the Python versions you support here
        # These classifiers are *not* checked by 'pip install'
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
