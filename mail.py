### A simple module to send email
### Reads a template file "email.txt"
### And constructs an email to an othello player
### About an upcoming game

import smtplib
import sys
from email.mime.text import MIMEText


def send_email(player, opp, time):
	""" player is the userID of player1, opp is the userID of player2
	time is the integer number of minutes until the game will begin.
	An email will be sent to player@tjhsst.edu """

	textfile = "email.txt"	
	fp = open(textfile,"r")
	body = fp.read()
	body = body.replace("{PLAYER}", player).replace("{TIME}",  str(time)).replace("{OPPONENT}", opp)

	msg = MIMEText(body)

	msg['Subject'] = 'TEST: Your Othello Game is Soon'
	msg['From'] = "Othello-Server@tjhsst.edu"
	msg['To'] = "%s@tjhsst.edu" % player
	status = 0

	try:
		s = smtplib.SMTP('casey')
		s.send_message(msg)
		s.quit()
		status = 1
	except:
		status = -10

	return status

def send_emails(player, opp, time):
	""" send emails to player and opp about the upcoming game"""
	status1 = send_email(player, opp, time)
	status2 = send_email(opp, player, time)
	return status1+ status2 #negative if error

if __name__ == "__main__":
	send_email("bob1", "kate2", 10)
