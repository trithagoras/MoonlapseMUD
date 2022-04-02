from django.db import models


class User(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=200)


class Room(models.Model):
    name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=200)


class Entity(models.Model):
    typename = models.CharField(null=False, max_length=50)
    name = models.CharField(max_length=50, default=typename)


class Item(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    value = models.IntegerField(null=True, default=1)
    max_stack_amt = models.IntegerField(null=True, default=2147483647)


class DropTable(models.Model):
    pass


class DropTableItem(models.Model):
    droptable = models.ForeignKey(DropTable, on_delete=models.RESTRICT)
    item = models.ForeignKey(Item, on_delete=models.RESTRICT)
    min_amt = models.IntegerField(null=True, default=1)
    max_amt = models.IntegerField(null=True, default=1)
    chance = models.IntegerField(null=True, default=1)


class ResourceNode(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    droptable = models.ForeignKey(DropTable, on_delete=models.RESTRICT)
    req_lvl = models.IntegerField(null=True, default=1)
    xp_given = models.IntegerField(null=True, default=5)


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)


class Container(models.Model):
    pass


class Inventory(Container):
    player=models.ForeignKey(Player, on_delete=models.RESTRICT)


class ContainerItem(models.Model):
    container = models.ForeignKey(Container, on_delete=models.RESTRICT)
    item = models.ForeignKey(Item, on_delete=models.RESTRICT)
    amount = models.IntegerField(null=True, default=1)


class Portal(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    linkedy = models.IntegerField(null=True, default=None)
    linkedx = models.IntegerField(null=True, default=None)
    linkedroom = models.ForeignKey(Room, on_delete=models.RESTRICT)


class InstancedEntity(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.RESTRICT)
    room = models.ForeignKey(Room, on_delete=models.RESTRICT)
    y = models.IntegerField(null=True, default=None)
    x = models.IntegerField(null=True, default=None)
    amount = models.IntegerField(null=True, default=1)
    respawn_time = models.IntegerField(null=True, default=0)
