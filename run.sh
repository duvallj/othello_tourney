#!/bin/bash

cd /web/activities/othello
python3 -c 'import os;os.chown("hey",33560943,10770)'
echo "CHDIRED" > z.log
#source venv/bin/activate
echo "SOURCED" >> z.log
anaconda3/bin/python3 main_server.py --port $PORT &> temp.log
echo "ENDED" >> z.log
