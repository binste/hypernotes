import argparse
import copy
import json
import os
import subprocess
import textwrap
from datetime import datetime
from json import JSONEncoder
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Sequence, DefaultDict


__version__ = "0.1a"


class Note(dict):
    _metrics_key = "metrics"
    _parameters_key = "parameters"
    _features_key = "features"
    _info_key = "info"

    _description_key = "description"

    _start_datetime_key = "start_datetime"
    _end_datetime_key = "end_datetime"

    _git_key = "git"

    def __init__(
        self, description: str = "", note_data: Optional[Dict[str, dict]] = None
    ) -> None:
        if note_data is not None:
            super().__init__(note_data)
        else:
            self[self._description_key] = description
            self._set_up_initial_structure()
            self._start()

    def _set_up_initial_structure(self) -> None:
        self[self._metrics_key] = {}
        self[self._parameters_key] = {}
        self[self._features_key] = self._initial_features_structure()
        self[self._info_key] = {}

    def _initial_features_structure(self) -> dict:
        """This method can easily be overwritten to return a different
        initial structure of the features dictionary, e.g. if you want to always
        include different feature categories.
        """
        return {"identifier": [], "binary": [], "categorical": [], "numerical": []}

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
    def description(self) -> str:
        return self[self._description_key]

    @description.setter
    def description(self, value):
        self[self._description_key] = value

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
        self.notes = {}

    def load(self):
        """Should load the full store as Dict[str, Note]
        and make it available as the attribute 'notes'.

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError("Should be implemented by BaseStore subclasses")

    def add(self, note):
        """Should add an note to the persistent store implemented by the subclass
        and add the note to the 'notes' attribute.

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError("Should be implemented by BaseStore subclasses")
        self._add_to_notes(note)

    def _add_to_notes(self, note: Note) -> None:
        note = self._prepare_note_for_storing(note)
        self.notes[note.identifier] = note

    def _prepare_note_for_storing(self, note: Note) -> Note:
        if note._end_datetime_key not in note:
            note.end()
        return copy.deepcopy(note)

    def to_pandas(self):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "Pandas is not installed. You can install it via:\n"
                "conda install pandas\n"
                "or: pip install pandas"
            )
        return pd.DataFrame(copy.deepcopy(self._pandas_dict()))

    def _pandas_dict(self) -> dict:
        flat_dicts = []
        for identifier, note in self.notes.items():
            flat_dicts.append(self._flatten_dict(dict(note)))

        column_dict = {}  # type: Dict[str, list]
        all_column_names = set([col for d in flat_dicts for col, _ in d.items()])
        for column in all_column_names:
            column_dict[column] = []

        for d in flat_dicts:
            for column in all_column_names:
                column_dict[column].append(d.get(column))

        key_order = (
            [Note._start_datetime_key, Note._end_datetime_key, Note._description_key]
            + self._filter_sequence_if_startswith(
                column_dict.keys(), startswith=Note._metrics_key
            )
            + self._filter_sequence_if_startswith(
                column_dict.keys(), startswith=Note._parameters_key
            )
            + self._filter_sequence_if_startswith(
                column_dict.keys(), startswith=Note._features_key
            )
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

        self.load()

    def load(self):
        store_exists = self.path.exists()
        if not store_exists:
            self._create_new_store()
        else:
            self._load_store()

    def add(self, note: Note) -> None:
        # Reload json file to prevent overwritting changes
        # to the file which could have happend since the last load.
        # This of course can not prevent overwritting changes
        # which occured between this load and the writing of the file
        self.load()
        self._check_that_note_is_not_already_in_store(note)
        self._add_to_notes(note)
        self._save_notes()

    def _create_new_store(self) -> None:
        self._save_notes()

    def _load_store(self) -> None:
        notes_raw = self._json_load(self.path)
        self.notes = _raw_dicts_to_notes(notes_raw)

    def _check_that_note_is_not_already_in_store(self, note) -> None:
        if note.identifier in self.notes:
            raise Exception(
                f"The identifier for the note '{note.identifier}' already exists in the store."
                + " The note was not added."
            )

    def _save_notes(self) -> None:
        notes_raw = _notes_to_raw_dicts(self.notes)
        self._json_dump(notes_raw, self.path)

    @staticmethod
    def _json_load(path: Path) -> dict:
        with path.open("r") as f:
            content = json.load(f, object_hook=_deserialize_datetime)
        return content

    @staticmethod
    def _json_dump(dict_obj: dict, path: Path) -> None:
        with path.open("w") as f:
            json.dump(dict_obj, f, cls=DatetimeJSONEncoder)


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


def _raw_dicts_to_notes(raw_dicts: Dict[str, dict]) -> Dict[str, Any]:
    notes = {
        identifier: Note(note_data=raw_note_data)
        for identifier, raw_note_data in raw_dicts.items()
    }
    return notes


def _notes_to_raw_dicts(notes: Dict[str, Note]) -> Dict[str, dict]:
    raw_dicts = {identifier: dict(note) for identifier, note in notes.items()}
    return raw_dicts
