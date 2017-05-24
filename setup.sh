#!/bin/bash
echo "Made for a debian distribution, look at source if running other distro"

if [ $# -ne 1 ]
  then
    echo "Must be run with 'web' or 'vm'"
fi

if [ $1 == "web" ]
  then
    sudo apt-get install python3 python3-virtualenv
    virtualenv --python python3 venv
    source venv/bin/activate
    pip install eventlet flask
    { #try
        pip install socketio
    } || { #catch
        sudo apt-get install wget
        wget https://pypi.python.org/packages/d7/83/e3d5bbfe9eaceb4d116dfbf121c7b09069693bf6392a6f741ca6c6030d6b/python-socketio-1.7.4.tar.gz
        tar xvf python-socketio-1.7.4.tar.gz
        cd python-socketio
        python3 setup.py install
    }
fi

if [ $1 == "vm" ]
  then
    sudo apt-get install python3
fi

echo "Done!"
