import sys
from threading import Thread
from queue import Queue, Empty

def enqueue_stream_helper(stream, q):
    """
    Continuously reads from stream and puts any results into
    the queue `q`
    """
    for line in iter(stream.readline, b''):
        q.put(line)
    stream.close()
    
def get_stream_queue(stream):
    """
    Takes in a stream, and returns a Queue that will return the output from that stream. Starts a background thread as a side effect.
    """
    q = Queue()
    t = Thread(target=enqueue_stream_helper, args=(stream, q))
    t.daemon = True # Dies with the main program
    t.start()
    
    return q