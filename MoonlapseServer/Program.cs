using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using MoonlapseNetworking;

namespace MoonlapseServer
{
  class Program
  {
    static readonly object Lock = new object();
    static readonly Dictionary<int, TcpClient> Clients = new Dictionary<int, TcpClient>();
    const int Port = 8081;
    
    static void Main(string[] args)
    {
      int count = 1;
      TcpListener serverSocket = new TcpListener(IPAddress.Any, Port);
      serverSocket.Start();
      Console.WriteLine($"Moonlapse server started listening on any IP at port {Port}...");

      while (true)
      {
        TcpClient client = serverSocket.AcceptTcpClient();
        lock (Lock) Clients.Add(count, client);
        Console.WriteLine($"Received connection from {client.Client.RemoteEndPoint}.");

        Thread t = new Thread(HandleClients);
        t.Start(count);
        count++;
      }
    }

    public static void HandleClients(object o)
    {
      int id = (int)o;
      TcpClient client;

      lock (Lock) client = Clients[id];

      while (true)
      {
        NetworkStream stream = client.GetStream();
        byte[] buffer = new byte[1024];
        int byteCount = stream.Read(buffer, 0, buffer.Length);

        if (byteCount == 0)
        {
          break;
        }

        Packet packet = new Packet(buffer, byteCount);
        string header = packet.Header;
        string body = packet.Body;


        Broadcast(client, header ,body);
        Console.WriteLine($"[{client.Client.RemoteEndPoint}] [{header}] [{body}]");
      }

      lock (Lock) Clients.Remove(id);
      client.Client.Shutdown(SocketShutdown.Both);
      client.Close();
    }

    public static void Broadcast(TcpClient fromClient, string header, string body)
    {
      byte[] buffer = Packet.BuildBuffer(fromClient, header, body);

      lock (Lock)
      {
        foreach (TcpClient c in Clients.Values)
        {
          NetworkStream stream = c.GetStream();

          stream.Write(buffer, 0, buffer.Length);
        }
      }
    }
  }
}