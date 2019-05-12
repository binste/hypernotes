# hypernotes
hypernotes is a lightweight Python package for taking notes on your machine learning experiments. It provides a simple way to store hyperparameters, their corresponding evaluation metrics, as well as additional information and retrieve them again later for analyzing. It is written in pure Python and requires no additional dependencies.

# Installation
```bash
pip install hypernotes
```

Only Python 3.6+ is supported

# Basic Usage
hypernotes implements a *Note* and a *Store* class. A *Note* is a small wrapper around Python dictionaries. This means that you can do everything with it, that you could do with a normal dictionary, but in addition, it stores:

* the path to your Python executable,
* information about the current state of your Git repository (if there is one) such as the last commit, current branch, etc.,
* start (upon initialization) and end time (call note.end() or add to store)

and it provides

* a useful default dictionary structure (just print a note instance and you will see what's inside)
* access to the most commonly used dictionary keys as attributes for better auto-completion support and readability (see below, for example `note.metrics`)

The notes are then saved using as *Store* instance, which uses a json file. Due to this, you can only add json serializable objects + datetime.datetime instances to a *Note*.

A note is uniquely identifiable by its `identifier` attribute, which is the start datetime in ISO format.

## Add a note
```python
from hypernotes import Note, Store

note = Note("Some descriptive text about your experiment")

# Add name of used algorithm
note.model = "randomforest"

# Add hyperparameters about model training, preprocessing, etc.
note.parameters["num_estimators"] = 100
note.parameters["impute_missings"] = True

# Add the names of the features and of the target variable
note.features["identifier"] = ["id"]
note.features["binary"] = ["bool1"]
note.features["categorical"] = ["cat1", "cat2"]
note.features["numerical"] = ["num1"]
note.target = "target"

# Some additional information
note.info["important_stuff"] = "something noteworthy"

# ... Rest of your code ...
# train_recall, train_precision test_recall, test_precision = train_and_evaluate_model(
#                                              parameters=note.params,
#                                              feature_names=note.features,
#                                              label_name=note.label)
# ...

# Add your calculated evaluation metrics
note.metrics["train"] = {"recall": train_recall, "precision": train_precision}
note.metrics["test"] = {"recall": test_recall, "precision": test_precision}

store = Store("hyperstore.json")
store.add(note)
```

## Load notes
A Store instance provides the `load` method, which can be used to retrieve the whole store. By default it returns a sorted list (most recent note first).
```python
notes = store.load()
most_recent_note = notes[0]
print(most_recent_note.identifier)
```

If you have [pandas](https://github.com/pandas-dev/pandas) installed, you can use the `return_dataframe` argument to return a pandas dataframe.
```python
notes_df = store.load(return_dataframe=True)
notes_df.head()
```

## Update notes
If you want to update notes, you can do this either directly in the *json* file containing the notes, or load the notes as described above, change the relevant ones, and pass them to the `update` method.
```python
notes = store.load()
updated_notes = []
for note in notes[:2]:
    note.info["something_new"] = "..."
    updated_notes.append(note)

store.update(updated_notes)
```

## Remove notes
If you want to remove notes, you can do this either directly in the *json* file containing the notes, or load the notes as described above, and pass the ones which you want to remove to the `remove` method.
```python
notes = store.load()
notes_to_remove = notes[:2]
store.remove(notes_to_remove)
```

## View content of a store directly in your browser
This only requires a modern web browser as well as an internet connection to load the JQuery and Datatables Javascript libraries.
```
$ python -m hypernotes hyperstore.json --view
```


# Other tools
Check out tools such as MLflow, Sacred, DVC, etc. if you need better multi-user capabilities, more advanced reproducibility features, dataset versioning, ...

# Development
Feel free to open a GitHub issue or even better submit a pull request if you find a bug or miss a feature.

Any requirements for developing the package can be installed with
```
pip install -r requirements_dev.txt
```
