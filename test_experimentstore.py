from datetime import datetime

import pytest

from experimentstore import (
    BaseStore,
    Experiment,
    JSONStore,
    _format_datetime,
    _parse_datetime,
)


def validate_datetime_str(dt_str: str):
    assert isinstance(dt_str, str)
    dt = _parse_datetime(dt_str)
    assert isinstance(dt, datetime)


class TestExperiment:
    def test_setup(self):
        experiment = Experiment()
        assert all(
            key in experiment
            for key in (
                experiment._metrics_key,
                experiment._parameters_key,
                experiment._features_key,
                experiment._info_key,
                experiment._description_key,
                experiment._start_datetime_key,
            )
        )
        validate_datetime_str(experiment[experiment._start_datetime_key])

    def test_end(self):
        experiment = Experiment()
        experiment.end()
        validate_datetime_str(experiment[experiment._end_datetime_key])
        assert experiment._git_key in experiment
        for git_info_key in ("repo_name", "branch", "commit"):
            git_value = experiment[experiment._git_key][git_info_key]
            assert isinstance(git_value, str)
            assert len(git_value) > 1

    def test_pass_experiment_data(self):
        experiment_data = {
            Experiment._start_datetime_key: _format_datetime(datetime.now()),
            Experiment._description_key: "",
            Experiment._metrics_key: {"some_metric": 2},
            Experiment._parameters_key: {"some_parameter": True},
            Experiment._features_key: {
                "features": {
                    "identifier": ["id_column"],
                    "binary": ["is_imputed"],
                    "categorical": ["country"],
                    "numerical": ["amount"],
                }
            },
            Experiment._info_key: {"additional_info": "some info"},
        }
        experiment = Experiment(experiment_data=experiment_data)

        assert dict(experiment) == experiment_data

    def test_pass_description(self):
        description = "Descriptive text about the experiment"
        experiment = Experiment(description=description)
        assert experiment.description == description


class TestBaseStore:
    def test_raise_notimplementederrors(self):
        store = BaseStore()
        with pytest.raises(NotImplementedError):
            store.load()

        experiment = Experiment()
        with pytest.raises(NotImplementedError):
            store.add(experiment)
