using System;
using System.Collections.Generic;
using System.Linq;

namespace MoonlapseMUD.Entities.Items
{
    public class Armour : Item
    {
        public int PhysicalDefence { get; private set; }
        public int MagicalDefence { get; private set; }
        public int FireDefence { get; private set; }
        public int FrostDefence { get; private set; }
        public int LightningDefence { get; private set; }
        public int PoisonDefence { get; private set; }
        public int BleedDefence { get; private set; }

        public int MaxDurability { get; private set; }
        public int Durability { get; private set; }
        public bool Broken { get; private set; }

        public int[] Requirements { get; private set; }

        public ArmourLocation Location { get; private set; }

        public ArmourSize Size { get; private set; }

        public Armour(string name, string description, int value, double weight,
            int physicalDefence, int magicalDefence, int fireDefence, int frostDefence,
            int lightningDefence, int poisonDefence, int bleedDefence, int maxDurability,
            int[] requirements, ArmourLocation location, ArmourSize size) : base(name, description, value, weight)
        {
            PhysicalDefence = physicalDefence;
            MagicalDefence = magicalDefence;
            FireDefence = fireDefence;
            FrostDefence = frostDefence;
            LightningDefence = lightningDefence;
            PoisonDefence = poisonDefence;
            BleedDefence = bleedDefence;
            MaxDurability = maxDurability;
            Requirements = requirements;
            Location = location;
            Size = size;

            Durability = maxDurability;
        }

        /**
         * positive amount = repairing
         * negative amount = damaging
         */
        public void Repair(int amount)
        {
            Durability += amount;
            if (Durability <= 0)
            {
                Durability = 0;
                Broken = true;
            }
            else if (Durability >= MaxDurability)
            {
                Durability = MaxDurability;
                Broken = false;
            }
        }

        public override bool Equals(object obj)
        {
            return obj is Armour armour &&
                   base.Equals(obj) &&
                   PhysicalDefence == armour.PhysicalDefence &&
                   MagicalDefence == armour.MagicalDefence &&
                   FireDefence == armour.FireDefence &&
                   FrostDefence == armour.FrostDefence &&
                   LightningDefence == armour.LightningDefence &&
                   PoisonDefence == armour.PoisonDefence &&
                   BleedDefence == armour.BleedDefence &&
                   MaxDurability == armour.MaxDurability &&
                   Durability == armour.Durability &&
                   Broken == armour.Broken &&
                   Enumerable.SequenceEqual(Requirements, armour.Requirements) &&
                   Location == armour.Location &&
                   Size == armour.Size;
        }

        public override int GetHashCode()
        {
            var hashCode = -1272422807;
            hashCode = hashCode * -1521134295 + base.GetHashCode();
            hashCode = hashCode * -1521134295 + PhysicalDefence.GetHashCode();
            hashCode = hashCode * -1521134295 + MagicalDefence.GetHashCode();
            hashCode = hashCode * -1521134295 + FireDefence.GetHashCode();
            hashCode = hashCode * -1521134295 + FrostDefence.GetHashCode();
            hashCode = hashCode * -1521134295 + LightningDefence.GetHashCode();
            hashCode = hashCode * -1521134295 + PoisonDefence.GetHashCode();
            hashCode = hashCode * -1521134295 + BleedDefence.GetHashCode();
            hashCode = hashCode * -1521134295 + MaxDurability.GetHashCode();
            hashCode = hashCode * -1521134295 + Durability.GetHashCode();
            hashCode = hashCode * -1521134295 + Broken.GetHashCode();
            hashCode = hashCode * -1521134295 + Requirements.GetHashCode();
            hashCode = hashCode * -1521134295 + Location.GetHashCode();
            hashCode = hashCode * -1521134295 + Size.GetHashCode();
            return hashCode;
        }

        public static bool operator ==(Armour left, Armour right)
        {
            return EqualityComparer<Armour>.Default.Equals(left, right);
        }

        public static bool operator !=(Armour left, Armour right)
        {
            return !(left == right);
        }
    }

    public enum ArmourLocation
    {
        Head,
        Body,
        Legs,
        Feet,
        Arms,
        Ring,
        Necklace,
        Cape,
        NONE        // Do not use this! only reserved for Naked which is equipped anywhere
    }

    public enum ArmourSize
    {
        Light,      // best magicka regen
        Medium,     // best stamina regen
        Heavy       // best defence
    }

    public static class GameArmours
    {
        public static Armour Naked { get; } = new Armour("naked", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, -1,
            new int[3] { 0, 0, 0 }, ArmourLocation.NONE, ArmourSize.Light);
    }
}