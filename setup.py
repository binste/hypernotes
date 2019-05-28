"""
Publish a new version:
- Change version number in hypernotes/__init__.py
- Add entry to CHANGELOG.md
$ tox
$ git tag vX.Y.Z -m "Release X.Y.Z"
$ git push --tags
Use either pip or conda to upgrade twine and wheel
$ pip install --upgrade twine wheel
$ python setup.py sdist bdist_wheel
$ twine upload dist/*
"""
import setuptools
from pathlib import Path

import hypernotes

HERE = Path(__file__).parent
README = (HERE / "README.md").read_text()

setuptools.setup(
    name="hypernotes",
    version=hypernotes.__version__,
    author="Stefan Binder",
    url="https://github.com/binste/hypernotes",
    description=(
        "A lightweight Python package for taking notes on your"
        + " machine learning experiments"
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    packages=["hypernotes"],
    keywords=[
        "machine learning",
        "tracking",
        "metrics",
        "experiments",
        "hyperparameters",
        "model evaluation",
        "data science",
    ],
    python_requires=">=3.6",
    license="MIT",
    classifiers=(
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ),
)
