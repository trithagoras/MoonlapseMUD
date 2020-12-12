from django.db import models
from django.contrib.postgres.fields import ArrayField


class User(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=200)


class Room(models.Model):
    name = models.CharField(max_length=200)
    ground_data = ArrayField(models.TextField(max_length=None))
    solid_data = ArrayField(models.TextField(max_length=None))
    roof_data = ArrayField(models.TextField(max_length=None))
    height = models.IntegerField()
    width = models.IntegerField()


class Entity(models.Model):
    room = models.ForeignKey(Room, on_delete=models.RESTRICT)
    y = models.IntegerField(null=True, default=None)
    x = models.IntegerField(null=True, default=None)
    char = models.CharField(max_length=1, default='@')
    name = models.CharField(max_length=50)


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    view_radius = models.IntegerField(default=10)
