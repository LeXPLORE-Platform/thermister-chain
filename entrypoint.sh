#!/bin/bash

. /opt/conda/etc/profile.d/conda.sh
conda activate lexplore
git config --global --add safe.directory /repository
cd /repository
python -u scripts/pipeline.py "$@"