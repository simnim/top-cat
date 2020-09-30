#!/bin/bash -l
# -l to make sure to source .bashrc for our google creds etc

# Figure out where the top_cat script is
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Run it from the correct relative location
$SCRIPT_DIR/top_cat.py -v >> $HOME/top_cat_log 2>&1
