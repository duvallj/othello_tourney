include /etc/firejail/disable-mgmt.inc
include /etc/firejail/disable-secret.inc
include /etc/firejail/disable-common.inc
include /etc/firejail/disable-devel.inc
caps.drop all
net none
noroot
seccomp
whitelist /home/othello/www/anaconda3
whitelist /home/othello/www/public
whitelist /home/othello/www/run_ai_jailed.py
whitelist /home/othello/www/run_ai.py
whitelist /home/othello/www/Othello_Core.py
whitelist /home/othello/www/othello_admin.py
