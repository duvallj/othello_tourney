from django.db import models

from ...gamescheduler.othello_core import BLACK, WHITE, EMPTY, OUTER

WINNER_CHOICES = [
    (BLACK, 'Black'),
    (WHITE, 'White'),
    (OUTER, 'None'),
    (EMPTY, 'Tie'),
]

class PlayerModel(models.Model):
    id = models.CharField(max_length=15, primary_key=True)

class TournamentModel(models.Model):
    tournament_name = models.CharField(max_length=255)
    played_when = models.DateField(auto_now=True)

class SetModel(models.Model):
    black = models.ForeignKey(PlayerModel, on_delete=models.CASCADE,
            null=True, blank=True, related_name='black_sets')
    white = models.ForeignKey(PlayerModel, on_delete=models.CASCADE,
            null=True, blank=True, related_name='white_sets')
    winner = models.CharField(max_length=1, choices=WINNER_CHOICES,
            default=OUTER)
   
    black_from_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True, related_name='to_black_sets')
    white_from_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True, related_name='to_white_sets')
    winner_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True, related_name='winner_from_set')
    loser_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True, related_name='loser_from_set')

    completed = models.BooleanField(default=False)
    played_when = models.DateField(auto_now=True)
    in_tournament = models.ForeignKey(TournamentModel, on_delete=models.CASCADE,
            related_name='sets')

class GameModel(models.Model):
    black = models.ForeignKey(PlayerModel, on_delete=models.CASCADE,
            related_name='black_games')
    white = models.ForeignKey(PlayerModel, on_delete=models.CASCADE,
            related_name='white_games')
    timelimit = models.IntegerField(default=5)
    black_score = models.IntegerField(default=0)
    white_score = models.IntegerField(default=0)
    winner = models.CharField(max_length=1, choices=WINNER_CHOICES,
            default=OUTER)
    by_forfeit = models.BooleanField(default=False)

    completed = models.BooleanField(default=False)
    played_when = models.DateField(auto_now=True)
    in_set = models.ForeignKey(SetModel, on_delete=models.CASCADE, 
            related_name='games')

class MoveModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    board = models.CharField(max_length=100)
    to_move = models.CharField(max_length=1, choices=WINNER_CHOICES[:3])
    in_game = models.ForeignKey(GameModel, on_delete=models.CASCADE,
            related_name='moves')
