using System;
using System.Collections.Generic;
using System.ComponentModel;
using MoonlapseMUD.Entities;

namespace MoonlapseMUD.Locations
{
    public class Location
    {

        public string Name { get; private set; }
        public string Description { get; private set; }

        private List<Entity> Entities { get; } = new List<Entity>();

        public Location()
        {
            
        }

        
        

    }
}
