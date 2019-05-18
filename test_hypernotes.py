import multiprocessing as mp
import time
from datetime import datetime
from pathlib import Path

import pytest
import requests

from hypernotes import Note, Store, _pandas_dict
from hypernotes.__main__ import _format_notes_as_html, main, _parse_args


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
                note._text_key,
                note._start_datetime_key,
                note._end_datetime_key,
                note._python_path_key,
            )
        )
        assert isinstance(note[note._start_datetime_key], datetime)
        python_path = note[note._python_path_key]
        assert isinstance(python_path, str)
        assert python_path.endswith("python")
        assert Path(python_path).exists()

    def test_end(self):
        note = Note()
        note.end()
        assert isinstance(note[note._end_datetime_key], datetime)
        assert note._git_key in note
        for git_info_key in ("repo_name", "branch", "commit"):
            git_value = note[note._git_key][git_info_key]
            assert isinstance(git_value, str)
            assert len(git_value) > 1

    def test_pass_content(self):
        content = {
            Note._start_datetime_key: datetime.now(),
            Note._text_key: "",
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
        note = Note(content=content)

        assert dict(note) == content

    def test_pass_text(self):
        text = "Descriptive text about the note"
        note = Note(text=text)
        assert note.text == text


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
        # Check if same key order is retrieved
        assert list(loaded_notes[0].keys()) == list(note_2.keys())
        assert list(loaded_notes[1].keys()) == list(note.keys())
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

    def test_command_line_interface(self, tmp_path):
        note_1 = Note("Note 1")
        expected_test_value = "expected_test_value"
        note_1.parameters["find_this_value"] = expected_test_value
        note_2 = Note("Note 2")
        store_path = tmp_path / "test_store.json"
        store = Store(store_path)
        store.add(note_1)
        store.add(note_2)

        port = 8080
        p = mp.Process(
            target=main, args=([str(store_path), "--port", str(port), "--no-browser"],)
        )
        try:
            p.start()
            time.sleep(1)
            html = requests.get(f"http://localhost:{port}").text
            self.validate_html(html, expected_test_value)
        finally:
            p.terminate()

    def validate_html(self, html: str, expected_test_value: str) -> None:
        assert expected_test_value in html
        assert "<!DOCTYPE html>" in html
        assert "datatables" in html.lower()


def test_to_pandas_dict():
    note_1 = Note()
    recall_value = 0.2
    note_1.metrics["recall"] = recall_value
    note_1.end()
    note_2 = Note()
    impute_missings_value = True
    note_2.parameters["impute_missings"] = impute_missings_value
    note_2.end()

    pandas_dict = _pandas_dict([note_1, note_2])
    assert pandas_dict["metrics.recall"] == [recall_value, None]
    assert pandas_dict["parameters.impute_missings"] == [None, impute_missings_value]
