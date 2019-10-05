using System;
namespace MoonlapseMUD.Entities
{
    public abstract class Entity
    {
        public string Name { get; protected set; }
        public string Description { get; protected set; }

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
