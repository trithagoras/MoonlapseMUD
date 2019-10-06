using System;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD.Entities
{
    /// <summary>
    /// Any transition point which can take entities to other locations. e.g. Door, Stairs, etc.
    /// </summary>
    public class Portal : Entity
    {
        public Portal Destination { get; private set; }
        public Vector EntryPoint { get; private set; }

        public Portal(string name, string description, Portal destination, Vector entryPoint) : base(name, description)
        {
            Destination = destination;
            EntryPoint = entryPoint;
        }
    }

    public static class GamePortals
    {

    }
}
