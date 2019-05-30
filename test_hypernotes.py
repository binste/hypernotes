import multiprocessing as mp
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest  # type: ignore
import requests

from hypernotes import Note, Store, _pandas_dict
from hypernotes.__main__ import _format_notes_as_html, main


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
                note._identifier_key,
                note._git_key,
            )
        )
        assert isinstance(note.start_datetime, datetime)
        python_path = note.python_path
        assert isinstance(python_path, str)
        assert python_path.endswith("python")
        assert Path(python_path).exists()

    def test_end(self):
        note = Note()
        note.end()
        assert isinstance(note.end_datetime, datetime)
        assert note._git_key in note
        for git_info_key in ("repo_name", "branch", "commit"):
            git_value = note.git[git_info_key]
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

    def test_properties_and_setters(self):
        note = Note()
        note.end()
        assert isinstance(note.identifier, str)
        text_value = "test"
        model_value = "model"
        metrics_value = "metrics"
        parameters_value = "parameters"
        features_value = "features"
        target_value = "target"
        info_value = "info"
        start_datetime = datetime.now()
        end_datetime = datetime.now() + timedelta(seconds=1)
        python_path = "test_path"
        git = {"branch": "master", "commit": "1234"}

        note.text = text_value
        note.model = model_value
        note.metrics = metrics_value
        note.parameters = parameters_value
        note.features = features_value
        note.target = target_value
        note.info = info_value
        note.start_datetime = start_datetime
        note.end_datetime = end_datetime
        note.python_path = python_path
        note.git = git

        assert isinstance(note.identifier, str)
        assert len(note.identifier) == 36
        assert note.text == text_value
        assert note.model == model_value
        assert note.metrics == metrics_value
        assert note.parameters == parameters_value
        assert note.features == features_value
        assert note.target == target_value
        assert note.info == info_value
        assert note.start_datetime == start_datetime
        assert note.end_datetime == end_datetime
        assert note.python_path == python_path
        assert note.git == git

    def test_set_identifier(self):
        note = Note()
        old_identifier = note.identifier

        note._set_identifier()

        assert isinstance(old_identifier, str)
        assert isinstance(note.identifier, str)

        assert old_identifier != note.identifier


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

        # Delay creation to make sure that it has a different start datetime
        # Used further below to check if returned order of store is actually based on
        # end datetime instead of start datetime
        time.sleep(1)
        note_2 = Note("Desc 2")
        note.features["binary"] = ["bool"]

        store = Store(tmp_path / "test_store.json")
        # First add note_2 and then add one second of pause to check if store returns
        # notes in order of their end datetimes (and thereby also making sure
        # that not start datetime is used)
        store.add(note_2)
        time.sleep(1)
        store.add(note)

        loaded_notes = store.load()
        assert isinstance(loaded_notes, list)
        assert all(isinstance(note, Note) for note in loaded_notes)
        assert all(isinstance(note.start_datetime, datetime) for note in loaded_notes)
        assert all(isinstance(note.end_datetime, datetime) for note in loaded_notes)
        assert len(loaded_notes) == 2
        assert loaded_notes[0] == note
        assert loaded_notes[1] == note_2
        # Check if same key order is retrieved
        assert list(loaded_notes[0].keys()) == list(note.keys())
        assert list(loaded_notes[1].keys()) == list(note_2.keys())
        assert Note._end_datetime_key in note_2 and Note._end_datetime_key in note

    def test_update(self, tmp_path):
        note = Note("original note which will later be updated")
        original_value = "randomforest"
        note.model = original_value

        note_2 = Note("note which should be kept as is")
        note_2.model = "fancy_model"

        store = Store(tmp_path / "test_store.json")
        store.add(note)
        # Use one second of pause to check if store returns notes in order of their
        # end datetimes
        time.sleep(1)
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

    def test_writing_invalid_note(self, tmp_path):
        invalid_note = Note("Invalid note")
        invalid_note.info["invalid_object"] = InvalidObject()
        valid_note = Note("Valid note")
        store = Store(tmp_path / "test_store.json")

        store.add(valid_note)
        with pytest.raises(TypeError):
            store.add(invalid_note)

        # Make sure that store is still valid json and only contains valid note
        notes = store.load()
        len(notes) == 1
        notes[0] == valid_note

    def test_deterministic_sorting(self, tmp_path):
        # Test if sorting is deterministic even if end datetime is the same
        note = Note()
        note_2 = Note()
        note.end()
        note_2.end()
        note_2.end_datetime = note.end_datetime
        store = Store(tmp_path / "test_store.json")

        store.add(note)
        store.add(note_2)
        loaded_notes = store.load()

        assert len(loaded_notes) == 2
        assert note in loaded_notes
        assert note_2 in loaded_notes
        assert (
            sorted(loaded_notes, key=lambda x: x.identifier, reverse=True)
            == loaded_notes
        )

    def test_from_note(self):
        original_note = Note("original note")
        precision_value = 0.5
        original_note.metrics["precision"] = precision_value

        # Pause to make sure that newly created note gets a different start datetime
        # than the original one
        time.sleep(1)
        new_note = Note.from_note(original_note)
        new_note.features["numerical"].append("num1")

        assert new_note.text == original_note.text
        assert new_note.metrics["precision"] == precision_value
        assert new_note.start_datetime > original_note.start_datetime
        assert new_note.identifier != original_note.identifier
        assert new_note.features["numerical"] == ["num1"]
        assert len(original_note.features["numerical"]) == 0


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


class InvalidObject:
    pass
