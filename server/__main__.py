from database import Database
from tcpsrv import TcpServer

if __name__ == '__main__':
    database = Database('server/connectionstrings.json')
    tcpsrv = TcpServer('', 42523, database)
    tcpsrv.start()
