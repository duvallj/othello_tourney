#!/bin/bash

cd /web/activities/othello
echo "CHDIRED" > z.log
source venv/bin/activate
echo "SOURCED" >> z.log
python3 server.py &> temp.log
echo "ENDED" >> z.log
