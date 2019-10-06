using System;
using MoonlapseMUD.Utils;

namespace MoonlapseMUD
{
    class MainClass
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("Hello World!");
            Console.WriteLine("Testing collaboration!");
            //UI.AskQuestion("How are you?", new string[] { "good", "bad" });

            Vector left = new Vector(2, 4);
            Vector right = new Vector(5, 2);

            left += Vector.Down;

            Console.WriteLine(left);
        }
    }
}
