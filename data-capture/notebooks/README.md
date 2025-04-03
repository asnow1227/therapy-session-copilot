# Jupyter Lab for Displaying Potential using Pose Estimation
Utilizing an Open-Source pose estimation model running locally to get the pose of a user and track their location.
This can eventually be used to track where the person is looking, their body language, and get emotion.

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

All that is needed to run the app now is just run the command below and check your browser instance for the Jupyter lab:
```
jupyter lab
```


