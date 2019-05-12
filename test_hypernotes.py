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
                note._model_key,
                note._target_key,
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
            Note._model_key: "randomforest",
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
            Note._target_key: "target_column",
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

    def test_to_pandas_dict(self):
        store = BaseStore()
        note_1 = Note()
        recall_value = 0.2
        note_1.metrics["recall"] = recall_value
        note_1.end()
        note_2 = Note()
        impute_missings_value = True
        note_2.parameters["impute_missings"] = impute_missings_value
        note_2.end()

        pandas_dict = store._pandas_dict([note_1, note_2])
        assert pandas_dict["metrics.recall"] == [recall_value, None]
        assert pandas_dict["parameters.impute_missings"] == [
            None,
            impute_missings_value,
        ]


class TestStore:
    def test_roundtrip(self, tmp_path):
        """Tests add as well as load"""
        note = Note("Desc")
        note.model = "randomforest"
        note.parameters["impute_missings"] = True
        note.features["identifier"] = ["id"]
        note.features["binary"] = ["bool1"]
        note.features["categorical"] = ["cat1", "cat2"]
        note.features["numerical"] = ["num1"]
        note.target = "target"
        note.info["important_stuff"] = "something noteworthy"
        note.metrics["recall"] = 0.2
        note.metrics["accuracy"] = 0.8

        note_2 = Note("Desc 2")
        note.features["binary"] = ["bool"]

        store = Store(tmp_path / "test_store.json")
        store.add(note)
        store.add(note_2)

        loaded_notes = store.load()
        assert isinstance(loaded_notes, list)
        assert all(isinstance(note, Note) for note in loaded_notes)
        assert all(
            isinstance(note[note._start_datetime_key], datetime)
            for note in loaded_notes
        )
        assert all(
            isinstance(note[note._end_datetime_key], datetime) for note in loaded_notes
        )
        assert len(loaded_notes) == 2
        assert loaded_notes[0] == note_2
        assert loaded_notes[1] == note
        assert Note._end_datetime_key in note_2 and Note._end_datetime_key in note

    def test_update(self, tmp_path):
        note = Note("original note which will later be updated")
        original_value = "randomforest"
        note.model = original_value

        note_2 = Note("note which should be kept as is")
        note_2.model = "fancy_model"

        store = Store(tmp_path / "test_store.json")
        store.add(note)
        store.add(note_2)

        loaded_notes = store.load()
        note_to_udpate = loaded_notes[1]
        assert note_to_udpate.model == original_value
        new_value = "somethingelse"
        note_to_udpate.model = new_value

        store.update([note_to_udpate])
        updated_loaded_notes = store.load()
        assert len(updated_loaded_notes) == 2
        assert updated_loaded_notes[0] == note_2
        assert updated_loaded_notes[1] == note_to_udpate
        assert updated_loaded_notes[1].model == new_value

    def test_remove(self, tmp_path):
        note_1 = Note("Note 1")
        note_2 = Note("Note 2")

        store = Store(tmp_path / "test_store.json")
        store.add(note_1)
        store.add(note_2)

        loaded_notes = store.load()
        assert note_1 in loaded_notes and note_2 in loaded_notes

        store.remove([note_1])
        loaded_notes_again = store.load()
        assert note_1 not in loaded_notes_again and note_2 in loaded_notes


class TestMain:
    def test_html_format(self):
        expected_test_value = "expected_test_value"

        note = Note()
        note.metrics["accuracy"] = 0.2
        note.parameters["impute_values"] = True
        note.parameters["find_this_value"] = expected_test_value
        note.end()

        html = _format_notes_as_html([note])
        self.validate_html(html, expected_test_value)

    def validate_html(self, html: str, expected_test_value: str) -> None:
        assert expected_test_value in html
        assert "<!DOCTYPE html>" in html
        assert "datatables" in html.lower()