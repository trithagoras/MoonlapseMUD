using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using MoonlapseNetworking;

namespace MoonlapseMUD
{
    class Program
    {
        static void Main(string[] args)
        {
            IPAddress ip = IPAddress.Parse("10.1.1.10");
            int port = 8081;
            TcpClient client = new TcpClient();
            client.Connect(ip, port);
            Console.WriteLine($"Client connected to Moonlapse server at {client.Client.RemoteEndPoint}");
            NetworkStream ns = client.GetStream();
            Thread thread = new Thread(o => HandlePacket((TcpClient) o));

            thread.Start(client);

            string s;
            while (!string.IsNullOrEmpty((s = Console.ReadLine())))
            {
                byte[] buffer = Packet.BuildBuffer(client, "SAY", s);
                ns.Write(buffer, 0, buffer.Length);
            }

            client.Client.Shutdown(SocketShutdown.Send);
            thread.Join();
            ns.Close();
            client.Close();
            Console.WriteLine("Client disconnected from Moonlapse server, exiting.");
        }


        static void HandlePacket(TcpClient client)
        {
            NetworkStream ns = client.GetStream();
            byte[] receivedBytes = new byte[1024];

            int byteCount;
            while ((byteCount = ns.Read(receivedBytes, 0, receivedBytes.Length)) > 0)
            {
                Packet packet = new Packet(receivedBytes, byteCount);
                switch (packet.Header)
                {
                    case "SAY":
                        Console.WriteLine($"[{packet.Client}] [{packet.Header}] [{packet.Body}]");
                        break;
                }
            }
            
        }
    }
}