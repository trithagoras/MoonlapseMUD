using System;
using MoonlapseMUD.Entities;
using MoonlapseMUD.Entities.Actors;
using MoonlapseMUD.Entities.Items;
using MoonlapseMUD.Locations;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD
{
    class MainClass
    {
        public static Player Player = new Player();

        public static void Main(string[] args)
        {
            Console.WriteLine("Hello World!");
            Console.WriteLine("Testing collaboration!");

            Location location = new Location(11, 11);
            Player.PlaceInWorld(location, new Vector(5, 5));
            UI.MainUI();

        }
    }
}
