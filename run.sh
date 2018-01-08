#!/bin/bash

cd /web/activities/othello
echo "CHDIRED" > z.log
#source venv/bin/activate
echo "SOURCED" >> z.log
anaconda3/bin/python3 main_server.py --port $PORT &> temp.log
echo "ENDED" >> z.log
