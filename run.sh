#!/bin/bash

cd /web/activities/othello
source venv/bin/activate
python3 server.py &> temp.log
