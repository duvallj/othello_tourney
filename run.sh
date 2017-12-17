#!/bin/bash

cd /web/activities/othello
echo "CHDIRED" > z.log
source venv/bin/activate
echo "SOURCED" >> z.log
python3 flask_server.py --port $PORT --forward --remotes ovm1.vm.sites.tjhsst.edu &> temp.log
echo "ENDED" >> z.log
