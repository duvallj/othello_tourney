include /etc/firejail/disable-mgmt.inc
include /etc/firejail/disable-secret.inc
include /etc/firejail/disable-common.inc
include /etc/firejail/disable-devel.inc
caps.drop all
#net none
noroot
seccomp
whitelist /home/othello/anaconda3/envs/django
whitelist /home/othello/django/run_ai_jailed.py
whitelist /home/othello/django/othello/settings.py
whitelist /home/othello/django/students/public/Othello_Core.py
whitelist /home/othello/django/othello/apps/games/othello_admin.py
whitelist /home/othello/django/othello/apps/games/othello_core.py
whitelist /home/othello/django/othello/apps/games/run_ai_utils.py
whitelist /home/othello/django/othello/apps/games/pipe_utils.py
whitelist /home/othello/django/othello/apps/games/worker_utils.py
