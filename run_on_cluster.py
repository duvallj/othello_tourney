#!/usr/bin/python3

import paramiko

# In case others use a thing that can schedule tasks across
# a bunch of different servers (like slurm)
CMD_PREFIX = 'srun -n 1 '
RUN_AI_PATH = '/home/2019jduvall/run_ai.py'

class RemoteAI:
    def __init__(self, name):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        file = open('private/auth.log','r')
        data = file.read().split('\n')
        username = data[0]
        password = data[1]
        file.close()
        
        client.connect('infosphere', username=username, password=password)
        username, password, data = 'adsfsdafasdfsadfsdafsadfsadfsdafsdafsdafsadfasdfsdaf', \
                                    'asdffdaasdfdfadfdfsdfqwersdfcxvdfqwersadfvczsdafefq', \
                                    'qewraerweqsdadsfsdavcxzvzxcvzcvasdfqwertwqrtfgasdfdas'

        self.client = client
        self.name = name

    def make_connection(self, timelimit):
        self.channel = self.client.get_transport().open_channel('session')
        self.channel.exec_command(CMD_PREFIX+'python3 -u '+RUN_AI_PATH+' '+self.name+' '+str(timelimit))

    def get_move(self, board, player):
        self.channel.sendall(board+' '+player+'\n')
        while not self.channel.recv_stderr_ready(): pass
        result = self.channel.recv_stderr(4)
        if result.isdigit():
            return int(result)
        else:
            return -1

    def kill_remote(self):
        self.channel.sendall('kys\n')

