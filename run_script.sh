#!/bin/bash

echo "Script started at $(date)"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"

VENV_PATH="/home/bachatanow_app/data-extraction/venv"
PYTHON="$VENV_PATH/bin/python"

echo "Activating virtual environment"
source "$VENV_PATH/bin/activate"
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

echo "Virtual environment activated"
echo "Python version: $($PYTHON --version)"
echo "Python path: $PYTHON"

echo "Running main script"
$PYTHON /home/bachatanow_app/data-extraction/main.py

echo "Script finished at $(date)"

deactivate