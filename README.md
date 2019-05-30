# hypernotes <!-- omit in toc -->
[![PyPI version](http://img.shields.io/pypi/v/hypernotes.svg?style=flat-square&color=blue)](https://pypi.python.org/pypi/hypernotes/) [![Python versions](https://img.shields.io/pypi/pyversions/hypernotes.svg?style=flat-square&color=blue)]()

hypernotes is a lightweight Python package for taking notes on your machine learning experiments. It provides a simple way to store hyperparameters, their corresponding evaluation metrics, as well as additional information and retrieve them again later for analyzing. It is written in pure Python and requires no additional dependencies.

# Table of contents <!-- omit in toc -->
- [Installation](#installation)
- [Basic Usage](#basic-usage)
  - [Create note and add to store](#create-note-and-add-to-store)
  - [Load notes](#load-notes)
  - [Update notes](#update-notes)
  - [Remove notes](#remove-notes)
  - [Create note from another one](#create-note-from-another-one)
- [Bonus](#bonus)
  - [View content of a store in your browser](#view-content-of-a-store-in-your-browser)
  - [Store additional objects](#store-additional-objects)
- [Alternatives](#alternatives)
- [Development](#development)

[Changelog for this package](CHANGELOG.md)

# Installation
```bash
pip install hypernotes
```

Python 3.6+ is required

# Basic Usage
hypernotes implements a *Note* and a *Store* class. A *Note* is a small wrapper around Python dictionaries. This means that you can do everything with it, that you could do with a normal dictionary, but in addition, it stores:

* the path to your Python executable,
* information about the current state of your Git repository (if there is one) such as the last commit, current branch, etc.,
* start (upon initialization) and end datetime (call note.end() or add to store)

and it provides:

* a useful default dictionary structure
* access to all initial dictionary keys as attributes for better auto-completion support and readability (for example `note.parameters`, `note.features`)

If you print a note, you can see what's inside. A note right after initialization looks like this:
```python
Note(content={'text': '',
 'model': None,
 'parameters': {},
 'features': {'identifier': [],
              'binary': [],
              'categorical': [],
              'numerical': []},
 'target': None,
 'metrics': {},
 'info': {},
 'start_datetime': datetime.datetime(2019, 5, 21, 11, 3, 20),
 'end_datetime': None,
 'identifier': '3228fe02-d1c8-4251-8b35-bb8ae3d5f227',
 'python_path': 'C:/example_path/python.exe',
 'git': {'repo_name': 'C:/path_to_your_repo',
         'branch': 'master',
         'commit': '6bbdf31'}}
```

The notes are then saved with a *Store* instance, which uses a json file. Due to this, you should only add [json-serializable objects](https://docs.python.org/3/library/json.html#py-to-json-table) + *datetime.datetime* instances to a *Note*.

A note is uniquely identifiable by its `identifier` attribute.

## Create note and add to store
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
#                                              target_name=note.target)
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
```

If you have [pandas](https://github.com/pandas-dev/pandas) installed, you can use the `return_dataframe` argument to return a pandas dataframe.
```python
notes_df = store.load(return_dataframe=True)
notes_df.head()
```
Example of a returned pandas dataframe:
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>start_datetime</th>
      <th>end_datetime</th>
      <th>text</th>
      <th>model</th>
      <th>identifier</th>
      <th>metrics.test.precision</th>
      <th>metrics.test.recall</th>
      <th>metrics.train.precision</th>
      <th>metrics.train.recall</th>
      <th>parameters.min_sample_split</th>
      <th>parameters.num_estimators</th>
      <th>parameters.sample_weight</th>
      <th>features.binary</th>
      <th>features.categorical</th>
      <th>features.identifier</th>
      <th>features.numerical</th>
      <th>target</th>
      <th>git.branch</th>
      <th>git.commit</th>
      <th>git.repo_name</th>
      <th>info.important_stuff</th>
      <th>python_path</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2019-05-21 16:44:48</td>
      <td>2019-05-21 17:05:21</td>
      <td>Another useful description</td>
      <td>randomforest</td>
      <td>0f84217d-e01b-466d-9a73-001827c60584</td>
      <td>0.29</td>
      <td>0.29</td>
      <td>0.40</td>
      <td>0.50</td>
      <td>7</td>
      <td>150</td>
      <td>None</td>
      <td>[bool1]</td>
      <td>[cat1, cat2]</td>
      <td>[id]</td>
      <td>[num1]</td>
      <td>target</td>
      <td>master</td>
      <td>5e098ab</td>
      <td>C:/path_to_your_repo</td>
      <td>something noteworthy</td>
      <td>C:/example_path/python.exe</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2019-05-21 16:12:53</td>
      <td>2019-05-21 16:30:16</td>
      <td>Useful description</td>
      <td>randomforest</td>
      <td>dd8bbc32-ff8f-433d-9eec-a24a7859622f</td>
      <td>0.82</td>
      <td>0.29</td>
      <td>0.91</td>
      <td>0.98</td>
      <td>7</td>
      <td>100</td>
      <td>balanced</td>
      <td>[bool1]</td>
      <td>[cat1, cat2]</td>
      <td>[id]</td>
      <td>[num1]</td>
      <td>target</td>
      <td>master</td>
      <td>5e098ab</td>
      <td>C:/path_to_your_repo</td>
      <td>something noteworthy</td>
      <td>C:/example_path/python.exe</td>
    </tr>
  </tbody>
</table>

## Update notes
If you want to update notes, you can do this either directly in the json file containing the notes, or load the notes as described above, change the relevant ones, and pass them to the `update` method.
```python
notes = store.load()
updated_notes = []
for note in notes[:2]:
    note.info["something_new"] = "..."
    updated_notes.append(note)

store.update(updated_notes)
```

## Remove notes
If you want to remove notes, you can do this either directly in the json file containing the notes, or load the notes as described above, and pass the ones which you want to remove to the `remove` method.
```python
notes = store.load()
notes_to_remove = notes[:2]
store.remove(notes_to_remove)
```

## Create note from another one
When evaluating multiple model parameters (e.g. in a grid search setup), you might find it useful to create a new note for each parameter set. To do this, you can use the `from_note` method to create a new note from an existing one. This takes over all existing content, but also sets a new start datetime and identifier. After creation, the notes are independent, i.e. modifying one will not affect the other.

```python
original_note = Note("Original")
new_note = Note.from_note(original_note)
```

# Bonus
## View content of a store in your browser
To get a quick glance into a store, you can use the package from the command line. It will start an http server and automatically open the relevant page in your web browser. The page contains an interactive table which shows the most relevant information of all notes in the store such as metrics and parameters. The table is similar in style to the one shown in the [Load notes](#load-notes) section.
```
$ python -m hypernotes hyperstore.json
```
This only requires a modern web browser as well as an internet connection to load some javascript libraries and css files.

To see all available options pass the `--help` argument.

## Store additional objects
If you want to store larger artifacts of your experiment, such as a trained model, you could create a separate folder and use the identifier of a note as part of the name.

```python
experiment_folder = f"experiment_{note.identifier}"
```
You can then store any additional objects into this folder and it will be very easy to lather on link them again to the hyperparameters and metrics stored using hypernotes.

# Alternatives
Check out tools such as [MLflow](https://mlflow.org/), [Sacred](https://sacred.readthedocs.io/en/latest/index.html), or [DVC](https://dvc.org/) if you need better multi-user capabilities, more advanced reproducibility features, dataset versioning, ...

# Development
Feel free to open a GitHub issue or even better submit a pull request if you find a bug or miss a feature.

Any requirements for developing the package can be installed with
```
pip install -r requirements_dev.txt
```

Make sure that all tests run by tox pass.
