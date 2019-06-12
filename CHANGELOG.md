# Changelog
## 2.0.2 (2019-06-12)
* Fix issue where stores which contained datetimes in arrays (such as lists) could not be viewed using the command-line interface
* Fix windows compatibility issue of tests

## 2.0.1 (2019-05-30)
* Make datatable properly scale up in width with bigger screens
* Show whole content of store in datatable view (previous behaviour was to show only a subset of columns)
* Show identifier column in table representation (i.e. pandas dataframe or data table view from cli) before metrics, parameters, etc.
* Fix bug where identifier column was shown twice in table representation
* Add black, mypy, and flake8 checks to tox
* Additional documentation improvements and internal changes

## 2.0.0 (2019-05-25)
* **Major**: Change identifier to unique id provided by the uuid module. This breaks compatibility with existing stores. Has the advantage that notes can now have the same start datetime.
* Add attributes for all initial keys in Note instance. Previously it was only for a few
* Git attribute now always exists, but is an empty dictionary if no repository can be found
* Add from_note classmethod to construct a new Note from an existing one
* Fix bug where existing store could be corrupted if a new note was not convertable to json. New behaviour is, that store is only updated if json encoding worked.

## 1.0.0 (2019-05-21)
* **Major**: Change string representation of datetimes to a format without microseconds and which can be used in a path on common file systems. This therefore also changes the return value of the identifier attribute.
* Fix bug in info setter
* Add better repr for Note
* Minor improvements to command-line usage

## 0.3.0 (2019-05-19)
* Add parameter to command-line interface to pass ip for http server
* Add better styling for web page (from command-line interface)
* Minor bug fixes, refactoring, docstring improvements
