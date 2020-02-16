from database import Database
from tcpsrv import TcpServer

if __name__ == '__main__':
    database = Database('server/connectionstrings.json')
    tcpsrv = TcpServer('', 8081, database)
    tcpsrv.start()
