using System;
using System.Collections.Generic;

namespace MoonlightMUD.Entities.Items
{
    public abstract class Item : Entity
    {
        public int Value { get; protected set; }
        public double Weight { get; protected set; }

        protected Item(string name, string description, int value, double weight) : base(name, description)
        {
            Value = value;
            Weight = weight;
        }

        public override bool Equals(object obj)
        {
            return obj is Item item &&
                   Name == item.Name &&
                   Description == item.Description &&
                   Value == item.Value &&
                   Math.Abs(Weight - item.Weight) < 0.001;
        }

        public override int GetHashCode()
        {
            var hashCode = -1456025726;
            hashCode = hashCode * -1521134295 + EqualityComparer<string>.Default.GetHashCode(Name);
            hashCode = hashCode * -1521134295 + EqualityComparer<string>.Default.GetHashCode(Description);
            hashCode = hashCode * -1521134295 + Value.GetHashCode();
            hashCode = hashCode * -1521134295 + Weight.GetHashCode();
            return hashCode;
        }

        public static bool operator ==(Item left, Item right)
        {
            return EqualityComparer<Item>.Default.Equals(left, right);
        }

        public static bool operator !=(Item left, Item right)
        {
            return !(left == right);
        }
    }
}
