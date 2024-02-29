#!/bin/bash
export POETRY_HOME=poetry
python3 -m venv $POETRY_HOME
$POETRY_HOME/bin/pip install poetry==1.2.0
export PATH=${PATH}:$POETRY_HOME/bin
