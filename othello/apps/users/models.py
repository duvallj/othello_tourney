from django.db import models
from django.core import validators
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager as DjangoUserManager

from social_django.utils import load_strategy

import json
import requests

class UserManager(DjangoUserManager):
    pass


class User(AbstractBaseUser, PermissionsMixin):
    id = models.PositiveIntegerField(primary_key=True, validators=[validators.MinValueValidator(1000)])
    service = models.BooleanField(default=False)
    username = models.CharField(unique=True, max_length=32)
    full_name = models.CharField(max_length=60)
    email = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    github_token = models.CharField(max_length=40, blank=True)
    access_token = models.CharField(max_length=64, blank=True, null=True)
    USERNAME_FIELD = 'username'

    objects = UserManager()

    @property
    def is_staff(self):
        return self.staff or self.is_superuser

    @is_staff.setter
    def is_staff(self, value):
        if isinstance(value, bool):
            self.staff = value
        else:
            self.staff = False

    @property
    def short_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return self.full_name

    def get_social_auth(self):
        return self.social_auth.get(provider='ion')
        
    def api_request(self, url, params={}, refresh=True):
        s = self.get_social_auth()
        params.update({"format": "json"})
        params.update({"access_token": s.access_token})
        r = requests.get("https://ion.tjhsst.edu/api/{}".format(url), params=params)
        if r.status_code == 401:
            if refresh:
                try:
                    self.get_social_auth().refresh_token(load_strategy())
                except Exception:
                    client.captureException()
                return self.api_request(url, params, False)
            else:
                client.captureMessage("Ion API Request Failure: {} {}".format(r.status_code, r.json()))
        return r.json()