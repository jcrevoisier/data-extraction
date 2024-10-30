#!/bin/bash

# Activate virtual environment
source ~/data-extraction/venv/bin/activate

# Load environment variables
set -a
source .env
set +a

# Run the Python script
python main.py

# Deactivate virtual environment
deactivate