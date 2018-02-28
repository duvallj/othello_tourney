"""
Plan:
use django channel consumer for bg process
have that consumer use this runner to create 2 long running jailed processes beside it
this class will take consumer as an arg in order to send channel api messages
"""

class GameRunner:
    pass