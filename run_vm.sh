#!/bin/bash

cd /home/othello/www
echo "CHDIRED" > z.log
#source venv/bin/activate
#echo "SOURCED" >> z.log
anaconda3/bin/python3 main_server.py --port 45310  --serve_ai_only &> temp.log
# python3 main_server.py --hostname [::1] --port 23456 --serve_ai_only --jail_begin "python3 /home/othello/www/run_ai_jailed.py"
echo "ENDED" >> z.log
