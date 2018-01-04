#!/bin/bash
echo "Made for a debian distribution, look at source if running other distro"

if [ $# -ne 1 ]
then
	echo "You must either put 'web' or 'vm' as an argument"
	exit 1
fi

if [ $1 == "web" ]
then
	sudo apt-get install python3 python3-virtualenv python3-pip
	pip3 install --upgrade python-socketio
	virtualenv --python python3 venv
	source venv/bin/activate
	pip install --upgrade flask flask_security flask_sqlalchemy
    pip install --upgrade https://github.com/italomaia/flask-social/archive/develop.zip
    pip install --upgrade flask_oauthlib
    pip install eventlet==0.17.4
fi

if [ $1 == "vm" ]
then
	sudo apt-get install python3 python3-pip python3-eventlet python3-flask
fi


echo "Done!"
