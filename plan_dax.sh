#!/bin/bash

DIR=$(cd $(dirname $0) && pwd)

if [ $# -ne 1 ]; then
    echo "Usage: $0 DAXFILE"
    exit 1
fi

DAXFILE=$1

# shared directory on the condor pool
# update accordingly
SHARED_DIR=/lizard/scratch-90-days/adass-demo

# directory where survey catalog files are downloaded
# Look at rc.txt to see where to download the file from
SURVEY_DIR=${DIR}/input/DES/SV

export SHARED_DIR
export DIR
export SURVEY_DIR

# This command tells Pegasus to plan the workflow contained in 
# dax file passed as an argument. The planned workflow will be stored
# in the "submit" directory. The execution # site is "".
# --input-dir tells Pegasus where to find workflow input files.
# --output-dir tells Pegasus where to place workflow output files.
pegasus-plan --conf pegasus.properties \
    --dax $DAXFILE \
    --dir $DIR/submit \
    --output-dir $DIR/output \
    --cleanup none \
    --cluster label \
    --force \
    --sites condorpool \
    --staging-site condorpool \
    -v \
    --submit
