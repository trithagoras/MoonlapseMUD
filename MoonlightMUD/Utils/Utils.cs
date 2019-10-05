using System;
using System.Collections.Generic;

namespace MoonlightMUD.Utils
{
    public abstract class Utils
    {
        // Key presses
        public static ConsoleKey KeyUp = ConsoleKey.UpArrow, KeyDown = ConsoleKey.DownArrow, KeyLeft = ConsoleKey.LeftArrow,
            KeyRight = ConsoleKey.RightArrow;


        public static IReadOnlyDictionary<GameColour, ConsoleColor> GameColours = new Dictionary<GameColour, ConsoleColor>
        {
            { GameColour.Ally, ConsoleColor.Green },
            { GameColour.Player, ConsoleColor.Cyan },
            { GameColour.Enemy, ConsoleColor.Red },
            { GameColour.Important, ConsoleColor.Magenta },
            { GameColour.Neutral, ConsoleColor.DarkYellow }
        };

        /// <summary>
        /// Asks a question with array of possible answers.
        /// </summary>
        /// <param name="question">Question string to be asked</param>
        /// <param name="answers">array of possible answers. Must be between 0 and 10 exclusive</param>
        /// <returns>the int value represented by the order of the answer, or -1 if failed.</returns>
        public static int AskQuestion(string question, string[] answers)
        {
            if (answers.Length >= 10 || answers.Length == 0)
            {
                throw new ArgumentOutOfRangeException(nameof(answers));
            }

            while (true)
            {
                Console.Clear();
                Console.WriteLine(question);

                for (int i = 0; i < answers.Length; i++)
                {
                    Console.WriteLine($"{i + 1}) {answers[i]}");
                }

                ConsoleKeyInfo keyInfo = Console.ReadKey(true);

                if (char.IsDigit(keyInfo.KeyChar))
                {
                    int value = int.Parse(keyInfo.KeyChar.ToString());
                    if (value <= answers.Length && value > 0)
                    {
                        return value;
                    }
                }


            }
        }

        public static void WriteMessage(string message, GameColour colour)
        {
            Console.ForegroundColor = GameColours[colour];
            Console.WriteLine(message);
            Console.ResetColor();
            Console.WriteLine("[ENTER]");
            Console.Clear();
        }
    }

    public enum GameColour
    {
        Player = ConsoleColor.Cyan,
        Ally = ConsoleColor.Green,
        Enemy = ConsoleColor.Red,
        Neutral = ConsoleColor.DarkYellow,
        Important = ConsoleColor.Magenta
    }
}