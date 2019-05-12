import argparse
import copy
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from json import JSONEncoder
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Sequence, DefaultDict


__version__ = "0.1.1"


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

    _git_key = "git"
    _python_path_key = "python_path"

    def __init__(
        self, text: str = "", note_data: Optional[Dict[str, dict]] = None
    ) -> None:
        if note_data is not None:
            super().__init__(note_data)
        else:
            self[self._text_key] = text
            self._set_up_initial_structure()
            self._start()

    def _set_up_initial_structure(self) -> None:
        self[self._model_key] = None
        self[self._parameters_key] = {}
        self[self._features_key] = self._initial_features_structure()
        self[self._target_key] = None
        self[self._metrics_key] = {}
        self[self._info_key] = {}
        self[self._start_datetime_key] = None
        self[self._end_datetime_key] = None
        self[self._python_path_key] = self._python_executable_path()

    def _initial_features_structure(self) -> dict:
        """This method can easily be overwritten to return a different
        initial structure of the features dictionary, e.g. if you want to always
        include different feature categories.
        """
        return {"identifier": [], "binary": [], "categorical": [], "numerical": []}

    def _python_executable_path(self) -> str:
        return sys.executable

    def _start(self) -> None:
        self[self._start_datetime_key] = datetime.now()
        self._add_git_info()

    def end(self) -> None:
        self[self._end_datetime_key] = datetime.now()

    def _add_git_info(self) -> None:
        if self._is_in_git_repo():
            git_info = {}
            git_info["repo_name"] = (
                subprocess.check_output(["git", "rev-parse", "--git-dir"])
                .strip()
                .decode("utf-8")
            )
            git_info["branch"] = (
                subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
                .strip()
                .decode("utf-8")
            )
            git_info["commit"] = (
                subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
                .strip()
                .decode("utf-8")
            )

            self[self._git_key] = git_info

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

    @property
    def identifier(self) -> str:
        return _format_datetime(self[self._start_datetime_key])

    @property
    def text(self) -> str:
        return self[self._text_key]

    @text.setter
    def text(self, value):
        self[self._text_key] = value

    @property
    def model(self):
        return self[self._model_key]

    @model.setter
    def model(self, value):
        self[self._model_key] = value

    @property
    def metrics(self):
        return self[self._metrics_key]

    @metrics.setter
    def metrics(self, value):
        self[self._metrics_key] = value

    @property
    def parameters(self):
        return self[self._parameters_key]

    @parameters.setter
    def parameters(self, value):
        self[self._parameters_key] = value

    @property
    def features(self):
        return self[self._features_key]

    @features.setter
    def features(self, value):
        self[self._features_key] = value

    @property
    def target(self):
        return self[self._target_key]

    @target.setter
    def target(self, value):
        self[self._target_key] = value

    @property
    def info(self):
        return self[self._info_key]

    @info.setter
    def info(self, value):
        self[self._info_key] = info


class BaseStore:
    """The base store class. This class cannot be used directly and mostly acts
    as a placeholder which defines the store interface. Inherit from this class if you
    want to implement your own store class.
    """

    def __init__(self):
        pass

    def load(self, return_dataframe: bool = False):
        """Should return the full store as List[Note] with the most recent
        note first, or, if return_dataframe=True,
        as a Pandas dataframe.

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError("Should be implemented by BaseStore subclasses")
        loaded_notes = self._load()
        if return_dataframe:
            loaded_notes = self._to_pandas(loaded_notes)
        return loaded_notes

    def add(self, note: Note):
        """Should add an note to the persistent store implemented by the subclass

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError("Should be implemented by BaseStore subclasses")
        note = self._prepare_note_for_storing(note)

    def _prepare_note_for_storing(self, note: Note) -> Note:
        if note[note._end_datetime_key] is None:
            note.end()
        return copy.deepcopy(note)

    def _to_pandas(self, notes: List[Note]):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "Pandas is not installed. You can install it via:\n"
                "conda install pandas\n"
                "or: pip install pandas"
            )
        return pd.DataFrame(copy.deepcopy(self._pandas_dict(notes)))

    def _pandas_dict(self, notes: List[Note]) -> dict:
        flat_dicts = []
        for note in notes:
            flat_dicts.append(self._flatten_dict(dict(note)))

        column_dict = {}  # type: Dict[str, list]
        all_column_names = set([col for d in flat_dicts for col, _ in d.items()])
        for column in all_column_names:
            column_dict[column] = []

        for d in flat_dicts:
            for column in all_column_names:
                column_dict[column].append(d.get(column))

        key_order = (
            [
                Note._start_datetime_key,
                Note._end_datetime_key,
                Note._text_key,
                Note._model_key,
            ]
            + self._filter_sequence_if_startswith(
                column_dict.keys(), startswith=Note._metrics_key
            )
            + self._filter_sequence_if_startswith(
                column_dict.keys(), startswith=Note._parameters_key
            )
            + self._filter_sequence_if_startswith(
                column_dict.keys(), startswith=Note._features_key
            )
            + [Note._target_key]
            + self._filter_sequence_if_startswith(
                column_dict.keys(), startswith=Note._git_key
            )
        )
        key_order.extend(key for key in column_dict.keys() if key not in key_order)
        ordered_dict = {k: column_dict[k] for k in key_order}
        return ordered_dict

    def _flatten_dict(self, d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """Flattens a dictionary by concatenating key names

        Taken from https://stackoverflow.com/a/6027615
        """
        items = []  # type: List[tuple]
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _filter_sequence_if_startswith(
        self, seq: Sequence[str], startswith: str
    ) -> List[str]:
        return [x for x in seq if x.startswith(startswith)]


class Store(BaseStore):
    """Implements a store for notes based on a JSON file"""

    def __init__(self, path: Union[str, Path]) -> None:
        super().__init__()
        self.path = _convert_to_path(path)
        self._create_store_if_not_exists()

    def _create_store_if_not_exists(self):
        store_exists = self.path.exists()
        if not store_exists:
            self._save_notes(notes=[])

    def load(self, return_dataframe: bool = False):
        """Returns the full store as List[Note] with the most recent
        note first, or, if return_dataframe=True, as a Pandas dataframe.
        """
        loaded_notes = self._load()
        if return_dataframe:
            loaded_notes = self._to_pandas(loaded_notes)
        return loaded_notes

    def _load(self) -> List[Note]:
        notes_raw = self._json_load(self.path)
        notes = _raw_dicts_to_notes(notes_raw)
        return self._sort_notes(notes)

    def add(self, note: Note) -> None:
        """Adds a single note to the .json file of the store"""
        # As the whole json file needs to be loaded to add a new entry,
        # changes made to the file between the call to self.load and
        # the saving of the file will be overwritten.
        all_notes = self.load()
        if self._notes_are_subset(notes_subset=[note], all_notes=all_notes):
            raise Exception(
                f"The identifier for the note '{note.identifier}' already exists in the store."
                + " The note was not added."
            )
        note = self._prepare_note_for_storing(note)
        all_notes.append(note)
        self._save_notes(all_notes)

    def update(self, notes: List[Note]) -> None:
        """Updates the passed in notes in the .json file of the store"""
        notes_to_be_updated = notes
        # As the whole json file needs to be loaded to add a new entry,
        # changes made to the file between the call to self.load and
        # the saving of the file will be overwritten.
        stored_notes = self.load()
        # Update list by first filtering out notes which should be updated and
        # then insert new version of notes
        assert self._notes_are_subset(notes_subset=notes, all_notes=stored_notes), (
            "Some of the notes do not yet exist in the store."
            + " Add them with the .add method. Nothing was updated."
        )
        new_stored_notes = self._filter_notes(
            notes_to_filter_out=notes, all_notes=stored_notes
        )
        new_stored_notes.extend(notes_to_be_updated)
        self._save_notes(new_stored_notes)

    def remove(self, notes: List[Note]) -> None:
        """Removes passed in notes from store"""
        stored_notes = self.load()
        assert self._notes_are_subset(notes_subset=notes, all_notes=stored_notes), (
            "Some of the notes do not yet exist in the store."
            + " Nothing was removed. Only pass in notes which already"
            + " exist in the store."
        )
        new_stored_notes = self._filter_notes(
            notes_to_filter_out=notes, all_notes=stored_notes
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
        """Sorted by start datetime. Most recent note first"""
        return list(sorted(notes, key=lambda x: x[x._start_datetime_key], reverse=True))

    @staticmethod
    def _json_load(path: Path) -> List[dict]:
        with path.open("r") as f:
            content = json.load(f, object_hook=_deserialize_datetime)
        return content

    @staticmethod
    def _json_dump(obj: List[dict], path: Path) -> None:
        with path.open("w") as f:
            json.dump(obj, f, cls=DatetimeJSONEncoder)


class DatetimeJSONEncoder(JSONEncoder):
    """Encodes datetime objects as a dictionary
    with key "_isoformat" and the isoformat representation
    of the datetime as value.

    Idea for this encoder class comes from
    https://stackoverflow.com/a/52838324
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return {"_isoformat": _format_datetime(obj)}
        return super().default(obj)


def _deserialize_datetime(obj):
    """Reverts the encoding done by the custom
    DatetimeJSONEncoder class

    Idea for this function comes from
    https://stackoverflow.com/a/52838324
    """
    _isoformat = obj.get("_isoformat")
    if _isoformat is not None:
        return _parse_datetime(_isoformat)
    return obj


def _format_datetime(dt: datetime) -> str:
    return dt.isoformat()


def _parse_datetime(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


def _convert_to_path(path: Union[str, Path]) -> Path:
    if isinstance(path, str):
        path = Path(path)
    return path


def _raw_dicts_to_notes(raw_dicts: List[dict]) -> List[Note]:
    converted_notes = [Note(note_data=raw_note_data) for raw_note_data in raw_dicts]
    return converted_notes


def _notes_to_raw_dicts(notes: List[Note]) -> List[dict]:
    raw_dicts = [dict(note) for note in notes]
    return raw_dicts
