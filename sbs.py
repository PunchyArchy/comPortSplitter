import socket
import threading
from serial import Serial
import serial.tools.list_ports
from time import sleep
from traceback import format_exc

import logging
#from terminal_parsers import *
#ports = serial.tools.list_ports.comports()
#import tp
#import terminal_parsers as tp

class comPortSplitter:
    """ Сервер для прослушивания порта USB (CPS), к которому подключено устройство с COM-портом через адаптер
     и переотправки данных подключенным к нему клиентов (Clients).
     По сути, выполняет роль сплиттера - COM > USB > CPS > Clients. """
    def __init__(self, ip, port, port_name='/dev/ttyUSB0', terminal_name='CAS', debug=False):
        self.debug = debug
        self.port_name = port_name
        self.create_server(ip, port)
        self.allConnections = []

    def start(self):
        threading.Thread(target=self.connReciever, args=()).start()
        self._mainloop()

    def create_server(self, ip, port):
        # Создает сервер
        self.show_print('Creating CPS server')
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serv.bind((ip, port))
        self.serv.listen(10)

    def connReciever(self):
        # Отдельный поток, принимающий подключения и добавляющий их в список self.allConnections для дальнейшней
        # работы
        while True:
            self.show_print('\nWaiting for client...')
            conn,addr = self.serv.accept()
            self.allConnections.append(conn)
            self.show_print('\tGot new client!')

    def _mainloop(self):
        # Основной цикл работы программы, слушает порт и передает данные клиентам
        self.show_print('Запущен основной цикл отправки весов')
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

    def make_data_aliquot(self, data):
        try:
           data = int(data)
           data = data - (data % 10)
        except: self.show_print(format_exc())
        return data
 
    def check_data(self, data, parser_func):
        if self.check_scale_disconnected(data):
            data = '17'
        else:
            data = parser_func(data)
        return data

    def check_scale_disconnected(self, data):
        data = str(data)
        if 'x00' in data:
            self.show_print('Terminal has been disconnected')
            return True

    def scale_disconnect_act(self):
        pass

    def send_data(self, data, **kwargs):
        for conn in self.allConnections:
            try:
                conn.send(data)
                #self.show_print('Sent to the client with success')
            except:
                self.show_print('Failed to send weight to client')
                self.allConnections.remove(conn)

    def make_str_tuple(self, msg):
        return ' '.join(map(str, msg))

    def show_print(self, *msg, debug=False):
        msg = self.make_str_tuple(msg)
        if debug and self.debug:
            print(msg)
        elif not debug:
            print(msg)

class WeightSplitter(comPortSplitter):
    def __init__(self, ip, port, port_name='/dev/ttyUSB0', terminal_name='CAS', debug=False):
        super().__init__(ip, port, port_name, terminal_name, debug=debug)
        self.parser_func = self.define_parser(terminal_name)
        threading.Thread(target=self.sending_thread, args=(1,)).start()
        self.smlist = ['5']

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
            return '4'

    def send_data(self, data, **kwargs):
        #self.show_print('sending data', data)
        try:
            data = bytes(data, encoding='utf-8')
            super().send_data(data, **kwargs)
        except TypeError:
            self.reconnect_logic()

    def reconnect_logic(self):
        self.show_print('Терминал выключен!')
        self.port.close()
        self._mainloop()


    def check_send_data(self):
        self.show_print('Checking data b4 sendig...', debug=True)
        data = self.smlist[-1]
        if data != None:
            return data
        else:
            return '0'

    def sending_thread(self, timing=1):
        while True:
            sleep(timing)
            self.send_data(self.smlist[-1])

    def _mainloop(self):
        # Основной цикл работы программы, слушает порт и передает данные клиентам
        self.show_print('Запущен основной цикл отправки весов')
        sleep(5)
        self.port = Serial(self.port_name, bytesize=8, parity='N', stopbits=1, timeout=1, baudrate=9600)
        while True:
            data = self.port.readline()
            #self.show_print('data -', data)
            #data = b'ST,GS,1\xbe,       10000 kg\r\n'
            if data:
                data = self.check_data(data, self.parser_func)
                self.prepare_data_to_send(data)
            else:
                 self.reconnect_logic()

    def prepare_data_to_send(self, data):
        self.smlist.append(data)


class HermesSplitter(WeightSplitter):
    def __init__(self, ip, port, port_name='/dev/ttyUSB0', terminal_name='CAS', debug=False):
        super().__init__(ip, port, debug=debug)
        self.active = False
        self.kf = 0
        self.hermes_weight = 0
        self.avg_tara = 0
        self.max_brutto = 0

    def set_kf(self, kf):
        self.show_print('setting kf', kf, debug=True)
        self.kf = 1.0 + kf

    def set_debug(self, debug):
        self.debug = debug

    def set_status(self, status):
        self.show_print('settings status', status, debug=True)
        self.active = status
        if not status:
            self.hermes_weight = 0

    def set_avg_tara(self, avg_tara):
        try:
            self.avg_tara = int(avg_tara)
        except:
            self.show_print(self.avg_tara, '-  ЭТО НЕ ЧИСЛО')
            self.avg_tara = 0

    def set_max_brutto(self, max_brutto):
        try:
            self.max_brutto = int(max_brutto)
        except:
            self.show_print(self.max_brutto, '-  ЭТО НЕ ЧИСЛО')
            self.max_brutto = 0
        self.netto_max = self.max_brutto - self.avg_tara

    def prepare_data_to_send(self, data):
        #self.show_print('PREPARING DATA TO SEND')
        #try:
        #    data = int(data)
        #except:
        #    self.show_print(format_exc())
        self.smlist.append(data)

    def send_data(self, data):
        data = self.make_magic(data)
        super().send_data(data)

    def set_avg_weigth(self, weight):
        try:
            self.avg_weight = int(weight)
        except:
            self.show_print(self.avg_weight, '-  ЭТО НЕ ЧИСЛО')
            self.avg_weight = 0

    def make_magic(self, data):
        try:
            if self.active and data.isdigit() and self.avg_tara != 0 and self.max_brutto != 0 and self.avg_weight != 0:
                self.show_print('It`s active! KF', self.kf, debug=True)
                self.show_print('Increasing. data', data, debug=True)
                self.show_print('avg_tara', self.avg_tara, debug=True)
                self.show_print('avg_weight', self.avg_weight, debug=True)

                # 3 положение
                approx_netto = float(data) - float(self.avg_tara)
                self.show_print('approximate netto is', approx_netto)
                delta_k = approx_netto * float(self.kf) - approx_netto
                self.show_print('new delta_k', delta_k, debug=True)

                # 1 Положение
                avg_delta = self.avg_weight * self.kf - self.avg_weight
                if float(delta_k) > float(avg_delta):
                    delta_k = float(avg_delta)
                self.show_print('avg_delta', avg_delta, debug=True)

                # 5 положение
                if int(delta_k) > 0:
                    new_data = float(data) + float(delta_k)
                else:
                    new_data = data

                # 2 положение
                if float(new_data) > float(self.max_brutto):                     # 2 Положение
                    new_data = data
                new_data = str(self.make_data_aliquot(new_data))
                self.show_print('New data', new_data)
                self.show_print('Old data', data)
                self.hermes_weight = int(new_data) - int(data)
                if self.debug:
                    new_data = data
            else:
                new_data = data
        except:
            new_data = data
            self.show_print(format_exc())
        return str(new_data)

    def make_netto_less(self, added, br_diff, kf):
        delta_k = added * kf
        if delta_k > br_diff: #решить с кэфом
            over = delta_k - br_diff
            delta_k = delta_k - over * 1.1
        return delta_k

if __name__ == '__main__':
    cps = WeightSplitter('localhost', 1488)
    cps.start()
