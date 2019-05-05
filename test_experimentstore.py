from datetime import datetime

import pytest

from experimentstore import BaseStore, Experiment, JSONStore
from experimentstore.__main__ import _format_experiments_as_html


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
        assert isinstance(experiment[experiment._start_datetime_key], datetime)

    def test_end(self):
        experiment = Experiment()
        experiment.end()
        assert isinstance(experiment[experiment._end_datetime_key], datetime)
        assert experiment._git_key in experiment
        for git_info_key in ("repo_name", "branch", "commit"):
            git_value = experiment[experiment._git_key][git_info_key]
            assert isinstance(git_value, str)
            assert len(git_value) > 1

    def test_pass_experiment_data(self):
        experiment_data = {
            Experiment._start_datetime_key: datetime.now(),
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
        experiment = Experiment()

        with pytest.raises(NotImplementedError):
            store.load()
        with pytest.raises(NotImplementedError):
            store.add(experiment)

    def test_add_to_experiments(self):
        store = BaseStore()
        experiment = Experiment()

        store._add_to_experiments(experiment)
        assert len(store.experiments) == 1
        assert experiment.identifier in store.experiments

    def test_to_pandas_dict(self):
        store = BaseStore()
        experiment_1 = Experiment()
        recall_value = 0.2
        experiment_1.metrics["recall"] = recall_value
        experiment_2 = Experiment()
        impute_missings_value = True
        experiment_2.parameters["impute_missings"] = impute_missings_value

        store._add_to_experiments(experiment_1)
        store._add_to_experiments(experiment_2)
        pandas_dict = store.to_pandas_dict()
        assert pandas_dict["metrics.recall"] == [recall_value, None]
        assert pandas_dict["parameters.impute_missings"] == [
            None,
            impute_missings_value,
        ]


class TestMain:
    def test_html_format(self, tmp_path):
        expected_test_value = "expected_test_value"

        experiment = Experiment()
        experiment.metrics["accuracy"] = 0.2
        experiment.parameters["impute_values"] = True
        experiment.parameters["find_this_value"] = expected_test_value
        store_path = tmp_path / "temp_store.json"
        store = JSONStore(store_path)
        store.add(experiment)

        html = _format_experiments_as_html(store.experiments)
        self.validate_html(html, expected_test_value)

    def validate_html(self, html: str, expected_test_value: str) -> None:
        assert expected_test_value in html
        assert "<!DOCTYPE html>" in html
        assert "datatables" in html.lower()
