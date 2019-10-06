﻿using System;
using System.Collections.Generic;
using System.Linq;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD.Entities.Actors
{
    public abstract class Actor : Entity
    {
        public int MaxHP { get; protected set; }
        public int HP { get; protected set; }
        public int Level { get; protected set; }
        public bool Dead { get; protected set; }

        public IReadOnlyDictionary<Resistance, double> Resistances { get; } = new Dictionary<Resistance, double>()
        {
            { Resistance.Physical, 0 },
            { Resistance.Magical, 0 },
            { Resistance.Fire, 0 },
            { Resistance.Frost, 0 },
            { Resistance.Lightning, 0 }
        };

        protected Actor(string name, string description) : base(name, description)
        {

        }

        public abstract void Hit(Actor actor);

        public abstract void Die();

        public void EnterPortal(Portal portal)
        {
            PlaceInWorld(portal.Destination, portal.ExitPoint);
        }

        public void Translate(Vector direction)
        {
            if (Location[Position + direction].OfType<Solid>().Any())
            {
                return;
            }

            PlaceInWorld(Location, Position + direction);
        }
    }

    public enum Resistance
    {
        Physical,
        Magical,
        Fire,
        Frost,
        Lightning
    }
}
