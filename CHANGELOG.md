# Changelog
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
