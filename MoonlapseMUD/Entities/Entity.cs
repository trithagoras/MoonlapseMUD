using System;
using MoonlapseMUD.Locations;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD.Entities
{
    public abstract class Entity
    {
        public string Name { get; protected set; }
        public string Description { get; protected set; }

		public Location Location { get; protected set; }
        public Vector Position { get; protected set; }

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

        public void PlaceInWorld(Location location, Vector position)
        {
            if (Location != null)
            {
                Location[Position.X, Position.Y].Remove(this);
            }

            Location = location;

            Position = position;
            Location[Position.X, Position.Y].Add(this);
        }
    }
}
