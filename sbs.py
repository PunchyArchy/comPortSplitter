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
    def __init__(self, ip, port):
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
        #sleep(5)
        ser = Serial('/dev/ttyUSB0', bytesize=8, parity='N', stopbits=1, timeout=1, baudrate=9600)
        while True:
            data = ser.readline()
            #self.send_data(data)
            #data = self.check_data(data)
            self.send_data(data)
            #if data:
                 #print('TRACK. Sending', data)
            #     self.send_data(bytes(data, encoding='utf-8'))

    def parse_data_cas(self, data):
        #data_str = data
        #print(type(data))
       # print('data', data)
        data = str(data) #.decode()
        try:
            data_els = data.split(',')
        #    print('data els', data_els, 'len', len(data_els))
            data_kg = data_els[3]
         #   print(data_kg)
            data_kg_els = data_kg.split(' ')
          #  print('data_kg_els', data_kg_els, 'len', len(data_kg_els))
            kg = data_kg_els[7]
            return kg
        except:
            return False

           
    def check_data(self, data):
        if self.check_scale_disconnected(data):
            data = '17'
        else:
            data = self.parse_data_cas(data)
        #print('Получены данные после парсинга:', data)
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
    def __init__(self, ip, port):
        comPortSplitter.__init__(self, ip, port)

    def parse_data_cas(self, data):
        #data_str = data
        #print(type(data))
       # print('data', data)
        data = str(data) #.decode()
        try:
            data_els = data.split(',')
          #  print('data els', data_els, 'len', len(data_els))
            #data_kg = data_els[3]
         #   print(data_kg)
            #data_kg_els = data_kg.split(' ')
          #  print('data_kg_els', data_kg_els, 'len', len(data_kg_els))
            #kg = data_kg_els[7]
            #if 'kg' in kg:
            #    kg = data_kg_els[6]
            for el in data_els:
                #print(el)
                if 'kg' in el:
                    ela = el.split(' ')
                    for el in ela:
                        if el.isdigit():
                            print(el)
                            return el
                #if 'kg' in el:
                 #   el = el.split(' ')
                 #   print('el1', el)
                 #   kg = el[-2]
                 #   print('kg', kg)
                 #   return kg
        except:
            return False

    def _mainloop(self):
        # Основной цикл работы программы, слушает порт и передает данные клиентам
        print('Запущен основной цикл отправки весов')
        #sleep(5)
        ser = Serial('/dev/ttyUSB0', bytesize=8, parity='N', stopbits=1, timeout=1, baudrate=9600)
        while True:
            data = ser.readline()
            #self.send_data(data)
            data = self.check_data(data)
            #print(data)
            #self.send_data(data)
            if data:
                 #print('TRACK. Sending', data)
                 self.send_data(bytes(data, encoding='utf-8'))
                 sleep(1)

if __name__ == '__main__':
    cps = WeightSplitter('localhost', 1488)
    cps.create_server('localhost', 1488)
    cps.start()
