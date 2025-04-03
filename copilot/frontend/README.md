# Streamlit Frontend for Processing Video and Audio Data
Utilizing GPT-4 models to process Video and Audio data

## How to install and run the app
This project was made using [Pipenv](https://github.com/pypa/pipenv) for keeping track of dependencies. First you must have Pipenv installed:
```
pip install pipenv
```
After having Pipenv installed, you should create a virutalenv for the project. To do this, cd into the directory and run the command:
```
pipenv shell
```
Finally, to install the necessary dependencies run:
```
pipenv install
```
By calling ```pipenv install``` you install all of the necessary dependencies within the Pipfile.lock.

All that is needed to run the app now is just run the command below and check your browser instance for the locally hosted app:
```
streamlit run app.py
```

