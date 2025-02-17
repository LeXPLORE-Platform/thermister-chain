#!/bin/bash

# Directory containing files
DIR="/home/runnalja/Desktop/Temperature_v3"

# Loop through each file in the directory
for file in "$DIR"/*; do
    # Run Python script and pass the file as an argument
    echo "Processing file: $file"
    python scripts/main.py "$file"
done
