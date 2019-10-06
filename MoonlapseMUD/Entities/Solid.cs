using System;
namespace MoonlapseMUD.Entities
{
    public class Solid : Entity
    {
        public Solid(string name, string description) : base(name, description)
        {
        }
    }

    public static class GameSolids
    {
        public static Solid Wall = new Solid("Wall", "GENERIC WALL");
    }
}
