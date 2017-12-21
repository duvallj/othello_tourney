#!/bin/bash
echo "Made for a debian distribution, look at source if running other distro"

sudo apt-get install python3 python3-virtualenv
virtualenv --python python3 venv
source venv/bin/activate
pip install eventlet flask
{ #try
    pip install socketio
} || { #catch
    sudo apt-get install wget
    wget https://pypi.python.org/packages/58/a9/52af6a7ad0805977afc838ed394f8d26d078ef61e8c1bdd632801c58ef3a/python-socketio-1.8.4.tar.gz#md5=9de73990f6c32c701278c01b0fa1a0c3
    tar xvf python-socketio-1.8.4.tar.gz
    cd python-socketio
    python3 setup.py install
}

echo "Done!"
