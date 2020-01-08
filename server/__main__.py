from tcpsrv import TcpServer

if __name__ == '__main__':
    tcpsrv = TcpServer('', 8081)
    tcpsrv.start()
