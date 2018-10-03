#include /etc/firejail/disable-common.inc
#include /etc/firejail/disable-devel.inc
#caps.drop all
#net none
noroot
#seccomp
whitelist /home/jduvall/miniconda3/envs/ot
whitelist /home/jduvall/sr/othello_tourney/run_ai_jailed.py
whitelist /home/jduvall/sr/othello_tourney/othello/settings.py
whitelist /home/jduvall/sr/othello_tourney/students/public/Othello_Core.py
whitelist /home/jduvall/sr/othello_tourney/othello/apps/games/othello_admin.py
whitelist /home/jduvall/sr/othello_tourney/othello/apps/games/othello_core.py
whitelist /home/jduvall/sr/othello_tourney/othello/apps/games/run_ai_utils.py
whitelist /home/jduvall/sr/othello_tourney/othello/apps/games/pipe_utils.py
whitelist /home/jduvall/sr/othello_tourney/othello/apps/games/worker_utils.py
whitelist /usr/var
