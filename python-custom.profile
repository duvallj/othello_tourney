include /etc/firejail/disable-mgmt.inc
include /etc/firejail/disable-secret.inc
include /etc/firejail/disable-common.inc
include /etc/firejail/disable-devel.inc
caps.drop all
#net none
noroot
seccomp
whitelist /home/othello/tourney/anaconda3
whitelist /home/othello/tourney/public
whitelist /home/othello/tourney/run_ai_jailed.py
whitelist /home/othello/tourney/run_ai.py
whitelist /home/othello/tourney/Othello_Core.py
whitelist /home/othello/tourney/othello_admin.py
