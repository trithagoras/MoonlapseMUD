using System;
namespace MoonlapseMUD.Entities.Items
{
    public class MiscItem : Item
    {
        public MiscItem(string name, string description, int value, double weight) : base(name, description, value, weight)
        {

        }
    }

    public static class GameMiscItems
    {
        public static MiscItem GoldCoin { get; } = new MiscItem("Gold Coin", "A gold coin with King Roldar's face on it.", 1, 0);
    }
}
