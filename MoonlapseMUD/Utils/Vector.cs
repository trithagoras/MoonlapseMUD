using System;
namespace MoonlapseMUD.Utils
{
    public struct Vector
    {
        public int X, Y;

        public Vector(int x, int y)
        {
            X = x;
            Y = y;
        }

        public static Vector Zero => new Vector(0, 0);
        public static Vector Up => new Vector(0, -1);
        public static Vector Down => new Vector(0, 1);
        public static Vector Left => new Vector(-1, 0);
        public static Vector Right => new Vector(1, 0);

        public static Vector operator +(Vector left, Vector right)
        {
            return new Vector(left.X + right.X, left.Y + right.Y);
        }

        public static Vector operator -(Vector position)
        {
            return new Vector(-position.X, -position.Y);
        }

        public static Vector operator -(Vector left, Vector right)
        {
            return left + (-right);
        }

        public static Vector operator *(Vector position, int scalar)
        {
            return new Vector(position.X * scalar, position.Y * scalar);
        }

        public static Vector operator *(int scalar, Vector position)
        {
            return new Vector(position.X * scalar, position.Y * scalar);
        }

        public override string ToString()
        {
            return $"{X},{Y}";
        }

        #region Equal overrides
        public override bool Equals(object obj)
        {
            return obj is Vector position &&
                   X == position.X &&
                   Y == position.Y;
        }

        public override int GetHashCode()
        {
            var hashCode = 1861411795;
            hashCode = hashCode * -1521134295 + X.GetHashCode();
            hashCode = hashCode * -1521134295 + Y.GetHashCode();
            return hashCode;
        }

        public static bool operator ==(Vector left, Vector right)
        {
            return left.Equals(right);
        }

        public static bool operator !=(Vector left, Vector right)
        {
            return !(left == right);
        }
        #endregion
    }
}
