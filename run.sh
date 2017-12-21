#!/bin/bash

cd /web/activities/othello
echo "CHDIRED" > z.log
source venv/bin/activate
echo "SOURCED" >> z.log
python3 flask_server.py --port $PORT --remotes [2001:468:cc0:1600:0:bff:9951:ac5b]=45310 &> temp.log
echo "ENDED" >> z.log
