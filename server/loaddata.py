"""
This file loads all entities into the DB. This should only be run once the database
is flushed. A python script is less cumbersome than a JSON file, so it is preferred.
"""

# Required for importing the networking app (upper dir)
import sys
from pathlib import Path

file = Path(__file__).resolve()
root = file.parents[1]
sys.path.append(str(root))

from server import manage
from server import models

print("ALERT: Please remember to flush before running this script!")
x = input("Do you wish to continue? y/n\n").upper()

if x != 'Y' and x != 'YES':
    print("Exiting script")
    exit(0)

print("Importing all initial models into DB")

# all rooms
rm_garden = models.Room(name="Garden", file_name="garden"); rm_garden.save()
rm_tavern = models.Room(name="Tavern", file_name="tavern"); rm_tavern.save()
rm_forest = models.Room(name="Forest", file_name="forest"); rm_forest.save()

# door from garden to tavern
ent_garden_to_tavern = models.Entity(typename="Portal", name="Door to Tavern"); ent_garden_to_tavern.save()
portal_garden_to_tavern = models.Portal(entity=ent_garden_to_tavern, linkedroom=rm_tavern, linkedy=14, linkedx=14); portal_garden_to_tavern.save()
inst_garden_to_tavern = models.InstancedEntity(entity=ent_garden_to_tavern, room=rm_garden, y=9, x=7); inst_garden_to_tavern.save()

# door from tavern to garden
ent_tavern_to_garden = models.Entity(name="Door to Garden", typename="Portal"); ent_tavern_to_garden.save()
portal_tavern_to_garden = models.Portal(entity=ent_tavern_to_garden, linkedroom=rm_garden, linkedy=9, linkedx=7); portal_tavern_to_garden.save()
inst_tavern_to_garden = models.InstancedEntity(entity=ent_tavern_to_garden, y=14, x=14, room=rm_tavern); inst_tavern_to_garden.save()

# beer
ent_beer = models.Entity(name="Beer", typename="Item"); ent_beer.save()
item_beer = models.Item(entity=ent_beer, value=6); item_beer.save()
inst_beer = models.InstancedEntity(entity=ent_beer, room=rm_tavern, y=5, x=10, respawn_time=5); inst_beer.save(())
inst_beer2 = models.InstancedEntity(entity=ent_beer, room=rm_tavern, y=5, x=12, respawn_time=3); inst_beer2.save()

# door from tavern to forest
ent_tavern_to_forest = models.Entity(name="Door to Forest", typename="Portal"); ent_tavern_to_forest.save()
portal_tavern_to_forest = models.Portal(entity=ent_tavern_to_forest, linkedroom=rm_forest, linkedy=12, linkedx=34); portal_tavern_to_forest.save()
inst_tavern_to_forest = models.InstancedEntity(entity=ent_tavern_to_forest, y=1, x=1, room=rm_tavern); inst_tavern_to_forest.save()

# door from forest to tavern
ent_forest_to_tavern = models.Entity(typename="Portal", name="Door to Tavern"); ent_forest_to_tavern.save()
portal_forest_to_tavern = models.Portal(entity=ent_forest_to_tavern, linkedroom=rm_tavern, linkedy=1, linkedx=1); portal_forest_to_tavern.save()
inst_forest_to_tavern = models.InstancedEntity(entity=ent_forest_to_tavern, room=rm_forest, y=12, x=34); inst_forest_to_tavern.save()

# pickaxe and axe spawns
ent_pickaxe = models.Entity(name="Iron Pickaxe", typename="Pickaxe"); ent_pickaxe.save()
item_pickaxe = models.Item(entity=ent_pickaxe, value=45); item_pickaxe.save()
inst_pickaxe = models.InstancedEntity(entity=ent_pickaxe, room=rm_garden, y=16, x=10, respawn_time=15); inst_pickaxe.save()

ent_axe = models.Entity(name="Iron Axe", typename="Axe"); ent_axe.save()
item_axe = models.Item(entity=ent_axe, value=35); item_axe.save()
inst_axe = models.InstancedEntity(entity=ent_axe, room=rm_garden, y=16, x=15, respawn_time=15); inst_axe.save()

# tree resource
ent_logs = models.Entity(name="Logs", typename="Logs"); ent_logs.save()
item_logs = models.Item(entity=ent_logs, value=15); item_logs.save()

dtable_tree = models.DropTable(); dtable_tree.save()
dtableitem_logs_from_tree_node = models.DropTableItem(droptable=dtable_tree, item=item_logs, min_amt=1, max_amt=1, chance=1); dtableitem_logs_from_tree_node.save()

ent_tree_node = models.Entity(name="Tree", typename="TreeNode"); ent_tree_node.save()
inst_tree_node = models.InstancedEntity(entity=ent_tree_node, room=rm_garden, y=19, x=21, respawn_time=10); inst_tree_node.save()
rsnode_tree = models.ResourceNode(entity=ent_tree_node, droptable=dtable_tree, req_lvl=1, xp_given=5); rsnode_tree.save()

# Iron ore resource
ent_iron_ore = models.Entity(name="Iron Ore", typename="Ore"); ent_iron_ore.save()
item_iron_ore = models.Item(entity=ent_iron_ore, value=15); item_iron_ore.save()

dtable_iron_ore = models.DropTable(); dtable_iron_ore.save()
dtableitem_iron_ore_from_iron_ore_node = models.DropTableItem(droptable=dtable_iron_ore, item=item_iron_ore, min_amt=1, max_amt=1, chance=1); dtableitem_iron_ore_from_iron_ore_node.save()

ent_iron_ore_node = models.Entity(name="Iron Ore", typename="OreNode"); ent_iron_ore_node.save()
inst_iron_ore_node = models.InstancedEntity(entity=ent_iron_ore_node, room=rm_garden, y=3, x=4, respawn_time=10); inst_iron_ore_node.save()
rsnode_iron_ore = models.ResourceNode(entity=ent_iron_ore_node, droptable=dtable_iron_ore, req_lvl=1, xp_given=5); rsnode_iron_ore.save()

print("Done")
