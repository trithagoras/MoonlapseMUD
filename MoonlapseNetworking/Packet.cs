using System;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;

namespace MoonlapseNetworking
{
    public class Packet
    {
        public readonly string Client;
        public readonly string Header;
        public readonly string Body;

        public Packet(byte[] buffer, int byteCount)
        {
            Regex regex = new Regex("^[0-9]*");
            string data;
            Match match;

            // Data is O.T.F. 15|10.1.1.10:455246|HEADER13|Hello, world!
            data = Encoding.ASCII.GetString(buffer, 0, byteCount);
            match = regex.Match(data);
            int clientLength;
            if (match.Length > 0)
                clientLength = int.Parse(match.Value);
            else
                throw new FormatException("No client length");
            int clientStartIdx = data.IndexOf("|", StringComparison.Ordinal) + 1;
            Client = data.Substring(clientStartIdx, clientLength);
            
            data = data.Substring(clientStartIdx + clientLength);
            match = regex.Match(data);
            int headerLength;
            if (match.Length > 0)
                headerLength = int.Parse(match.Value);
            else
                throw new FormatException("No header length");
            int headerStartIdx = data.IndexOf("|", StringComparison.Ordinal) + 1;
            Header = data.Substring(headerStartIdx, headerLength);
            
            data = data.Substring(headerStartIdx + headerLength);
            match = regex.Match(data);
            int bodyLength;
            if (match.Length > 0)
                bodyLength = int.Parse(match.Value);
            else
                throw new FormatException("No body length");
            int bodyStartIdx = data.IndexOf("|", StringComparison.Ordinal) + 1;
            Body = data.Substring(bodyStartIdx, bodyLength);
        }

        public static byte[] BuildBuffer(TcpClient client, string header, string body)
        {
            string c = client.Client.RemoteEndPoint.ToString();
            return Encoding.ASCII.GetBytes($"{c.Length}|{c}{header.Length}|{header}{body.Length}|{body}");
        }
    }
}