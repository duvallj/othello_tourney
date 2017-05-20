#!/usr/bin/python3

import paramiko

def open_connection():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    file = open('private/auth.log','r')
    data = file.read().split('\n')
    username = data[0]
    password = data[1]
    file.close()
    client.connect('infosphere', username=username, password=password)
    username, password, data = '', '', ''
    return client


def get_move(name, cluster_list, cluster_used):
    pass

if __name__=='__main__':
    client = open_connection()
    stdin, stdout, stderr = client.exec_command('echo derp')
    print(stdout.read())
