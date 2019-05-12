"""
Publish a new version:
$ git tag X.Y.Z -m "Release X.Y.Z"
$ git push --tags
$ pip install --upgrade twine wheel
$ python setup.py sdist bdist_wheel
$ twine upload dist/*
"""
import setuptools

import hypernotes

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="hypernotes",
    version=hypernotes.__version__,
    author="Stefan Binder",
    url="https://github.com/binste/hypernotes",
    description=(
        "hypernotes is a lightweight Python package for taking notes on your machine learning experiments."
    ),
    long_description=long_description,
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
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ),
)
