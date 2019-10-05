using System;
namespace MoonlapseMUD.Entities.Items
{
    public class Shield : Item, IEquippable
    {
        public Shield(string name, string description, int value, double weight) : base(name, description, value, weight)
        {

        }
    }
}
