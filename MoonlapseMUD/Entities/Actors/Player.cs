using System;
using MoonlapseMUD.Entities.Items;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD.Entities.Actors
{
    public class Player : Character
    {
        public int MaxXP { get; private set; }
        public int XP { get; private set; }

        public Player() : base(name: "Adventurer", description: "", vitality: 10, strength: 10, agility: 10,
            dexterity: 10, willpower: 10, intelligence: 10, GameWeapons.Fist, GameWeapons.Fist,
            GameArmours.Naked, GameArmours.Naked, GameArmours.Naked, GameArmours.Naked)
        {

        }

        public void Equip(IEquippable item)
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
                switch (weapon.Size)
                {
                    case WeaponSize.Large:
                        MainHand = weapon;
                        OffHand = GameWeapons.Fist;
                        break;

                    case WeaponSize.Medium:
                        MainHand = weapon;
                        break;

                    case WeaponSize.Small:
                        int answer = UI.AskQuestion("Which hand?", new string[] { "Main", "Off" });
                        if (answer == 1)
                        {
                            MainHand = weapon;
                        }
                        else if (answer == 2)
                        {
                            OffHand = weapon;
                            if (MainHand.Size == WeaponSize.Large)
                            {
                                MainHand = GameWeapons.Fist;
                            }
                        }
                        break;
                }
            }
        }
    }
}
