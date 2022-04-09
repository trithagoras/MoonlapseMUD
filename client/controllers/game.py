import curses
import curses.ascii
import math
from typing import *

import maps
from client.controllers.controller import Controller
from client.views.gameview import GameView
from networking import packet
from networking.logger import Log
from client.controllers.widgets import TextField
from client.controllers import keybindings


# ContainerItem = {'id': 194, 'container': 2, 'item': {'id': 7, 'entity': {'id': 13, 'typename': 'Item', 'name': 'Banana'},
#                       'value': 1, 'max_stack_amt': 4}, 'amount': 4}
class Model:
    def __init__(self, attr: dict):
        self.id = 0
        for k, v in attr.items():
            setattr(self, k, v)

    def update(self, delta: dict):
        if delta['id'] != self.id:
            raise ValueError("Cannot change model's ID")
        for k, v in delta.items():
            setattr(self, k, v)

    def haskey(self, key: str) -> bool:
        return key in self.__dict__

    def __getitem__(self, item):
        return self.__dict__[item]


class Context:
    NORMAL = 0
    LOGOUT = 1
    MOVE_ROOMS = 2


class State:
    NORMAL = 0
    LOOKING = 1
    GRABBING_ITEM = 2
    IN_BANK = 3
    SELECTING_TRADE_PARTNER = 4


class Game(Controller):
    def __init__(self, cs):
        super().__init__(cs)
        self.chatbox = TextField(self, title="Say: ", max_length=80)

        self.visible_instances = set()
        self.player_info = None  # id, entity, inventory
        self.player_instance = None  # id, entity, room_id, y, x
        self.inventory = {}     # inv_item.id : {inv_item_id, item, amount}
        self.bank = {}          # bank_item.id : {bank_item_id, item, amount}
        self.inventory_index = 0    # cursor position in inventory
        self.bank_index = 0     # cursor position in bank
        self.room = None

        self.context = Context.NORMAL
        self.state = State.NORMAL

        self.look_cursor_y = 0
        self.look_cursor_x = 0

        self.weather = "Clear"

        self.logger = Log()
        self.quicklog = ""      # line that appears above win1

        self.view = GameView(self)

    def ready(self):
        return False not in [bool(data) for data in (self.player_info, self.player_instance, self.room)]

    def process_packet(self, p) -> bool:
        if isinstance(p, packet.ServerModelPacket):
            if not self.ready():
                self.initialise_my_models(p.payloads[0].value, p.payloads[1].value)
            else:
                self.process_model(p.payloads[0].value, p.payloads[1].value)

        elif isinstance(p, packet.GoodbyePacket):
            # Some instance has been removed from room (item picked up, player logged out, etc.)
            entityid: int = p.payloads[0].value
            departed = next((e for e in self.visible_instances if e['id'] == entityid), None)
            if departed:
                self.visible_instances.remove(departed)

        elif isinstance(p, packet.WeatherChangePacket):
            self.weather = p.payloads[0].value

        elif isinstance(p, packet.MoveRoomsPacket):
            self.context = Context.MOVE_ROOMS

        elif isinstance(p, packet.ServerLogPacket):
            self.logger.log(p.payloads[0].value)

        elif isinstance(p, packet.OkPacket):
            if self.context == Context.LOGOUT:
                self.cs.change_controller("MainMenu")
            elif self.context == Context.MOVE_ROOMS:
                self.reinitialize()
                self.context = Context.NORMAL
            else:
                pass
        elif isinstance(p, packet.DenyPacket):
            self.quicklog = p.payloads[0].value
            if self.state == State.GRABBING_ITEM:
                self.state = State.NORMAL
        else:
            return False

        return True

    def initialise_my_models(self, mtype: str, data: dict):
        if mtype == 'Room':
            self.room = maps.Room(data['id'], data['name'], data['file_name'])
        elif mtype == 'Instance':
            self.player_instance = Model(data)
        elif mtype == 'Player':
            self.player_info = Model(data)

    def process_model(self, mtype: str, data: dict):
        if mtype == 'Instance':
            instance = Model(data)
            visible_instance = next((e for e in self.visible_instances if e['id'] == instance['id']), None)
            if visible_instance:  # If the incoming entity is already visible to us, update it
                visible_instance.update(data)
                # If the incoming entity is ours, update it
                if instance.id == self.player_instance['id']:
                    self.player_instance.update(data)
            else:  # If not visible already, add to visible list (it is only ever sent to us if it's in view)
                self.visible_instances.add(instance)

        elif mtype in ("InventoryItem", "BankItem"):
            c_item = Model(data)
            c_item_id = c_item['id']
            amt = c_item['amount']

            if mtype == 'InventoryItem':
                # Add container item to inventory
                if c_item_id in self.inventory:
                    amt -= self.inventory[c_item_id]['amount']

                self.inventory[c_item_id] = c_item

                if self.state == State.GRABBING_ITEM:
                    self.quicklog = f"You pick up {amt} {c_item['item']['entity']['name']}."
                    self.state = State.NORMAL

                self.balance_container(self.inventory)

            elif mtype == 'BankItem':
                # Add container item to bank
                if c_item_id in self.bank:
                    amt -= self.bank[c_item_id]['amount']
                self.bank[c_item_id] = c_item
                self.balance_container(self.bank)

    # ContainerItem = {'id': 194, 'player': 2, 'item': {'id': 7, 'entity': {'id': 13, 'typename': 'Item', 'name': 'Banana'},
    #                       'value': 1, 'max_stack_amt': 4}, 'amount': 4}

    def balance_container(self, container: dict): # Container must be same structure as self.bank or self.inventory
        unique_cnt_items = []
        for cntItem in container.values():
            to_add = True
            for unique_cnt_item in unique_cnt_items:
                if unique_cnt_item['item']['id'] == cntItem['item']['id']:
                    to_add = False
                    break
            if to_add:
                unique_cnt_items.append(cntItem)

        for cntItem in unique_cnt_items:
            stacks = [ itm for itm in container.values() if itm['item']['id'] == cntItem['item']['id'] and itm['amount'] < cntItem['item']['max_stack_amt'] ]
            if not stacks:
                continue
            sum = 0
            for itm in stacks:
                sum += itm['amount']
            residue = sum % cntItem['item']['max_stack_amt']
            total_stacks = math.ceil(sum / cntItem['item']['max_stack_amt'])
            stacks_to_remove = len(stacks) - total_stacks
            for i in range(stacks_to_remove):
                container.pop(stacks[0]['id'])
                stacks.pop(0)
            for stack in stacks:
                setattr(stack, 'amount', stack['item']['max_stack_amt'])

            if residue:
                setattr(stacks[0], 'amount', residue)

    def update(self):
        if self.state in (State.LOOKING, State.SELECTING_TRADE_PARTNER):
            self.quicklog = ""
            cpos = self.look_cursor_y, self.look_cursor_x
            for instance in self.visible_instances:
                pos = instance['y'], instance['x']
                if cpos == pos:
                    if instance.haskey('amount') and instance['amount'] > 1:
                        self.quicklog += f"{instance['amount']}x "
                    self.quicklog += f"{instance['entity']['name']}"
                    return
            

    def process_input(self, key: int):
        super().process_input(key)
        
        if self.process_global_input(key):
            return

        # input state machine
        if self.state == State.NORMAL:
            self.process_normal_input(key)
        elif self.state == State.LOOKING:
            self.process_look_input(key)
        elif self.state == State.SELECTING_TRADE_PARTNER:
            self.process_selecting_trade_partner_input(key)

    def process_global_input(self, key: int) -> bool:
        if self.chatbox.selected:
            if keybindings.enter(key):
                self.send_chat(self.chatbox.value)
                self.chatbox.value = ""
                self.chatbox.cursor = 0
                self.view.chat_scroll = 0
            self.chatbox.process_input(key)
            return True
        elif keybindings.escape(key):
            if self.state in (State.LOOKING, State.IN_BANK, State.SELECTING_TRADE_PARTNER):
                self.state = State.NORMAL
        elif keybindings.enter(key) and self.state != State.SELECTING_TRADE_PARTNER:
            self.chatbox.select()
        elif key == ord('q'):
            self.cs.ns.send_packet(packet.LogoutPacket(self.cs.ns.username))
            self.context = Context.LOGOUT
        elif key == ord('k'):
            if self.state != State.LOOKING:
                self.state = State.LOOKING
                self.look_cursor_y = self.player_instance['y']
                self.look_cursor_x = self.player_instance['x']
            else:
                self.state = State.NORMAL
        elif key == ord('t'):
            if self.state != State.SELECTING_TRADE_PARTNER:
                self.state = State.SELECTING_TRADE_PARTNER
                self.look_cursor_y = self.player_instance['y']
                self.look_cursor_x = self.player_instance['x']
            else:
                self.state = State.NORMAL
        elif key == ord('['):
            self.inventory_index = max(self.inventory_index - 1, 15 * self.view.inventory_page)
        elif key == ord(']'):
            self.inventory_index = min(self.inventory_index + 1, min(15 * self.view.inventory_page + 14, len(self.inventory) - 1))
        elif key == ord('<'):
            self.view.inventory_page = max(0, self.view.inventory_page - 1)
            self.inventory_index = 15 * self.view.inventory_page
        elif key == ord('>'):
            if len(self.inventory) > 15 * (self.view.inventory_page + 1):
                self.view.inventory_page += 1
                self.inventory_index = 15 * self.view.inventory_page
        elif key == ord('D'):
            # Drop item on ground, or deposity in bank
            if len(self.inventory) > 0:
                # drop-all
                inv = []
                for key in self.inventory:
                    inv.append(key)

                iid = inv[self.inventory_index]
                amt = self.inventory[iid]['amount']
                if self.state == State.IN_BANK:
                    self.cs.ns.send_packet(packet.DepositItemPacket(iid, amt))
                else:
                    self.cs.ns.send_packet(packet.DropItemPacket(iid, amt))
                self.inventory.pop(iid)

                # need to account for all pages. index past the last item in list ==> index == last item in list
                if self.inventory_index >= len(inv) - 1:
                    self.inventory_index = max(0, len(inv) - 2)

                # go back a page if we've dropped the last item on the last page
                while 15 * self.view.inventory_page >= len(self.inventory) and len(self.inventory) != 0:
                    self.view.inventory_page = max(0, self.view.inventory_page - 1)

                self.balance_container(self.inventory)
        elif key == ord('d'):
            if len(self.inventory) > 0:
                # drop/deposit single
                inv = []
                for key in self.inventory:
                    inv.append(key)

                iid = inv[self.inventory_index]
                amt = self.inventory[iid]['amount']
                if self.state == State.IN_BANK:
                    self.cs.ns.send_packet(packet.DepositItemPacket(iid, 1))
                else:
                    self.cs.ns.send_packet(packet.DropItemPacket(iid, 1))

                if amt == 1:
                    self.inventory.pop(iid)

                    # need to account for all pages. index past the last item in list ==> index == last item in list
                    if self.inventory_index >= len(inv) - 1:
                        self.inventory_index = max(0, len(inv) - 2)

                    # go back a page if we've dropped the last item on the last page
                    while 15 * self.view.inventory_page >= len(self.inventory) and len(self.inventory) != 0:
                        self.view.inventory_page = max(0, self.view.inventory_page - 1)
                else:
                    setattr(self.inventory[iid], 'amount', self.inventory[iid]['amount'] - 1)

                self.balance_container(self.inventory)
        elif key == ord('1'):
            self.view.focused_win = self.view.win1
        elif key == ord('2'):
            self.view.focused_win = self.view.win2
        elif key == ord('3'):
            self.view.focused_win = self.view.win3

        elif self.view.focused_win == self.view.win3:
            if key == curses.KEY_DOWN and self.view.chat_scroll > 0:
                self.view.chat_scroll -= 1
            elif key == curses.KEY_UP and self.view.chat_scroll < self.view.times_logged - self.view.win3.height + self.view.chatwin.height:
                self.view.chat_scroll += 1
        
        elif self.state == State.IN_BANK:
            if key == curses.KEY_UP:
                self.bank_index = max(self.bank_index - 1, 15 * self.view.bank_page)
            elif key == curses.KEY_DOWN:
                self.bank_index = min(self.bank_index + 1, min(15 * self.view.bank_page + 14, len(self.bank) - 1))
            elif key == curses.KEY_LEFT:
                self.view.bank_page = max(0, self.view.bank_page - 1)
                self.bank_index = 15 * self.view.bank_page
            elif key == curses.KEY_RIGHT:
                if len(self.bank) > 15 * (self.view.bank_page + 1):
                    self.view.bank_page += 1
                    self.bank_index = 15 * self.view.bank_page
            elif key == ord('w'):
                if len(self.bank) > 0:
                    # withdraw single
                    bank = []
                    for key in self.bank:
                        bank.append(key)

                    iid = bank[self.bank_index]
                    amt = self.bank[iid]['amount']
                    self.cs.ns.send_packet(packet.WithdrawItemPacket(iid, 1))

                    if amt <= 1:
                        self.bank.pop(iid)

                        # need to account for all pages. index past the last item in list ==> index == last item in list
                        if self.bank_index >= len(bank) - 1:
                            self.bank_index = max(0, len(bank) - 2)

                        # go back a page if we've withdrawn the last item on the last page
                        while 15 * self.view.bank_page >= len(self.bank) and len(self.bank) != 0:
                            self.view.bank_page = max(0, self.view.bank_page - 1)
                    else:
                        setattr(self.bank[iid], 'amount', self.bank[iid]['amount'] - 1)

                    self.balance_container(self.bank)
            elif key == ord('W'):
                # With draw full stack
                if len(self.bank) > 0:
                    # drop-all
                    bank = []
                    for key in self.bank:
                        bank.append(key)

                    iid = bank[self.bank_index]
                    amt = self.bank[iid]['amount']
                    self.cs.ns.send_packet(packet.WithdrawItemPacket(iid, amt))
                    self.bank.pop(iid)

                    # need to account for all pages. index past the last item in list ==> index == last item in list
                    if self.bank_index >= len(bank) - 1:
                        self.bank_index = max(0, len(bank) - 2)

                    # go back a page if we've withdrawn the last item on the last page
                    while 15 * self.view.bank_page >= len(self.bank) and len(self.bank) != 0:
                        self.view.bank_page = max(0, self.view.bank_page - 1)

        
        else:
            return False
        return True

    def process_normal_input(self, key: int) -> bool:
        if key == curses.KEY_UP:
            if self.move(-1, 0):
                self.cs.ns.send_packet(packet.MoveUpPacket())
        elif key == curses.KEY_DOWN:
            if self.move(1, 0):
                self.cs.ns.send_packet(packet.MoveDownPacket())
        elif key == curses.KEY_LEFT:
            if self.move(0, -1):
                self.cs.ns.send_packet(packet.MoveLeftPacket())
        elif key == curses.KEY_RIGHT:
            if self.move(0, 1):
                self.cs.ns.send_packet(packet.MoveRightPacket())
        elif key == ord('g'):
            self.state = State.GRABBING_ITEM
            self.cs.ns.send_packet(packet.GrabItemPacket())
        else:
            return False
        return True

    def move(self, dy, dx) -> bool:
        """
        Moves the game client in a direction. Returns whether the move was successful 
        (can be used to determine whether to send a move packet or not)
        """
        if not self.player_instance:
            # We are most likely loading the room, OK to ignore
            return
        y: int = self.player_instance['y']
        x: int = self.player_instance['x']
        dest_y: int = y + dy
        dest_x: int = x + dx

        # Immovable or special objects
        for instance in self.visible_instances:
            pos = instance['y'], instance['x']
            if pos == (dest_y, dest_x):
                if instance.entity["typename"] == "Bank":
                    self.state = State.IN_BANK
                    return False
                if instance.entity["typename"] in ("OreNode", "TreeNode"):
                    return True


        if self.room.coordinate_exists(dest_y, dest_x) and self.room.at('solid', dest_y, dest_x) == maps.NOTHING:
            self.player_instance.update({
                'id': self.player_instance['id'],
                'y': dest_y,
                'x': dest_x
            })
            return True

        return False

    def get_visible_instance_at(self, y, x) -> dict:
        for instance in self.visible_instances:
            pos = instance['y'], instance['x']
            if pos == (y, x):
                return instance
        return None
    
    def process_selecting_trade_partner_input(self, key: int) -> bool:
        if keybindings.enter(key):
            trade_partner: dict = self.get_visible_instance_at(self.look_cursor_y, self.look_cursor_x)
            if not trade_partner:
                self.quicklog = f"No one to trade with!"
                self.state = State.NORMAL
                return False
            elif trade_partner.entity["typename"] != "Player":
                self.quicklog = f"Can't trade with {trade_partner.entity['name']}!"
                self.state = State.NORMAL
                return False
            else:
                self.quicklog = f"Initiating trade request with {trade_partner.entity['name']}..."
                self.state = State.NORMAL
                self.cs.ns.send_packet(packet.TradeRequestPacket(self.player_instance.entity["id"], trade_partner.entity["id"]))
                return True
                
        return self.process_look_input(key)

    def process_look_input(self, key: int) -> bool:
        desired_y = self.look_cursor_y
        desired_x = self.look_cursor_x

        if key == curses.KEY_UP:
            desired_y -= 1
            pass
        elif key == curses.KEY_DOWN:
            desired_y += 1
        elif key == curses.KEY_LEFT:
            desired_x -= 1
        elif key == curses.KEY_RIGHT:
            desired_x += 1
        else:
            return False

        y, x = self.player_instance['y'], self.player_instance['x']
        if self.room.coordinate_exists(desired_y, desired_x):
            if abs(desired_y - y) <= 10 and abs(desired_x - x) <= 10:
                self.look_cursor_y = desired_y
                self.look_cursor_x = desired_x

        return True

    def send_chat(self, message):
        self.cs.ns.send_packet(packet.ChatPacket(message))

    def reinitialize(self):
        self.room = None
        self.player_instance = None
        self.visible_instances = set()
