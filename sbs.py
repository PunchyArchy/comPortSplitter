import socket
import threading
from serial import Serial


class comPortSplitter:
    """ Сервер для прослушивания порта USB (CPS), к которому подключено устройство с COM-портом через адаптер
     и переотправки данных подключенным к нему клиентов (Clients).
     По сути, выполняет роль сплиттера - COM > USB > CPS > Clients. """
    def __init__(self, ip, port):
        self.create_server(ip, port)
        self.allConnections = []
        threading.Thread(target=self.connReciever, args=()).start()
        self._mainloop()

    def create_server(self, ip, port):
        # Создает сервер
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.bind((ip, port))
        self.serv.listen(10)

    def connReciever(self):
        # Отдельный поток, принимающий подключения и добавляющий их в список self.allConnections для дальнейшней
        # работы
        while True:
            print('\nWaiting for client...')
            conn,addr = self.serv.accept()
            self.allConnections.append(conn)
            print('\tGot new client!')

    def _mainloop(self):
        # Основной цикл работы программы, слушает порт и передает данные клиентам
        while True:
            ser = Serial('COM1', bytesize=8, parity='N', stopbits=1, timeout=1)
            print('\nWaiting data from port.')
            data = ser.readline()
            #data = data.decode()
            ser.close()
            print('\tGot data from port:', data)
            if len(str(data)) < 4:
                data = b'too short msg'
            for conn in self.allConnections:
                try:
                    conn.send(data)
                    print('Sent to the client with success')
                except:
                    print('Failed to send data to client')
                    self.allConnections.remove(conn)
                    
cps = comPortSplitter('192.168.100.33', 2297)
