#### - does not work on pythonanywhere: !#/bin/bash

echo "Executing dayend.sh"
cd /home/ascgliding/asc
export PYTHONPATH=$HOME/asc
export CONFIG=dayend
echo "Clearing download files"
find $HOME/instance/downloads -daystart -mtime +30
find $HOME/instance/downloads -daystart -mtime +30 -exec rm -f {} \;
echo "Starting dayend in virtual environment"
/home/ascgliding/.virtualenvs/flask310/bin/python /home/ascgliding/asc/dayend.py

