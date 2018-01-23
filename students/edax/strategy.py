# MIT License
# 
# Copyright (c) 2018 Omkar Kulkarni
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import subprocess
import re
COLS = 'ABCDEFGH'
ROWS = '12345678'
LOCATIONS = {COLS[x % 8] + ROWS[x // 8]: x for x in range(64)}
EMPTY, BLACK, WHITE, OUTER = '.', '@', 'o', '?'
class Strategy:
    def process_board(self, board):
        string = ""
        for x in board:
            if x == EMPTY:
                string += "-"
            elif x == BLACK:
                string += "X"
            elif x == WHITE:
                string += "O"
        return string

    def real_location(self, i):
        return ((i//8)+1)*10+(i%8)+1

    def best_strategy(self, board, player, best_move, still_running):
        with open("/home/othello/www/students/edax/edax_files.obf", "w+") as f:
            print(self.process_board(board), 'OX'[player == BLACK], file=f)
        out = subprocess.check_output(
            "/home/othello/www/students/edax/edax -solve /home/othello/www/students/edax/edax_files.obf -move-time 2 -book-usage off", shell=True, stderr=subprocess.DEVNULL).decode()
        lines = ' '.join(out.splitlines())
        matched = re.search(r"[a-zA-Z]{1}\d{1}", lines)
        loc = matched.group()
        best_move.value = self.real_location(LOCATIONS[loc.upper()])
