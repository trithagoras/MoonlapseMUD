using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

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

        string data = Encoding.ASCII.GetString(buffer, 0, byteCount);
        Broadcast(client, data);
        Console.WriteLine($"[{client.Client.RemoteEndPoint}]: {data}");
      }

      lock (Lock) Clients.Remove(id);
      client.Client.Shutdown(SocketShutdown.Both);
      client.Close();
    }

    public static void Broadcast(TcpClient fromClient, string msg)
    {
      byte[] buffer = Encoding.ASCII.GetBytes($"[{fromClient.Client.RemoteEndPoint}]: {msg + Environment.NewLine}");

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