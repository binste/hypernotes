from datetime import datetime

import pytest

from hypernotes import BaseStore, Note, Store
from hypernotes.__main__ import _format_notes_as_html


class TestNote:
    def test_setup(self):
        note = Note()
        assert all(
            key in note
            for key in (
                note._metrics_key,
                note._parameters_key,
                note._features_key,
                note._info_key,
                note._description_key,
                note._start_datetime_key,
            )
        )
        assert isinstance(note[note._start_datetime_key], datetime)

    def test_end(self):
        note = Note()
        note.end()
        assert isinstance(note[note._end_datetime_key], datetime)
        assert note._git_key in note
        for git_info_key in ("repo_name", "branch", "commit"):
            git_value = note[note._git_key][git_info_key]
            assert isinstance(git_value, str)
            assert len(git_value) > 1

    def test_pass_note_data(self):
        note_data = {
            Note._start_datetime_key: datetime.now(),
            Note._description_key: "",
            Note._metrics_key: {"some_metric": 2},
            Note._parameters_key: {"some_parameter": True},
            Note._features_key: {
                "features": {
                    "identifier": ["id_column"],
                    "binary": ["is_imputed"],
                    "categorical": ["country"],
                    "numerical": ["amount"],
                }
            },
            Note._info_key: {"additional_info": "some info"},
        }
        note = Note(note_data=note_data)

        assert dict(note) == note_data

    def test_pass_description(self):
        description = "Descriptive text about the note"
        note = Note(description=description)
        assert note.description == description


class TestBaseStore:
    def test_raise_notimplementederrors(self):
        store = BaseStore()
        note = Note()

        with pytest.raises(NotImplementedError):
            store.load()
        with pytest.raises(NotImplementedError):
            store.add(note)

    def test_add_to_notes(self):
        store = BaseStore()
        note = Note()

        store._add_to_notes(note)
        assert len(store.notes) == 1
        assert note.identifier in store.notes

    def test_to_pandas_dict(self):
        store = BaseStore()
        note_1 = Note()
        recall_value = 0.2
        note_1.metrics["recall"] = recall_value
        note_2 = Note()
        impute_missings_value = True
        note_2.parameters["impute_missings"] = impute_missings_value

        store._add_to_notes(note_1)
        store._add_to_notes(note_2)
        pandas_dict = store._pandas_dict()
        assert pandas_dict["metrics.recall"] == [recall_value, None]
        assert pandas_dict["parameters.impute_missings"] == [
            None,
            impute_missings_value,
        ]


class TestMain:
    def test_html_format(self, tmp_path):
        expected_test_value = "expected_test_value"

        note = Note()
        note.metrics["accuracy"] = 0.2
        note.parameters["impute_values"] = True
        note.parameters["find_this_value"] = expected_test_value
        store_path = tmp_path / "temp_store.json"
        store = Store(store_path)
        store.add(note)

        html = _format_notes_as_html(store.notes)
        self.validate_html(html, expected_test_value)

    def validate_html(self, html: str, expected_test_value: str) -> None:
        assert expected_test_value in html
        assert "<!DOCTYPE html>" in html
        assert "datatables" in html.lower()
