using System;
using MoonlapseMUD.Locations;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD.Entities
{
    /// <summary>
    /// Any transition point which can take entities to other locations. e.g. Door, Stairs, etc.
    /// </summary>
    public class Portal : Entity
    {
        public Location Destination { get; private set; }
        /// <summary>
        /// Where the entity is placed on the other side of the portal.
        /// </summary>
        public Vector ExitPoint { get; private set; }

        public Portal(string name, string description, Location destination, Vector exitPoint) : base(name, description)
        {
            Destination = destination;
            ExitPoint = exitPoint;
        }
    }

    public static class GamePortals
    {

    }
}
