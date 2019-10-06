using System;
using System.Collections.Generic;
using MoonlapseMUD.Entities.Items;

namespace MoonlapseMUD.Entities
{
    public class ItemStack : Entity
    {
        private Dictionary<Item, int> Contents;

        public ItemStack() : base("Stack of items", "There are many items here.")
        {
            Contents = new Dictionary<Item, int>();
        }

        public void AddToStack(Item item, int amount)
        {
            foreach (Item i in Contents.Keys)
            {
                if (item == i)
                {
                    Contents[i] += amount;
                    return;
                }
            }
            Contents[item] = amount;
        }
    }
}
