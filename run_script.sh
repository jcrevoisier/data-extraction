#!/bin/bash

# Activate the virtual environment
source /home/bachatanow_app/data-extraction/venv/bin/activate

# Print environment information
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Python path: $(which python)"

# Run the script and capture output
python /home/bachatanow_app/data-extraction/main.py 2>&1 | tee /home/bachatanow_app/data-extraction/script_output.log

# Deactivate the virtual environment
deactivate