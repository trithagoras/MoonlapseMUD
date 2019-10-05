using System;
using System.Collections.Generic;
using MoonlightMUD.Entities.Items;

namespace MoonlightMUD.Entities.Actors
{
    public class Character : Actor
    {
        public int MaxMP { get; protected set; }
        public int MP { get; protected set; }

        public Dictionary<Attribute, int> Attributes { get; } = new Dictionary<Attribute, int>()
        {
            { Attribute.Vitality, 0 },
            { Attribute.Strength, 0 },
            { Attribute.Agility, 0 },
            { Attribute.Dexterity, 0 },
            { Attribute.Willpower, 0 },
            { Attribute.Intelligence, 0 }
        };

        public Weapon MainHand { get; protected set; }
        public IEquippable OffHand { get; protected set; }
        public Armour Head { get; protected set; }
        public Armour Body { get; protected set; }
        public Armour Arms { get; protected set; }
        public Armour Feet { get; protected set; }

        protected Dictionary<Item, int> inventory { get; } = new Dictionary<Item, int>();
        public IReadOnlyDictionary<Item, int> Inventory { get => inventory; }

        //protected List<Spell> spellbook { get; } = new List<Spell>();
        //public IReadOnlyList<Spell> Spellbook { get => spellbook; }

        #region Constructors
        public Character(string name, string description, int vitality,
            int strength, int agility, int dexterity, int willpower,
            int intelligence, Weapon mainHand, IEquippable offHand,
            Armour head, Armour body, Armour arms, Armour feet) : base(name, description)
        {
            Attributes[Attribute.Vitality] = vitality;
            Attributes[Attribute.Strength] = strength;
            Attributes[Attribute.Agility] = agility;
            Attributes[Attribute.Dexterity] = dexterity;
            Attributes[Attribute.Willpower] = willpower;
            Attributes[Attribute.Intelligence] = intelligence;

            Level = 1 + (vitality + strength + agility + dexterity + willpower + intelligence - 60);

            MaxHP = 400 + vitality * 20;
            HP = MaxHP;
            MaxMP = MP = 0;

            // Resistances inherited and = 0

            MainHand = mainHand;
            OffHand = offHand;
            Head = head;
            Body = body;
            Arms = arms;
            Feet = feet;
        }
        #endregion

        #region Inventory and Spells
        /// <summary>
        /// Adds <paramref name="item"/> to inventory with <paramref name="amount"/>
        /// </summary>
        /// <param name="item">Item to be added</param>
        /// <param name="amount">Amount of Item to add</param>
        public void AddToInventory(Item item, int amount)
        {

            foreach (Item i in inventory.Keys)
            {
                if (item == i)
                {
                    inventory[i] += amount;
                    return;
                }
            }
            inventory[item] = amount;
        }

        /// <summary>
        /// Calls <see cref="AddToInventory(Item, int)"/> with amount=1
        /// </summary>
        /// <param name="item">Item to be added</param>
        public void AddToInventory(Item item)
        {
            AddToInventory(item, 1);
        }

        public string GetInventory()
        {
            string s = "";

            foreach (Item item in inventory.Keys)
            {
                s += $"{item.ToString()}\t\t{inventory[item]}\n";
            }
            return s;
        }

        public void Equip(IEquippable item, bool toMainHand = true)
        {
            if (item is Shield shield)
            {
                OffHand = shield;
                if (MainHand.Size == WeaponSize.Large)
                {
                    MainHand = GameWeapons.Fist;
                }
            }
            else if (item is Weapon weapon)
            {
                if (toMainHand)
                {
                    MainHand = weapon;
                    if (weapon.Size == WeaponSize.Large)
                    {
                        OffHand = GameWeapons.Fist;
                    }
                }

                if (!toMainHand && weapon.Size == WeaponSize.Small)
                {
                    OffHand = weapon;
                    if (MainHand.Size == WeaponSize.Large)
                    {
                        MainHand = GameWeapons.Fist;
                    }
                }
            }
        }

        public void Equip(Armour item)
        {
            int[] reqs = { Attributes[Attribute.Strength], Attributes[Attribute.Dexterity], Attributes[Attribute.Intelligence] };
            for (var i = 0; i < 3; i++)
            {
                if (reqs[i] < item.Requirements[i])
                {
                    Utils.
                    Utils.WriteMessage("You do not meet the requirements to equip this.", Utils.GameColour.Enemy);
                    return;
                }
            }

            switch (item.Location)
            {
                case ArmourLocation.Head: Head = item; return;
                case ArmourLocation.Body: Body = item; return;
                    //TODO Complete this
            }
        }
        #endregion

        public override string ToString()
        {
            return
                $"{Name}\n" +
                $"{Description}\n" +
                $"Level: {Level}\n" +
                $"Attributes: {string.Join(";", Attributes)}\n" +
                $"HP: {HP}/{MaxHP}\n" +
                $"Main Hand: {(MainHand as Item).Name}\n" +
                $"Off Hand: {(OffHand as Item).Name}";
        }

        #region Combat
        public override void Hit(Actor actor)
        {
            if (OffHand is Weapon offHand)
            {

            }

            if (actor is Character character)
            {

            }
            /*else if (actor is Creature creature)
            {

            }*/
        }

        public override void Die()
        {
            throw new NotImplementedException();
        }
        #endregion
    }

    public enum Attribute
    {
        Vitality,
        Strength,
        Agility,
        Dexterity,
        Willpower,
        Intelligence
    }

    public static class GameCharacters
    {
        //public static Character Rickert = new Character("Rickert", "PH", 25, 15, 30, 20, 55, 65,
        //    GameWeapons.Fist, GameWeapons.Fist, GameArmours.Naked, GameArmours.Naked, GameArmours.Naked, GameArmours.Naked);
    }
}