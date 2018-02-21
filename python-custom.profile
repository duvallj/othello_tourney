noblacklist /tmp
include /etc/firejail/disable-mgmt.inc
include /etc/firejail/disable-secret.inc
include /etc/firejail/disable-common.inc
include /etc/firejail/disable-devel.inc
caps.drop all
net none
noroot
seccomp
whitelist /home/othello/www-old/anaconda3
whitelist /home/othello/www-old/public
whitelist /home/othello/www-old/run_ai_jailed.py
whitelist /home/othello/www-old/run_ai.py
whitelist /home/othello/www-old/Othello_Core.py
whitelist /home/othello/www-old/othello_admin.py
whitelist /tmp
