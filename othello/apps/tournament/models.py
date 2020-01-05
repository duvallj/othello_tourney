from django.db import models

from ...gamescheduler.othello_core import BLACK, WHITE, EMPTY, BORDER

WINNER_CHOICES = [
    (BLACK, 'Black'),
    (WHITE, 'White'),
    (BORDER, 'None'),
    (EMPTY, 'Tie'),
]

class PlayerModel(models.Model):
    name = models.CharField(max_length=15, primary_key=True)

class TournamentModel(models.Model):
    name = models.CharField(max_length=255)
    played_when = models.DateField(auto_now=True)

class SetModel(models.Model):
    black = models.ForeignKey(PlayerModel, on_delete=models.CASCADE,
            null=True, blank=True)
    white = models.ForeignKey(PlayerModel, on_delete=models.CASCADE,
            null=True, blank=True)
    winner = models.CharField(max_length=1, choices=WINNER_CHOICES,
            default=BORDER)
   
    black_from_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True)
    white_from_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True)
    winner_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True)
    loser_set = models.ForeignKey('self', on_delete=models.CASCADE,
            null=True, blank=True)

    completed = models.BooleanField(default=False)
    played_when = models.DateField(auto_now=True)
    in_tournament = models.ForeignKey(TournamentModel, on_delete=models.CASCADE,
            related_name='sets')

class GameModel(models.Model):
    black = models.ForeignKey(PlayerModel, on_delete=models.CASCADE)
    white = models.ForeignKey(PlayerModel, on_delete=models.CASCADE)
    timelimit = models.IntegerField()
    black_score = models.IntegerField()
    white_score = models.IntegerField()
    winner = models.CharField(max_length=1, choices=WINNER_CHOICES,
            default=BORDER)
    by_forfeit = models.BooleanField(default=False)

    played_when = models.DateField(auto_now=True)
    in_set = models.ForeignKey(SetModel, on_delete=models.CASCADE, 
            related_name='games')

class MoveModel(models.Model):
    id = BigAutoField(primary_key=True)
    
    board = models.CharField(max_length=100)
    to_move = models.CharField(max_length=1, choices=WINNER_CHOICES[:3])
    in_game = models.ForeignKey(GameModel, on_delete=models.CASCADE,
            related_name='moves')
