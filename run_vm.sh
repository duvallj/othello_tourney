#!/bin/bash

cd /home/othello/othello_tourney
echo "CHDIRED" > z.log
#source venv/bin/activate
#echo "SOURCED" >> z.log
python3 flask_server.py --port 45310 &> temp.log
echo "ENDED" >> z.log
