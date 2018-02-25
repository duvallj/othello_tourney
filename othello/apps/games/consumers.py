from channels.generic.websocket import WebsocketConsumer

class GameServingConsumer(WebsocketConsumer):
    groups = []
    
    def connect(self):
        pass
        
    def recieve(self, text_data=None, bytes_data=None):
        pass
        
    def disconnect(self, close_data):
        pass