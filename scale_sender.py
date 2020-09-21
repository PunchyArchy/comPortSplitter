from serial import Serial
from time import sleep
import socket
import threading

class Tcp_Sender():
	def __init__(self):
		#self.sock = socket.socket()
		self.count = 0
		self.connectCm = False
		self.connectAR = False
	
	def connect_to_watchman(self):
		while 1:
			#try:
			#print('c')
			self.sock = socket.socket()
			#print('c1')
			self.sock.connect(('192.168.100.109',2290))
			print('connected to AR')
			break
			#except:
				#sleep(1)
				#print('Have no connection with Watchman. Retrying..')

	def connect_to_watchman_cm(self):
		while 1:
			sleep(10)
			print('State -', self.connectCm)
			try:
				self.makeConnect()
			except:
				sleep(3)
				print('Have no connection with Watchman-CM. Retrying..')

	def makeConnect(self):
		self.sockcm = socket.socket()
		self.sockcm.connect(('localhost',2296))
		print('Connected to MC')
	
	def begin_lis(self):
		while 1:
			self.count += 1
			sleep(1)
			ser = Serial('COM1', bytesize=8, parity='N', 
				stopbits=1, timeout=1)
			data = ser.readline()
			if len(str(data)) < 4:
				data = b'too short msg'
			print(data)
			self.sock.send(data)
			try:
				self.sockcm.send(data)
			except:
				print('Failed to send data to WCM')
			ser.close()
			print('count is',self.count)
			if self.count % 10 == 0:
				self.sock.close()
				break

	def launch_operate(self):
		threading.Thread(target=self.connect_to_watchman_cm,args=()).start()
		while 1:
			try:
				print('new stream')
				self.connect_to_watchman()
				self.begin_lis()
			except:
				sleep(3)
				print('Error.. Retrying in 3 seconds..')

prg = Tcp_Sender()
prg.launch_operate()