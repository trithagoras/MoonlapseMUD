from django.db import models


class User(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=200)


class Room(models.Model):
    name = models.TextField(max_length=200)
    path = models.TextField(max_length=500)


class Entity(models.Model):
    roomid = models.ForeignKey(Room, on_delete=models.RESTRICT)
    y = models.IntegerField(default=0)
    x = models.IntegerField(default=0)
    char = models.CharField(max_length=1, default='@')
    name = models.CharField(max_length=50)


class Player(models.Model):
    userid = models.ForeignKey(User, on_delete=models.RESTRICT)
    entityid = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    view_radius = models.IntegerField(default=10)
