from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class AI(models.Model):
    nickname = models.CharField(max_length=100)
    uploaded_date = models.DateTimeField('date uploaded')
    wins = models.IntegerField(deault=0)
    losses = models.IntegerField(default=0)
    ties = models.IntegerField(default=0)
    legacy = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    path = models.CharField(max_length=200)
    author = models.ForeignKey(User)
