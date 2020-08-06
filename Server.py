import socket
from json import dumps, loads
from datetime import datetime
from select import select
from time import sleep
from cryptography.fernet import Fernet
from base64 import b64decode,b64encode
from threading import Thread

class server:
	all=[]
	connections=[]
	host="0.0.0.0", 9090
	def __init__(self,debug=False):
		self.debug=debug
		self._connection()
		# print(self.all)

	def _connection(self):
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind(self.host)
		print(f'[{self._get_time()}] Server start on {self.host}')
		if self.debug:self._log(f'[{self._get_time()}] Server start on {host}')
		self.sock.listen(5)
		Thread(target=self._accept).start()
		# self._accept()
		self._proc()
	def _get_time(self):
		dt = datetime.now().strftime("%I:%M:%S %p")
		return dt
	def _accept(self):
		if self.debug:self._log(f'[{self._get_time()}] Ready to accept connections')
		while True:
			try:
				conn,addr=self.sock.accept()
				check = self._decode_json(conn.recv(200))
				self.all.append([conn,addr,check])
				self.connections.append(conn)
				print("Connected {}:{}".format(*addr))
				if self.debug:self._log(f'[{self._get_time()}]'+"Connected {}:{}".format(*addr))
			except:continue

	def _proc(self):
		if self.debug:self._log(f'[{self._get_time()}] Ready to accept data')
		while True:
			if len(self.connections):self._process()
			else:sleep(0.1)
	def _process(self):
		triple = select(self.connections, [], [],1)[0]
		for n in triple:
			try:
				message=n.recv(2048)
				if not message:self._conn_end(n)
				else:Thread(target=self._send_to_others,args=(n,message,),).start()
			except:
				self._conn_end(n)
	def _send_to_others(self,conn,message):
		name, key=self._name_key(conn)
		message=self._decrypt(message,key)
		for n in self.all:
			if conn is not n[0]:
				datatosend={"name":name,"message":self._encrypt(message,n[2]["key"])}
				n[0].send(dumps(datatosend).encode())
	def _log(self,what):
		with open("all.log") as f:
			f.write(f'{what}\n')
			f.close()
	def _name_key(self,conn):
		for n in self.all:
			if conn is n[0]:
				return n[2]["name"], n[2]["key"]

	def _conn_end(self,conn):
		for no,bunch in enumerate(self.all):
			if conn is bunch[0]:
				del self.all[no]
				print("Disconnected {}:{}".format(*bunch[1]))
				if self.debug:self._log(f'[{self._get_time()}]'+"Connected {}:{}".format(*bunch[1]))

		self.connections.remove(conn)

	def _decode_json(self,data:bytes):
		return loads(data.decode("ascii"))

	def _decrypt(self,message,key):
		key=b64encode(f'{key:<32}'[:32].encode())
		return Fernet(key).decrypt(message)

	def _encrypt(self,message,key):
		key=b64encode(f'{key:<32}'[:32].encode())
		return Fernet(key).encrypt(message).decode()
    
if __name__ == '__main__':
	server()
