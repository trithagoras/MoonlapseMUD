using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using MoonlapseMUD.Entities;
using MoonlapseMUD.Entities.Actors;
using MoonlapseMUD.Entities.Items;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD.Locations
{
    public class Location
    {
        public string Name { get; private set; }
        public string Description { get; private set; }

        public int Width { get; private set; }
        public int Height { get; private set; }

        private Dictionary<Entity, int>[,] Coordinates;

        /// <summary>
        /// Testing constructor which creates an empty map surrounded by walls.
        /// </summary>
        /// <param name="width"></param>
        /// <param name="height"></param>
        public Location(int width, int height)
        {
            Width = width;
            Height = height;

            Coordinates = new Dictionary<Entity, int>[Width, Height];

            for (int row = 0; row < Height; row++)
            {
                for (int column = 0; column < Width; column++)
                {
                    
                    if (row == 0 || row == Height - 1 || column == 0 || column == Width - 1)
                    {
                        Coordinates[column, row] = new Dictionary<Entity, int>() { { GameSolids.Wall, 1 } };
                    }
                    else
                    {
                        Coordinates[column, row] = new Dictionary<Entity, int>();
                    }
                }
            }
        }

        /// <summary>
        /// Prints the map to the screen complete with colours
        /// </summary>
        public void PrintMap()
        {
            char key;

            for (int row = 0; row < Height; row++)
            {
                for (int column = 0; column < Width; column++)
                {
                    // drawing layers: wall | portal | Player, hostile actors, other players, other actors,
                    // leveled items (colour distinguished e.g. purple '$' = epic)

                    Console.ResetColor();

                    if (this[column, row].Keys.OfType<Solid>().Any())
                    {
                        key = '#';
                    }
                    else if (this[column, row].Keys.OfType<Portal>().Any())
                    {
                        Console.ForegroundColor = UI.GameColours[GameColour.Important];
                        key = 'X';
                    }
                    else if (this[column, row].Keys.OfType<Player>().Any())
                    {
                        Console.ForegroundColor = UI.GameColours[GameColour.Player];
                        key = '@';
                    }
                    else if (this[column, row].Keys.OfType<Character>().Any())
                    {
                        // TODO: Change this. @ should only reference players.
                        key = '@';
                    }
                    else if (this[column, row].Keys.OfType<Item>().Any())
                    {
                        key = '$';
                    }
                    else
                    {
                        Console.ForegroundColor = ConsoleColor.Gray;
                        key = '.';
                    }

                    Console.Write($"{key} ");
                }

                Console.Write("\n");
            }

        }

        public Dictionary<Entity, int> this[int x, int y]
        {
            get => Coordinates[x, y];
        }

    }
}
