#!/bin/bash

cd /web/activities/othello
echo "CHDIRED" > z.log
source venv/bin/activate
echo "SOURCED" >> z.log
python3 flask_server.py --port $PORT --remotes ovm1.vm.sites.tjhsst.edu:45310 &> temp.log
echo "ENDED" >> z.log
