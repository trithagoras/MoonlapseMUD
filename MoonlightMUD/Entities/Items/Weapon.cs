using System;
using System.Collections.Generic;
using System.Linq;

namespace MoonlightMUD.Entities.Items
{
    public class Weapon : Item, IEquippable
    {
        public double[] Scaling { get; private set; } = new double[3];
        public int[] Requirements { get; private set; } = new int[3];

        public int PhysicalDamage { get; private set; }
        public int MagicalDamage { get; private set; }
        public int FireDamage { get; private set; }
        public int FrostDamage { get; private set; }
        public int LightningDamage { get; private set; }

        public int PoisonBuildUp { get; private set; }
        public int BleedBuildUp { get; private set; }

        public int MaxDurability { get; private set; }
        public int Durability { get; private set; }

        public WeaponSize Size { get; private set; }

        public bool Broken { get; private set; }

        public int Level { get; private set; }

        public Weapon(string name, string description, int value, double weight, double[] scaling,
            int[] requirements, int physicalDamage, int magicalDamage, int fireDamage,
            int frostDamage, int lightningDamage, int poisonBuildUp, int bleedBuildUp,
            int maxDurability, WeaponSize size, int level) : base(name, description, value, weight)
        {
            Scaling = scaling;
            Requirements = requirements;
            PhysicalDamage = physicalDamage;
            MagicalDamage = magicalDamage;
            FireDamage = fireDamage;
            FrostDamage = frostDamage;
            LightningDamage = lightningDamage;
            PoisonBuildUp = poisonBuildUp;
            BleedBuildUp = bleedBuildUp;
            MaxDurability = maxDurability;
            Size = size;

            Durability = maxDurability;

            Level = level;
            for (int i = 0; i < level; i++)
            {
                Upgrade();
            }
        }

        public Weapon(string name, string description, int value, double weight, double[] scaling,
            int[] requirements, int physicalDamage, int maxDurability, WeaponSize size)
            : base(name, description, value, weight)
        {
            Scaling = scaling;
            Requirements = requirements;
            PhysicalDamage = physicalDamage;
            MagicalDamage = 0;
            FireDamage = 0;
            FrostDamage = 0;
            LightningDamage = 0;
            PoisonBuildUp = 0;
            BleedBuildUp = 0;
            MaxDurability = maxDurability;
            Size = size;

            Durability = maxDurability;

            Level = 0;
        }

        public Weapon(Weapon copy)
            : base(copy.Name, copy.Description, copy.Value, copy.Weight)
        {
            Scaling = new double[3] { copy.Scaling[0], copy.Scaling[1], copy.Scaling[2] };
            Requirements = new int[3] { copy.Requirements[0], copy.Requirements[1], copy.Requirements[2] };

            PhysicalDamage = copy.PhysicalDamage;
            MagicalDamage = copy.MagicalDamage;
            FireDamage = copy.FireDamage;
            FrostDamage = copy.FrostDamage;
            LightningDamage = copy.LightningDamage;
            PoisonBuildUp = copy.PoisonBuildUp;
            BleedBuildUp = copy.BleedBuildUp;
            MaxDurability = copy.MaxDurability;
            Size = copy.Size;

            Durability = copy.Durability;
            Broken = copy.Broken;
            Level = copy.Level;
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

        public void Upgrade()
        {
            if (Level < 10)
            {
                Level++;
                PhysicalDamage += (int)(0.1f * PhysicalDamage);
                MagicalDamage += (int)(0.1f * MagicalDamage);
                FireDamage += (int)(0.1f * FireDamage);
                FrostDamage += (int)(0.1f * FrostDamage);
                LightningDamage += (int)(0.1f * LightningDamage);

                for (var i = 0; i < 3; i++)
                {
                    Scaling[i] *= 1.1;
                    Scaling[i] = Math.Round(Scaling[i], 2);
                }
            }
        }

        public override string ToString()
        {
            return $"{Name} +{Level}";
        }

        //TODO: finish this
        public override string ExamineString()
        {
            return $"" +
                $"{Name} +{Level}\n" +
                $"{Description}\n" +
                $"Physical Damage: {PhysicalDamage}\n" +
                $"Magical Damage: {MagicalDamage}\n" +
                $"Scaling: {string.Join(", ", Scaling)}";
        }

        public override bool Equals(object obj)
        {
            return obj is Weapon weapon &&
                   Enumerable.SequenceEqual(Scaling, weapon.Scaling) &&
                   Enumerable.SequenceEqual(Requirements, weapon.Requirements) &&
                   PhysicalDamage == weapon.PhysicalDamage &&
                   MagicalDamage == weapon.MagicalDamage &&
                   FireDamage == weapon.FireDamage &&
                   FrostDamage == weapon.FrostDamage &&
                   LightningDamage == weapon.LightningDamage &&
                   PoisonBuildUp == weapon.PoisonBuildUp &&
                   BleedBuildUp == weapon.BleedBuildUp &&
                   MaxDurability == weapon.MaxDurability &&
                   Durability == weapon.Durability &&
                   Size == weapon.Size;
        }

        public override int GetHashCode()
        {
            var hashCode = 1871953358;
            hashCode = hashCode * -1521134295 + Scaling.GetHashCode();
            hashCode = hashCode * -1521134295 + Requirements.GetHashCode();
            hashCode = hashCode * -1521134295 + PhysicalDamage.GetHashCode();
            hashCode = hashCode * -1521134295 + MagicalDamage.GetHashCode();
            hashCode = hashCode * -1521134295 + FireDamage.GetHashCode();
            hashCode = hashCode * -1521134295 + FrostDamage.GetHashCode();
            hashCode = hashCode * -1521134295 + LightningDamage.GetHashCode();
            hashCode = hashCode * -1521134295 + PoisonBuildUp.GetHashCode();
            hashCode = hashCode * -1521134295 + BleedBuildUp.GetHashCode();
            hashCode = hashCode * -1521134295 + MaxDurability.GetHashCode();
            hashCode = hashCode * -1521134295 + Durability.GetHashCode();
            hashCode = hashCode * -1521134295 + Size.GetHashCode();
            return hashCode;
        }

        public static bool operator ==(Weapon left, Weapon right)
        {
            return EqualityComparer<Weapon>.Default.Equals(left, right);
        }

        public static bool operator !=(Weapon left, Weapon right)
        {
            return !(left == right);
        }

        /// <summary>
        /// Returns a deep copy
        /// </summary>
        /// <returns>deep copy</returns>
        public Weapon Copy()
        {
            return new Weapon(this);
        }
    }

    public enum WeaponSize
    {
        Small,
        Medium,
        Large
    }

    public enum AttackType
    {
        Slash,
        Crush,
        Stab
    }

    public static class GameWeapons
    {
        public static Weapon Fist { get; } = new Weapon("Bare Fist", "primitive", 0, 0,
            new double[3] { 0, 0, 0 }, new int[3] { 0, 0, 0 }, 2, -1, WeaponSize.Small);
    }
}
