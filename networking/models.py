from django.db import models


class User(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=200)


class Room(models.Model):
    name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=200)


class Entity(models.Model):
    room = models.ForeignKey(Room, on_delete=models.RESTRICT)
    y = models.IntegerField(null=True, default=None)
    x = models.IntegerField(null=True, default=None)
    char = models.CharField(max_length=1, default='@')
    typename = models.CharField(null=False, max_length=50)
    name = models.CharField(max_length=50, default=typename)


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    view_radius = models.IntegerField(default=10)


class Portal(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    linkedy = models.IntegerField(null=True, default=None)
    linkedx = models.IntegerField(null=True, default=None)
    linkedroom = models.ForeignKey(Room, on_delete=models.RESTRICT)
