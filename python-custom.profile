include /etc/firejail/disable-mgmt.inc
include /etc/firejail/disable-secret.inc
include /etc/firejail/disable-common.inc
include /etc/firejail/disable-devel.inc
caps.drop all
#net none
#noroot
seccomp
whitelist /root/othello_tourney/anaconda3
whitelist /root/othello_tourney/public
whitelist /root/othello_tourney/run_ai_jailed.py
whitelist /root/othello_tourney/run_ai.py
whitelist /root/othello_tourney/Othello_Core.py
whitelist /root/othello_tourney/othello_admin.py
