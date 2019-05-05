import argparse
import copy
import json
import os
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


__version__ = "0.1a"


class Experiment(dict):
    _metrics_key = "metrics"
    _parameters_key = "parameters"
    _features_key = "features"
    _info_key = "info"

    _description_key = "description"

    _start_datetime_key = "start_datetime"
    _end_datetime_key = "end_datetime"

    _git_key = "git"

    def __init__(
        self, description: str = "", experiment_data: Optional[Dict[str, dict]] = None
    ) -> None:
        if experiment_data is not None:
            super().__init__(experiment_data)
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
        self[self._start_datetime_key] = _format_datetime(datetime.now())
        self._add_git_info()

    def end(self) -> None:
        self[self._end_datetime_key] = _format_datetime(datetime.now())

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
        return self[self._start_datetime_key]

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
    """The base store class. This class cannot be used directly and only acts
    as a placeholder which defines the store interface. Inherit from this class if you
    want to implement your own store class.
    """

    def load(self):
        """Should load the full store as Dict[str, Experiment]
        and make it available as the attribute 'experiments'.

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError("Should be implemented by BaseStore subclasses")

    def add(self, experiment):
        """Should add an experiment to the persistent store implemented by the subclass
        and add the experiment to the 'experiments' attribute.

        This method is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError("Should be implemented by BaseStore subclasses")


class JSONStore(BaseStore):
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = _prepare_path(path)

        self.load()

    def load(self):
        store_exists = self.path.exists()
        if not store_exists:
            self._create_new_store()
        else:
            self._load_store()

    def add(self, experiment: Experiment) -> None:
        experiment = _prepare_experiment_for_storing(experiment)
        # Reload json file to prevent overwritting changes
        # to the file which could have happend since the last load.
        # This of course can not prevent overwritting changes
        # which occured between this load and the writing of the file
        self.load()
        self._check_that_experiment_is_not_already_in_store(experiment)
        self.experiments[experiment.identifier] = experiment
        self._save_experiments()

    def _create_new_store(self) -> None:
        self.experiments = {}  # type: Dict[str, Experiment]
        self._save_experiments()

    def _load_store(self) -> None:
        experiments_raw = self._json_load(self.path)
        self.experiments = _raw_dicts_to_experiments(experiments_raw)

    def _check_that_experiment_is_not_already_in_store(self, experiment) -> None:
        if experiment.identifier in self.experiments:
            raise Exception(
                f"The identifier for the experiment '{experiment.identifier}' already exists in the store."
                + " The experiment was not added."
            )

    def _save_experiments(self) -> None:
        experiments_raw = _experiments_to_raw_dicts(self.experiments)
        self._json_dump(experiments_raw, self.path)

    @staticmethod
    def _json_load(path: Path) -> dict:
        with path.open("r") as f:
            content = json.load(f)
        return content

    @staticmethod
    def _json_dump(dict_obj: dict, path: Path) -> None:
        with path.open("w") as f:
            json.dump(dict_obj, f)


class SQLiteStore(BaseStore):
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = _prepare_path(path)

        self.load()


def _format_datetime(dt: datetime) -> str:
    return dt.isoformat()


def _parse_datetime(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


def _prepare_path(path: Union[str, Path]) -> Path:
    if isinstance(path, str):
        path = Path(path)
    return path


def _prepare_experiment_for_storing(experiment: Experiment) -> Experiment:
    if experiment._end_datetime_key not in experiment:
        experiment.end()
    return copy.deepcopy(experiment)


def _raw_dicts_to_experiments(raw_dicts: Dict[str, dict]) -> Dict[str, Any]:
    experiments = {
        identifier: Experiment(experiment_data=raw_experiment_data)
        for identifier, raw_experiment_data in raw_dicts.items()
    }
    return experiments


def _experiments_to_raw_dicts(experiments: Dict[str, Experiment]) -> Dict[str, dict]:
    raw_dicts = {
        identifier: dict(experiment) for identifier, experiment in experiments.items()
    }
    return raw_dicts
