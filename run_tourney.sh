#!/bin/bash

home="/home/othello/tourney"

cd $home
echo "CHDIRED" > z.log
# anaconda3/bin/python3 main_server.py --hostname 0.0.0.0 --port 10770 --jail_begin "firejail --quiet --profile=$home/python-custom.profile --whitelist=$home/students/{NAME} $home/anaconda3/bin/python $home/run_ai_jailed.py"
source $home/anaconda3/bin/activate
python3 tournament_server.py  --game_list lists/round_01.txt --game_output static/games/round_01 --game_delay 5 --hostname 0.0.0.0 --port 10770 --jail_begin "firejail --quiet --profile=$home/python-custom.profile --whitelist=$home/students/{NAME} $home/anaconda3/bin/python $home/run_ai_jailed.py"
# python3 main_server.py --remotes 127.0.0.1=12345 [::1]=23456
echo "ENDED" >> z.log
