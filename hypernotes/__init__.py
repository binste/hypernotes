import copy
import json
import os
import subprocess
import sys
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from json import JSONEncoder
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from unittest.mock import patch

__version__ = "2.0.2"
DATETIME_STRING_FORMAT = "%Y-%m-%dT%H-%M-%S"


class Note(dict):
    _model_key = "model"
    _parameters_key = "parameters"
    _features_key = "features"
    _target_key = "target"
    _metrics_key = "metrics"
    _info_key = "info"

    _text_key = "text"

    _start_datetime_key = "start_datetime"
    _end_datetime_key = "end_datetime"

    _identifier_key = "identifier"
    _git_key = "git"
    _python_path_key = "python_path"

    def __init__(
        self, text: str = "", content: Optional[Dict[str, dict]] = None
    ) -> None:
        """A small wrapper around dictionaries with a default structure, which can
        be used like a normal dictionary, but additionally stores useful information
        such as time and date, last commit and current branch of git repository,
        path to Python executable, etc.

        All initial dictionary keys can be accessed as attributes
        for better auto-completion support and code readability.


        Parameters
        ----------
        text : str, optional (default="")
            Can be used to store some descriptive text about your experiment
        content : Optional[Dict[str, dict]], optional (default=None)
            Mainly for internal use to create Note instances out of loaded
            dictionaries from a Store. If content is passed, no additional information
            is added on instantiation of the class (e.g. no start datetime,
            identifier, ...), meaning that these attributes already need to be
            present in the passed in dictionary.
        """
        if content is not None:
            super().__init__(content)
            self._content_passed = True
        else:
            self._content_passed = False
            self.text = text
            self._set_up_initial_structure()
            self._start()

    def _set_identifier(self) -> None:
        self.identifier = str(uuid.uuid4())

    def _set_up_initial_structure(self) -> None:
        self.model = None
        self.parameters = {}  # type: dict
        self.features = self._initial_features_structure()
        self.target = None
        self.metrics = {}  # type: dict
        self.info = {}  # type: dict
        self.start_datetime = None
        self.end_datetime = None
        self._set_identifier()
        self.python_path = self._python_executable_path()
        self.git = {}  # type: dict

    def _initial_features_structure(self) -> dict:
        """This method can easily be overwritten to return a different
        initial structure of the features dictionary, e.g. if you want to always
        include different feature categories.
        """
        return {"identifier": [], "binary": [], "categorical": [], "numerical": []}

    def _python_executable_path(self) -> str:
        return sys.executable

    def _start(self) -> None:
        self.start_datetime = self._current_datetime()
        self._add_git_info()

    def end(self) -> None:
        """Adds the current datetime as 'end_datetime' to the note"""
        self.end_datetime = self._current_datetime()

    def _current_datetime(self) -> datetime:
        return datetime.now().replace(microsecond=0)

    def _add_git_info(self) -> None:
        if self._is_in_git_repo():
            self.git["repo_name"] = (
                subprocess.check_output(["git", "rev-parse", "--git-dir"])
                .strip()
                .decode("utf-8")
            )
            self.git["branch"] = (
                subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
                .strip()
                .decode("utf-8")
            )
            self.git["commit"] = (
                subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
                .strip()
                .decode("utf-8")
            )

    def _is_in_git_repo(self) -> bool:
        """Function based on following stackoverflow answer by tdelaney:
        https://stackoverflow.com/a/19688210
        """
        if (
            subprocess.call(
                ["git", "branch"],
                stderr=subprocess.STDOUT,
                stdout=open(os.devnull, "w"),
            )
            != 0
        ):
            return False
        else:
            return True

    @classmethod
    def from_note(cls, note: "Note") -> "Note":
        """Creates a new note from an existing one, taking over its content
        but setting a new start datetime and identifier.

        Can for example be used when evaluating multiple model parameters
        (e.g. in a gridsearch setup). Simply create a new note from the original one
        for each parameter set which should be evaluated and add the parameters
        and metrics to the new note.

        This method creates a deepcopy of the original one, meaning that modifying
        the new note should not affect the old one.

        Parameters
        ----------
        note : Note
            Existing ntoe from which the content should be taken over

        Returns
        -------
        Note
        """
        assert isinstance(note, cls)
        new_note = copy.deepcopy(note)
        new_note.start_datetime = new_note._current_datetime()
        new_note._set_identifier()
        return new_note

    @property
    def identifier(self) -> str:
        return self[self._identifier_key]

    @identifier.setter
    def identifier(self, value: str):
        self[self._identifier_key] = value

    @property
    def text(self) -> str:
        return self[self._text_key]

    @text.setter
    def text(self, value: str):
        self[self._text_key] = value

    @property
    def model(self) -> str:
        return self[self._model_key]

    @model.setter
    def model(self, value: str):
        self[self._model_key] = value

    @property
    def metrics(self) -> dict:
        return self[self._metrics_key]

    @metrics.setter
    def metrics(self, value: dict):
        self[self._metrics_key] = value

    @property
    def parameters(self) -> dict:
        return self[self._parameters_key]

    @parameters.setter
    def parameters(self, value: dict):
        self[self._parameters_key] = value

    @property
    def features(self) -> dict:
        return self[self._features_key]

    @features.setter
    def features(self, value: dict):
        self[self._features_key] = value

    @property
    def target(self) -> str:
        return self[self._target_key]

    @target.setter
    def target(self, value: str):
        self[self._target_key] = value

    @property
    def info(self) -> dict:
        return self[self._info_key]

    @info.setter
    def info(self, value: dict):
        self[self._info_key] = value

    @property
    def start_datetime(self) -> datetime:
        return self[self._start_datetime_key]

    @start_datetime.setter
    def start_datetime(self, value: datetime):
        self[self._start_datetime_key] = value

    @property
    def end_datetime(self) -> datetime:
        return self[self._end_datetime_key]

    @end_datetime.setter
    def end_datetime(self, value: datetime):
        self[self._end_datetime_key] = value

    @property
    def python_path(self) -> str:
        return self[self._python_path_key]

    @python_path.setter
    def python_path(self, value: str):
        self[self._python_path_key] = value

    @property
    def git(self) -> dict:
        return self[self._git_key]

    @git.setter
    def git(self, value: dict):
        self[self._git_key] = value

    def __repr__(self) -> str:
        # Code and idea for patching sorted to prevent sorting by
        # dictionary keys come from:
        # https://stackoverflow.com/a/55661095
        with patch("builtins.sorted", new=lambda l, **_: l):
            r = f"Note(content={pformat(dict(self))})"
        return r


class BaseStore(ABC):
    """The base store class. This class cannot be used directly and acts
    as a template which defines the store interface. Inherit from this class if you
    want to implement your own store class.
    """

    def __init__(self):
        pass

    @abstractmethod
    def load(self, return_dataframe: bool = False):
        """Should return the full store as List[Note] with the most recent
        note first, or, if return_dataframe=True,
        as a Pandas dataframe.

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        pass

    @abstractmethod
    def add(self, note: Note):
        """Should add an note to the persistent store implemented by the subclass

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        pass


def _prepare_note_for_storing(note: Note) -> Note:
    if note.end_datetime is None:
        note.end()
    return copy.deepcopy(note)


def _to_pandas(notes: List[Note]):
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        raise ImportError(
            "Pandas is not installed. You can install it via:\n"
            "conda install pandas\n"
            "or: pip install pandas"
        )
    return pd.DataFrame(copy.deepcopy(_pandas_dict(notes)))


def _pandas_dict(notes: List[Note]) -> dict:
    flat_dicts = _flatten_notes(notes)
    all_keys = _all_keys_from_dicts(flat_dicts)

    # Create basic structure
    column_dict = {}  # type: Dict[str, list]
    for column in all_keys:
        column_dict[column] = []

    # Fill structure with values
    for d in flat_dicts:
        for column in all_keys:
            column_dict[column].append(d.get(column))

    key_order = _key_order(all_keys)
    ordered_dict = {k: column_dict[k] for k in key_order}
    return ordered_dict


def _flatten_notes(notes: Sequence[Note]) -> List[Dict[str, Any]]:
    flat_dicts = []
    for note in notes:
        flat_dicts.append(_flatten_dict(dict(note)))
    return flat_dicts


def _all_keys_from_dicts(ds: Sequence[Dict[str, Any]]) -> List[str]:
    return list(set([col for d in ds for col, _ in d.items()]))


def _key_order(
    keys: Sequence[str], additional_keys_subset: Optional[Sequence[str]] = None
) -> List[str]:
    """start_datetime, end_datetime, text, model, and identifier are always first.
    Afterwards, either all keys are added in order of metrics, parameters,
    features, git, and others, or only the passed in categories
    from additional_keys_subset. additional_keys_subset can hereby just be
    the start of the strings, e.g. ["metrics", "parameters]"
    """
    key_order = [
        Note._start_datetime_key,
        Note._end_datetime_key,
        Note._text_key,
        Note._model_key,
        Note._identifier_key,
    ]
    if additional_keys_subset is None:
        key_order += (
            _filter_sequence_if_startswith(keys, startswith=Note._metrics_key)
            + _filter_sequence_if_startswith(keys, startswith=Note._parameters_key)
            + _filter_sequence_if_startswith(keys, startswith=Note._features_key)
            + [Note._target_key]
            + _filter_sequence_if_startswith(keys, startswith=Note._info_key)
            + _filter_sequence_if_startswith(keys, startswith=Note._git_key)
            + [Note._python_path_key]
        )
        key_order.extend(sorted([k for k in keys if k not in key_order]))
    else:
        for k in additional_keys_subset:
            key_order += _filter_sequence_if_startswith(keys, startswith=k)
    return key_order


def _flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flattens a dictionary by concatenating key names

    Taken from https://stackoverflow.com/a/6027615
    """
    items = []  # type: List[Tuple[Any, Any]]
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _filter_sequence_if_startswith(seq: Sequence[str], startswith: str) -> List[str]:
    return sorted([x for x in seq if x.startswith(startswith)])


class Store(BaseStore):
    """Main purpose is to store Note instances in a json file. Additional methods are
    provided to load all notes, as well as update or remove specified notes.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        """
        Parameters
        ----------
        path : Union[str, Path]
            Path to the json file. If it does not yet exist, a new one will be created,
            else, the Store will interact with the existing file and modify it
        """
        super().__init__()
        self.path = _convert_to_path(path)
        self._create_store_if_not_exists()

    def _create_store_if_not_exists(self):
        store_exists = self.path.exists()
        if not store_exists:
            self._save_notes(notes=[])

    def load(self, return_dataframe: bool = False):
        """Loads the entire json file and returns it as a list of Note instances
        with the most recent note first. Optionally, a pandas dataframe can be
        returned instead.

        Parameters
        ----------
        return_dataframe : bool, optional (default=False)
            If True, a pandas dataframe is returned with one row per note,
            where nested structures inside the notes are resolved as far as possible
            and the keys are joined with "." to form column names. This requires
            the pandas package to be installed.

        Returns
        -------
        Either List[str] or pd.DataFrame, depending on value of return_dataframe
        """
        loaded_notes = self._load()
        if return_dataframe:
            loaded_notes = _to_pandas(loaded_notes)
        return loaded_notes

    def _load(self) -> List[Note]:
        notes_raw = self._json_load(self.path)
        notes = _raw_dicts_to_notes(notes_raw)
        return self._sort_notes(notes)

    def add(self, note: Note) -> None:
        """Adds the given note to the .json file of the store.

        Before storing the note, the .end method of it is called, if
        not already done previously.

        Parameters
        ----------
        note : Note
            The Note instance which should be added to the store. The note
            needs to consist entirely of json serializable objects or
            datetime.datetime instances

        Returns
        -------
        None
        """
        # As the whole json file needs to be loaded to add a new entry,
        # changes made to the file between the call to self.load and
        # the saving of the file will be overwritten.
        all_notes = self.load()
        if self._notes_are_subset(notes_subset=[note], all_notes=all_notes):
            raise Exception(
                f"The identifier for the note '{note.identifier}' "
                + "already exists in the store."
                + " The note was not added."
            )
        note = _prepare_note_for_storing(note)
        all_notes.append(note)
        self._save_notes(all_notes)

    def update(self, notes: Union[Note, Sequence[Note]]) -> None:
        """Updates the passed in notes in the .json file of the store

        Uses the identifier attribute of the notes to find the original ones
        and replaces them

        Parameters
        ----------
        notes: Union[Note, Sequence[Note]]
            One or more notes which should be updated

        Returns
        -------
        None
        """
        if isinstance(notes, Note):
            notes_to_be_updated = [notes]
        else:
            notes_to_be_updated = list(notes)
        # As the whole json file needs to be loaded to add a new entry,
        # changes made to the file between the call to self.load and
        # the saving of the file will be overwritten.
        stored_notes = self.load()
        # Update list by first filtering out notes which should be updated and
        # then insert new version of notes
        assert self._notes_are_subset(
            notes_subset=notes_to_be_updated, all_notes=stored_notes
        ), (
            "Some of the notes do not yet exist in the store."
            + " Add them with the .add method. Nothing was updated."
        )
        new_stored_notes = self._filter_notes(
            notes_to_filter_out=notes_to_be_updated, all_notes=stored_notes
        )
        new_stored_notes.extend(notes_to_be_updated)
        self._save_notes(new_stored_notes)

    def remove(self, notes: Union[Note, Sequence[Note]]) -> None:
        """Removes passed in notes from store

        Uses the identifier attribute of the notes to find the original ones

        Parameters
        ----------
        notes: Union[Note, Sequence[Note]]
            One or more notes which should be removed

        Returns
        -------
        None
        """
        if isinstance(notes, Note):
            notes_to_be_removed = [notes]
        else:
            notes_to_be_removed = list(notes)
        stored_notes = self.load()
        assert self._notes_are_subset(
            notes_subset=notes_to_be_removed, all_notes=stored_notes
        ), (
            "Some of the notes do not yet exist in the store."
            + " Nothing was removed. Only pass in notes which already"
            + " exist in the store."
        )
        new_stored_notes = self._filter_notes(
            notes_to_filter_out=notes_to_be_removed, all_notes=stored_notes
        )
        self._save_notes(new_stored_notes)

    def _notes_are_subset(
        self, notes_subset: List[Note], all_notes: List[Note]
    ) -> bool:
        """Returns true if all notes in note_subset exist in all_notes, else False"""
        notes_subset_identifiers = self._get_identifers_of_notes(notes_subset)
        all_notes_identifiers = self._get_identifers_of_notes(all_notes)
        return all(
            identifier in all_notes_identifiers
            for identifier in notes_subset_identifiers
        )

    def _get_identifers_of_notes(self, notes: List[Note]) -> List[str]:
        return [n.identifier for n in notes]

    def _filter_notes(
        self, notes_to_filter_out: List[Note], all_notes: List[Note]
    ) -> List[Note]:
        notes_to_filter_out_identifiers = self._get_identifers_of_notes(
            notes_to_filter_out
        )
        return [
            note
            for note in all_notes
            if note.identifier not in notes_to_filter_out_identifiers
        ]

    def _save_notes(self, notes: List[Note]) -> None:
        notes = self._sort_notes(notes)
        raw_dicts = _notes_to_raw_dicts(notes)
        self._json_dump(raw_dicts, self.path)

    def _sort_notes(self, notes: List[Note]) -> List[Note]:
        """Sorted by end datetime (descending order, i.e. newest first)
        and if there is a tie also by the identifier to get a deterministic order.
        """
        return list(
            sorted(notes, key=lambda x: (x.end_datetime, x.identifier), reverse=True)
        )

    @staticmethod
    def _json_load(path: Path) -> List[dict]:
        with path.open("r", encoding="utf-8") as f:
            content = json.load(f, object_hook=_deserialize_datetime)
        return content

    @staticmethod
    def _json_dump(obj: List[dict], path: Path) -> None:
        json_str = json.dumps(obj, cls=DatetimeJSONEncoder)
        with path.open("w", encoding="utf-8") as f:
            f.write(json_str)

    def __repr__(self) -> str:
        return f"Store('{self.path}')"


class DatetimeJSONEncoder(JSONEncoder):
    """Encodes datetime objects as a dictionary
    with key "_datetime" and a string representation
    of the datetime as value.

    Idea for this encoder class comes from
    https://stackoverflow.com/a/52838324
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return {"_datetime": _format_datetime(obj)}
        return super().default(obj)


def _deserialize_datetime(obj):
    """Reverts the encoding done by the custom
    DatetimeJSONEncoder class

    Idea for this function comes from
    https://stackoverflow.com/a/52838324
    """
    _datetime = obj.get("_datetime")
    if _datetime is not None:
        return _parse_datetime(_datetime)
    return obj


def _format_datetime(dt: datetime) -> str:
    return dt.strftime(DATETIME_STRING_FORMAT)


def _parse_datetime(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, DATETIME_STRING_FORMAT)


def _convert_to_path(path: Union[str, Path]) -> Path:
    if isinstance(path, str):
        path = Path(path)
    return path


def _raw_dicts_to_notes(raw_dicts: List[dict]) -> List[Note]:
    converted_notes = [Note(content=raw_content) for raw_content in raw_dicts]
    return converted_notes


def _notes_to_raw_dicts(notes: List[Note]) -> List[dict]:
    raw_dicts = [dict(note) for note in notes]
    return raw_dicts
