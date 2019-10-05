using System;

namespace MoonlightMUD
{
    class MainClass
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("Hello World!");
            Console.WriteLine("Testing collaboration!");
            Utils.AskQuestion("How are you?", new string[] { "good", "bad" });

        }
    }
}
