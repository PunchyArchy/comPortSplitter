import socket
import threading
from serial import Serial
import serial.tools.list_ports
from time import sleep
import logging
#from terminal_parsers import *
#ports = serial.tools.list_ports.comports()
#import tp
#import terminal_parsers as tp

class comPortSplitter:
    """ Сервер для прослушивания порта USB (CPS), к которому подключено устройство с COM-портом через адаптер
     и переотправки данных подключенным к нему клиентов (Clients).
     По сути, выполняет роль сплиттера - COM > USB > CPS > Clients. """
    def __init__(self, ip, port, port_name='/dev/ttyUSB0', terminal_name='CAS'):
        self.port_name = port_name
        self.create_server(ip, port)
        self.allConnections = []

    def start(self):
        threading.Thread(target=self.connReciever, args=()).start()
        self._mainloop()

    def create_server(self, ip, port):
        # Создает сервер
        print('Creating CPS server')
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        print('Запущен основной цикл отправки весов')
        ser = Serial(self.port_name, bytesize=8, parity='N', stopbits=1, timeout=1, baudrate=9600)
        while True:
            data = ser.readline()
            self.send_data(data)

    def parse_data_cas(self, data):
        data = str(data) #.decode()
        try:
            data_els = data.split(',')
            data_kg = data_els[3]
            data_kg_els = data_kg.split(' ')
            kg = data_kg_els[7]
            return kg
        except:
            return False

           
    def check_data(self, data, parser_func):
        if self.check_scale_disconnected(data):
            data = '17'
        else:
            data = parser_func(data)
        return data

    def check_scale_disconnected(self, data):
        data = str(data)
        if 'x00' in data:
            print('Terminal has been disconnected')
            return True

    def scale_disconnect_act(self):
        pass

    def send_data(self, data, **kwargs):
        for conn in self.allConnections:
            try:
                conn.send(data)
                #print('Sent to the client with success')
            except:
                print('Failed to send weight to client')
                self.allConnections.remove(conn)

class WeightSplitter(comPortSplitter):
    def __init__(self, ip, port, port_name='/dev/ttyUSB0', terminal_name='CAS'):
        super().__init__(ip, port, port_name, terminal_name)
        self.parser_func = self.define_parser(terminal_name)
        self.smlist = [1]

    def define_parser(self, terminal_name):
        if terminal_name == 'CAS':
            return self.parse_data_cas

    def parse_data_cas(self, data):
        data = str(data)
        try:
            data_els = data.split(',')
            for el in data_els:
                if 'kg' in el:
                    kg_els = el.split(' ')
                    for element in kg_els:
                        if element.isdigit():
                            return element
        except:
            return 4

    def send_data(self, data, **kwargs):
        data = bytes(data, encoding='utf-8')
        super().send_data(data, **kwargs)

    def sending_thread(self, timing=1):
        sleep(timing)
        self.send_data(self.smlist[-1])

    def _mainloop(self):
        # Основной цикл работы программы, слушает порт и передает данные клиентам
        print('Запущен основной цикл отправки весов')
        sleep(5)
        ser = Serial(self.port_name, bytesize=8, parity='N', stopbits=1, timeout=1, baudrate=9600)
        threading.Thread(target=self.sending_thread, args=(1,)).start()
        while True:
            data = ser.readline()
            data = self.check_data(data, self.parser_func)
            self.smlist.append(data)
            #if data:
            #     self.send_data(data)

if __name__ == '__main__':
    cps = WeightSplitter('localhost', 1488)
    cps.start()
