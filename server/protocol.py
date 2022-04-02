import random
import math

import django
from django.db.utils import DataError
import rsa
from django.core.exceptions import ObjectDoesNotExist
from django.forms import model_to_dict
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import NetstringReceiver

from collections import deque
from networking import cryptography

from typing import *

from networking import packet
from networking.logger import Log
from server import models, pbkdf2
import maps
import copy

OOB = -32       # Out Of Bounds. All instances with y == OOB are awaiting to be respawned.


def get_dict_delta(before: dict, after: dict) -> dict:
    delta = {'id': before['id']}
    for k, v in after.items():
        if k == 'id':
            continue
        if v != before[k]:
            delta[k] = v

    return delta


def create_dict(model_type: str, model) -> dict:
    """
    Creates recursive dict to replace model_to_dict
    :param model_type: one of ('Instance', 'ContainerItem')
    :param model: a django.model
    :return:
    """
    if model_type == 'Instance':
        instancedict = model_to_dict(model)
        entdict = model_to_dict(model.entity)
        instancedict["entity"] = entdict
        return instancedict

    elif model_type == 'ContainerItem':
        cidict = model_to_dict(model)
        itemdict = model_to_dict(model.item)
        entdict = model_to_dict(model.item.entity)
        cidict["item"] = itemdict
        cidict["item"]["entity"] = entdict
        return cidict


class MoonlapseProtocol(NetstringReceiver):
    def __init__(self, server):
        self.server = server

        # Information specific to the player using this protocol
        self.username = ""
        self.player_instance: Optional[models.InstancedEntity] = None
        self.player_inventory: Optional[models.Inventory] = None
        self.player_info: Optional[models.Player] = None
        self.roommap: Optional[maps.Room] = None
        self.logged_in = False
        self.client_aes_key: Optional[bytes] = None

        self.state = self.GET_ENTRY
        self.actionloop = None

        self.waiting_to_sync = False
        self.outgoing = deque()
        self.incoming = deque()

        self.logger = Log()

        self.visible_instances: Set[models.InstancedEntity] = set()

    def connectionMade(self):
        self.server.connected_protocols.add(self)

        # Send the client the server's public key
        self.outgoing.append(packet.ServerKeyPacket(self.server.public_key.n, self.server.public_key.e))

    def connectionLost(self, reason=connectionDone):
        self.logout(packet.LogoutPacket(self.username))
        self.server.connected_protocols.remove(self)

    def stringReceived(self, string):
        # attempt to decrypt packet
        if self.client_aes_key:
            try:
                string = cryptography.decrypt_aes(string, self.client_aes_key)
            except Exception as e:
                self.debug(f"WARNING: String could not be decrypted with aes, dropping")
                self.debug(str(e))
                return
        else:
            # If we don't have the client's AES key yet, this string must be it (encrypted with RSA)
            try:
                string = cryptography.decrypt_rsa(string, self.server.private_key)
            except Exception as e:
                self.debug(f"WARNING: String could not be decrypted with rsa, dropping")
                self.debug(str(e))
                self.debug(f"String was: {string}")
                return

            self.debug(f"Successfully received string from my client: {string}")
        try:
            p = packet.frombytes(string)
        except Exception as e:
            self.debug(f"WARNING: Packet could not be formed from string, dropping")
            self.debug(str(e))
            self.debug(f"String was: {string}")
            return

        self.debug(f"Received packet from my client {p}")
        self.incoming.append(p)

    def process_packet(self, p: packet.Packet):
        self.state(p)

    def GET_ENTRY(self, p: packet.Packet):
        if isinstance(p, packet.ClientKeyPacket):
            # We have the client's AES key so now we can send some initial data
            self.client_aes_key = str.encode(p.payloads[0].value, 'latin1')  # Refer to docstring for ClientKeyPacket

            # Send the client some initial info it needs to know
            self.outgoing.append(packet.ServerTickRatePacket(self.server.tickrate))
            self.outgoing.append(packet.WelcomePacket(
                """Welcome to MoonlapseMUD\n ,-,-.\n/.( +.\\\n\ {. */\n `-`-'\n     Enjoy your stay ~"""))
        if isinstance(p, packet.LoginPacket):
            self.login_user(p)
        elif isinstance(p, packet.RegisterPacket):
            self.register_user(p)

    def login_user(self, p: packet.LoginPacket):
        username, password = p.payloads[0].value, p.payloads[1].value
        if not models.User.objects.filter(username=username):
            self.outgoing.append(packet.DenyPacket("I don't know anybody by that name"))
            return

        user = models.User.objects.get(username=username)
        player = models.Player.objects.get(user=user)

        if self.server.is_logged_in(player.pk):
            self.outgoing.append(packet.DenyPacket(f"{username} is already inhabiting this realm."))
            return

        if not pbkdf2.verify_password(user.password, password):
            self.outgoing.append(packet.DenyPacket("Incorrect password"))
            return

        # The user exists in the database so retrieve the player and entity objects
        self.username = user.username
        self.player_info = player
        self.player_instance = models.InstancedEntity.objects.get(entity=self.player_info.entity)
        self.player_instance = self.server.instances[self.player_instance.pk]
        self.player_inventory = models.Inventory.objects.get(player=self.player_info)

        self.outgoing.append(packet.OkPacket())
        self.move_rooms(self.player_instance.room.id)

    def register_user(self, p: packet.RegisterPacket):
        username, password = p.payloads[0].value, p.payloads[1].value

        if models.User.objects.filter(username=username):
            self.outgoing.append(packet.DenyPacket("Somebody else already goes by that name"))
            return

        password = pbkdf2.hash_password(password)

        # Save the new user
        user = models.User(username=username, password=password)
        try:
            user.save()
        except DataError as e:
            self.outgoing.append(packet.DenyPacket("Error. Value too long."))
            return

        # Create and save a new entity
        entity = models.Entity(typename='Player', name=username)
        entity.save()

        # Create and save a new instance
        initial_room = models.Room.objects.first()
        if not initial_room:
            self.outgoing.append(packet.DenyPacket("Error. Please try again later."))
            raise ObjectDoesNotExist("Initial room not loaded. Did you run manage.py loaddata data.json?")
        instance = models.InstancedEntity(entity=entity, room=initial_room, y=0, x=0)
        instance.save()

        # Create and save a new player
        player = models.Player(user=user, entity=entity)
        player.save()

        # Create and save a new inventory for the player
        player_inventory = models.Inventory(player=player)
        player_inventory.save()

        # adding instance to server
        self.server.instances[instance.pk] = instance

        self.outgoing.append(packet.OkPacket())

    def logout(self, p: packet.LogoutPacket):
        username = p.payloads[0].value
        if username == self.username:
            # Tell our client it's OK to log out
            self.outgoing.append(packet.OkPacket())

            # tell everyone we're leaving
            if self.player_instance:
                self.broadcast(packet.GoodbyePacket(self.player_instance.pk))

            self.logged_in = False
            self.player_instance = None
            self.player_info = None
            self.roommap = None
            self.username = ""
            self.visible_instances = set()
            self.state = self.GET_ENTRY

            if self.actionloop:
                self.server.remove_deferred(self.actionloop)
                self.actionloop = None

    def PLAY(self, p: packet.Packet):
        if isinstance(p, packet.MovePacket):
            self.move(p)
        elif isinstance(p, packet.ChatPacket):
            self.chat(p)
        elif isinstance(p, packet.LogoutPacket):
            self.logout(p)
        elif isinstance(p, packet.GoodbyePacket):
            self.depart_other(p)
        elif isinstance(p, packet.ServerLogPacket):
            self.outgoing.append(p)
        elif isinstance(p, packet.GrabItemPacket):
            self.grab_item_here()
        elif isinstance(p, packet.DropItemPacket):
            self.drop_item(p)
        elif isinstance(p, packet.WeatherChangePacket):
            self.outgoing.append(p)

    def chat(self, p: packet.ChatPacket):
        """
        Broadcasts a chat message which includes this protocol's connected player name.
        Truncates to 80 characters. Cannot be empty.
        """
        message: str = p.payloads[0].value
        if message.strip() != '':
            message: str = f"{self.player_instance.entity.name} says: {message[:80]}"
            self.broadcast(packet.ServerLogPacket(message), include_self=True)
            self.logger.log(message)

    def add_item_to_inventory(self, item: models.Item, amt: int) -> int:
        """
        adds this item to inventory
        :param item:
        :param amt:
        :require: amt <= item.max_stack_amt
        :return: leftover (if inventory is full)
        """

        inv_items = models.ContainerItem.objects.filter(item=item, container=self.player_inventory)
        for inv_item in inv_items:
            if inv_item.amount == item.max_stack_amt:
                continue
            else:
                leftover = max((inv_item.amount + amt) - item.max_stack_amt, 0)
                inv_item.amount = min(item.max_stack_amt, inv_item.amount + amt)
                inv_item.save()
                self.outgoing.append(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', inv_item)))

                while leftover > 0:
                    # if inventory is full
                    if self.inventory_full():
                        self.outgoing.append(packet.DenyPacket("Your inventory is full"))
                        return leftover

                    new_amt = min(item.max_stack_amt, leftover)
                    new_inv_item = models.ContainerItem(item=item, amount=new_amt, container=self.player_inventory)
                    new_inv_item.save()
                    self.outgoing.append(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', new_inv_item)))
                    leftover -= new_amt
                self.balance_inventory()
                return 0

        # if inventory is full
        if self.inventory_full():
            self.outgoing.append(packet.DenyPacket("Your inventory is full"))
            return amt

        new_inv_item = models.ContainerItem(item=item, amount=amt, container=self.player_inventory)
        new_inv_item.save()
        self.balance_inventory()
        self.outgoing.append(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', new_inv_item)))
        return 0

    def inventory_full(self) -> bool:
        return len(models.ContainerItem.objects.filter(container=self.player_inventory)) == 30

    def kill_instance(self, instance):
        """
        Not 'kill', but flag for respawn. e.g. grabbing item / mining rocks / killing goblin / etc.
        """
        self.broadcast(packet.GoodbyePacket(instance.pk), include_self=True)

        # a respawning instance isn't deleted, just temporarily displaced OOB
        if instance.respawn_time:
            instance.y = OOB
            self.server.add_deferred(self.server.respawn_instance, instance.respawn_time * self.server.tickrate, False, instance.pk)
        else:
            self.server.instances.pop(instance.pk)
            instance.delete()

    def grab_item_here(self):
        # Check if we're standing on an item
        for i in self.visible_instances:
            if i.entity.typename in ("Item", "Pickaxe", "Axe", "Ore", "Logs") \
                    and i.y == self.player_instance.y and i.x == self.player_instance.x:

                di = models.Item.objects.get(entity=i.entity)
                leftover = self.add_item_to_inventory(di, i.amount)

                if leftover:
                    i.amount = leftover
                else:
                    # remove instanced item from visible instances
                    self.kill_instance(i)
                return

        self.outgoing.append(packet.DenyPacket("There is no item here."))

    def balance_inventory(self):
        inventory = models.ContainerItem.objects.filter(container=self.player_inventory)
        uniqueItems = []
        for invItem in inventory:
            to_add = True
            for uniqueItem in uniqueItems:
                if uniqueItem.item.pk == invItem.item.pk:
                    to_add = False
                    break
            if to_add:
                uniqueItems.append(invItem)

        for invItem in uniqueItems:
            stacks = [ itm for itm in inventory if itm.item.pk == invItem.item.pk and itm.amount < invItem.item.max_stack_amt ]
            if not stacks:
                continue
            sum = 0
            for itm in stacks:
                sum += itm.amount
            residue = sum % invItem.item.max_stack_amt
            total_stacks = math.ceil(sum / invItem.item.max_stack_amt)
            stacks_to_remove = len(stacks) - total_stacks
            for i in range(stacks_to_remove):
                stacks[0].delete()
                stacks.pop(0)
            for stack in stacks:
                stack.amount = stack.item.max_stack_amt

            if residue:
                stacks[0].amount = residue

            for stack in stacks:
                stack.save()

        # send player their inventory back


    def drop_item(self, p: packet.DropItemPacket):
        try:
            inv_item = models.ContainerItem.objects.get(id=p.payloads[0].value)
        except:
            return
        amt = p.payloads[1].value

        inv_item.amount -= amt

        # if an instance already exists at this coordinate
        d = self.server.get_instances_at(self.player_instance.room.pk, self.player_instance.y, self.player_instance.x)
        existing_item: Optional[models.InstancedEntity] = None
        for key, inst in d.items():
            if inst.entity.pk == inv_item.item.entity.pk and inst.amount < inv_item.item.max_stack_amt:
                existing_item = inst

        # at this point, there should be either nothing in items, or 1 entry with amount < max_stack_amt
        leftover = amt

        # if there exists a duplicate item on floor already here
        if existing_item is not None:
            leftover = existing_item.amount + amt
            if leftover <= inv_item.item.max_stack_amt:
                existing_item.amount = leftover

                if inv_item.amount <= 0:
                    inv_item.delete()
                else:
                    inv_item.save()
                self.balance_inventory()
                # todo: cancel old deferred to despawn and add new one
                return
            else:
                existing_item.amount = inv_item.item.max_stack_amt
                leftover %= inv_item.item.max_stack_amt

        # create instance and place here
        inst = models.InstancedEntity(entity=inv_item.item.entity,
                                      room=self.player_instance.room, y=self.player_instance.y,
                                      x=self.player_instance.x, amount=leftover)
        pk = random.randint(0, (2**31 - 1))
        while pk in self.server.instances:
            pk = random.randint(0, (2 ** 31 - 1))

        inst.pk = pk     # guaranteed unique due to above check

        self.server.instances[inst.pk] = inst

        # update player inventory item or delete if dropped all
        if inv_item.amount <= 0:
            inv_item.delete()
        else:
            inv_item.save()

        self.balance_inventory()

        # set despawn countdown (2 mins - 120s)
        self.server.add_deferred(self.server.despawn_instance, self.server.tickrate * 120, False, inst.pk)

    def depart_other(self, p: packet.GoodbyePacket):
        ipk: int = p.payloads[0].value
        if ipk not in self.server.instances:
            return

        inst = self.server.instances[ipk]

        if inst in self.visible_instances:
            self.visible_instances.remove(inst)

        if inst.entity.typename == 'Player':
            self.outgoing.append(packet.ServerLogPacket(f"{inst.entity.name} has departed."))

        self.outgoing.append(p)

    def can_gather(self, node: models.ResourceNode) -> bool:
        requirements = {
            'OreNode': 'Pickaxe',
            'TreeNode': 'Axe'
        }

        cis = models.ContainerItem.objects.filter(container=self.player_inventory,
                                                  item__entity__typename=requirements[node.entity.typename])
        if not cis:
            self.outgoing.append(packet.ServerLogPacket(f"You do not have a {requirements[node.entity.typename]}."))
            return False

        if self.inventory_full():
            self.outgoing.append(packet.DenyPacket(f"Your inventory is full."))
            return False

        return True

    def start_gather(self, instance: models.InstancedEntity):
        node = models.ResourceNode.objects.get(entity=instance.entity)

        # check if player has required level and item (e.g. pickaxe)
        if not self.can_gather(node):
            return

        if node.entity.typename == "OreNode":
            self.outgoing.append(packet.ServerLogPacket("You begin to mine at the rocks."))
        elif node.entity.typename == "TreeNode":
            self.outgoing.append(packet.ServerLogPacket("You begin to chop at the tree."))

        if self.actionloop:
            self.server.remove_deferred(self.actionloop)
            self.actionloop = None
        self.actionloop = self.server.add_deferred(self.attempt_gather, self.server.tickrate, True, instance, node)

    def attempt_gather(self, instance: models.InstancedEntity, node: models.ResourceNode):
        # if node has already been killed (by other player)
        if instance.y == OOB:
            if self.actionloop:
                self.server.remove_deferred(self.actionloop)
                self.actionloop = None
            return

        if not self.can_gather(node):
            return

        # change change based on difficulty
        if random.randint(0, 5) == 0:
            # success
            if self.actionloop:
                self.server.remove_deferred(self.actionloop)
                self.actionloop = None

            dropitems = set(models.DropTableItem.objects.filter(droptable=node.droptable))
            for itm in dropitems:
                if random.randint(1, itm.chance) == 1:
                    amt = random.randint(itm.min_amt, itm.max_amt)
                    item = itm.item
                    fail = self.add_item_to_inventory(item, amt)
                    if fail == 0:
                        self.outgoing.append(packet.ServerLogPacket(f"You acquire {amt} {item.entity.name}."))

            self.kill_instance(instance)
        else:
            # fail
            self.outgoing.append(packet.ServerLogPacket(f"You continue gathering."))
            pass
        pass

    def move(self, p: packet.MovePacket):
        """
        Updates this protocol's player's position and sends the player back to all
        clients connected to the server.
        """

        if self.actionloop:
            self.server.remove_deferred(self.actionloop)
            self.actionloop = None

        # Calculate the desired destination
        desired_y = self.player_instance.y
        desired_x = self.player_instance.x

        if isinstance(p, packet.MoveUpPacket):
            desired_y -= 1
        elif isinstance(p, packet.MoveRightPacket):
            desired_x += 1
        elif isinstance(p, packet.MoveDownPacket):
            desired_y += 1
        elif isinstance(p, packet.MoveLeftPacket):
            desired_x -= 1

        # Check if we're going to land on a portal
        for instance in self.visible_instances:
            if instance.entity.typename == "Portal" and instance.y == desired_y and instance.x == desired_x:
                portal = models.Portal.objects.get(entity=instance.entity)
                desired_y = portal.linkedy
                desired_x = portal.linkedx
                self.player_instance.y = desired_y
                self.player_instance.x = desired_x
                if self.player_instance.room != portal.linkedroom:
                    self.move_rooms(portal.linkedroom.id)
                    return

            elif instance.entity.typename in ("OreNode", "TreeNode") and instance.y == desired_y and instance.x == desired_x:
                self.start_gather(instance)
                return

        if (0 <= desired_y < self.roommap.height and 0 <= desired_x < self.roommap.width) and (self.roommap.at('solid', desired_y, desired_x) == maps.NOTHING):
            self.player_instance.y = desired_y
            self.player_instance.x = desired_x

            for proto in self.server.protocols_in_room(self.player_instance.room_id):
                proto.process_visible_instances()
        else:
            self.outgoing.append(packet.DenyPacket("Can't move there"))

    def move_rooms(self, dest_roomid: Optional[int]):
        print(f"\nmove_rooms(dest_roomid={dest_roomid})\n")

        if self.logged_in:
            # Tell people in the current (old) room we are leaving
            self.broadcast(packet.GoodbyePacket(self.player_instance.pk))

            # Reset visible entities (so things don't "follow" us between rooms)
            self.visible_instances = set()

        self.logged_in = True

        # Tell our client we're ready to switch rooms so it can reinitialise itself and wait for data again.
        self.outgoing.append(packet.MoveRoomsPacket(dest_roomid))

        # Move db instance to the new room
        self.player_instance.room_id = dest_roomid

        room = self.player_instance.room
        self.roommap = maps.Room(room.pk, room.name, room.file_name)

        self.outgoing.append(packet.OkPacket())
        self.establish_player_in_room()

    def establish_player_in_room(self):
        self.outgoing.append(packet.ServerModelPacket('Room', model_to_dict(self.player_instance.room)))
        self.sync_player_instance()

        playerdict = model_to_dict(self.player_info)
        playerdict["entity"] = model_to_dict(self.player_info.entity)
        self.outgoing.append(packet.ServerModelPacket('Player', playerdict))

        self.outgoing.append(packet.WeatherChangePacket(self.server.weather))

        # send inventory to player
        if self.state == self.GET_ENTRY:    # Only send on initial login
            items = models.ContainerItem.objects.filter(container=self.player_inventory)
            for ci in items:
                self.outgoing.append(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', ci)))

        self.state = self.PLAY
        self.broadcast(packet.ServerLogPacket(f"{self.username} has arrived."))

        # Tell other players in view that we have arrived
        for proto in self.server.protocols_in_room(self.player_instance.room_id):
            proto.process_visible_instances()

    def process_visible_instances(self):
        """
        Say goodbye to old entities no longer in view and process the new and still-existing entities in view
        """
        prev_in_view = copy.deepcopy(self.visible_instances)

        instances_in_view = set()
        for instance in self.server.instances_in_room(self.player_instance.room_id).values():
            if self.coord_in_view(instance.y, instance.x):

                # We don't need to process ourselves. This is done on a less frequent server tick
                # See mlserver.py sync_player_instances
                if instance != self.player_instance:
                    instances_in_view.add(instance)

        # removing logged out players from view
        for instance in list(instances_in_view):  # Convert to list to avoid "Set changed size during iteration"
            if instance.entity.typename == 'Player':
                proto = self.server.get_proto_by_id(instance.entity.pk)
                if not proto or not proto.logged_in:
                    instances_in_view.remove(instance)

        self.visible_instances = copy.deepcopy(instances_in_view)

        # Say goodbye to the instances which are no longer in our view
        just_left_view: Set[models.InstancedEntity] = prev_in_view.difference(self.visible_instances)
        for instance in just_left_view:
            self.outgoing.append(packet.GoodbyePacket(instance.pk))

        # Send models for all instances brand new to the view
        new_to_view: Set[models.InstancedEntity] = self.visible_instances.difference(prev_in_view)
        for instance in new_to_view:
            self.outgoing.append(packet.ServerModelPacket('Instance', create_dict('Instance', instance)))

        # Now send deltas for instances which were already in the view but have changed in some way
        already_in_view: Set[models.InstancedEntity] = prev_in_view & instances_in_view
        for current_inst in already_in_view:
            c_inst_dict = create_dict('Instance', current_inst)

            p_inst_dict = {}
            for prev_inst in prev_in_view:
                if prev_inst.id == current_inst.id:
                    p_inst_dict = create_dict('Instance', prev_inst)
            
            delta_dict = get_dict_delta(p_inst_dict, c_inst_dict)
            if len(delta_dict) > 1: # If more than just the IDs differ
                self.outgoing.append(packet.ServerModelPacket('Instance', delta_dict))

    def tick(self):
        # process the next packet in the incoming queue
        if len(self.incoming) > 0:
            self.process_packet(self.incoming.popleft())
            self.debug(f"{len(self.incoming)} more packets in the queue to be processed in future ticks")

        # Sync if we were waiting for the incoming queue to empty before syncing
        if self.waiting_to_sync and len(self.incoming) <= 0:
            self.sync_player_instance()
            self.waiting_to_sync = False
            self.debug(f"Just completed an outstanding sync request")

        # send all packets in queue back to client in order
        while len(self.outgoing) > 0:
            self.send_packet(self.outgoing.popleft())

    def sync_player_instance(self):
        # Don't sync the player until we have processed all incoming packets
        if len(self.incoming) > 0:
            # TODO: Instead of this way, perhaps insert a special SyncRequest packet into the incoming queue which can be processed.
            # Otherwise, if the player keeps spamming keys, the sync might have to wait a really long time as the incoming queue keeps getting bigger
            self.waiting_to_sync = True
            self.debug(f"Wanted to sync, but need to empty incoming queue first. Need to wait for {len(self.incoming)} packets to be processed first.")
        else:
            self.outgoing.append(packet.ServerModelPacket('Instance', create_dict('Instance', self.player_instance)))

    def send_packet(self, p: packet.Packet):
        """
        Sends a packet to this protocol's client.
        Call this to communicate information back to the game client application.
        """
        message: bytes = p.tobytes()

        if isinstance(p, packet.ServerKeyPacket):  # Don't encrypt the server's public key
            self.sendString(message)
            self.debug(f"Sent the server's public key to my client")

        elif self.client_aes_key:
            try:
                message = cryptography.encrypt_aes(message, self.client_aes_key)
                self.sendString(message)
                self.debug(f"Sent data to my client: {p.tobytes()}")
            except Exception as e:
                self.debug(f"FATAL: Couldn't encrypt packet {p} for sending. Error was {e}. Returning.")

    def broadcast(self, p: packet.Packet, include_self=False):
        excluding = []
        if not include_self:
            excluding.append(self)
        self.server.broadcast_to_room(p, self.player_instance.room.pk, excluding=excluding)

    def debug(self, message: str):
        print(f"[{self.username if self.username else None}]"
              f"[{self.state.__name__}]"
              f"[{self.player_instance.room.name if self.player_instance else None}]: {message}")

    def coord_in_view(self, y: int, x: int) -> bool:
        yview = self.player_instance.y - 10, self.player_instance.y + 10
        xview = self.player_instance.x - 10, self.player_instance.x + 10

        return yview[0] <= y <= yview[1] and xview[0] <= x <= xview[1]
