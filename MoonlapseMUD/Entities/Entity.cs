using System;
using MoonlapseMUD.Locations;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD.Entities
{
    public abstract class Entity
    {
        public string Name { get; protected set; }
        public string Description { get; protected set; }

        public Location Location;

        public Vector Position;

        protected Entity(string name, string description)
        {
            Name = name;
            Description = description;
        }

        public virtual string ExamineString()
        {
            return $"" +
                $"{Name}\n" +
                $"{Description}\n";
        }

        public override string ToString()
        {
            return Name;
        }
    }
}
