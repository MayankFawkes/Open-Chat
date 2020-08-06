from tkinter import *
import tkinter.scrolledtext as scrolledtext
from json import dumps, loads
from cryptography.fernet import Fernet
from base64 import b64decode,b64encode
from select import select
from datetime import datetime
from time import sleep
from threading import Thread
import socket


# setup

title="Chat"

# setup end


class client:
	def __init__(self,debug=False):
		self.debug=debug
		self.issockconnected=False
	def _connect(self):
		self.ips=ip.get().split(":")
		self.names=name.get()
		self.key=enc.get()
		jj={"name":self.names,"key":self.key}
		if self.ips and self.names and self.key:self._connect_socket(jj)
		Thread(target=self._process).start()
	def _change_title(self,new_title,ip=False):
		window.title(f'{title} {new_title} {":".join(self.ips)}')
	def _connect_socket(self,data):
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.ips[0],int(self.ips[1])))
		self.sock.send(dumps(data).encode("ascii"))
		self.issockconnected=True
		self._change_title("Connected",True)
		if self.debug:self._log(f'[{self._get_time()}] Connection is connected')


	def _decrypt(self,message):
		key=b64encode(f'{self.key:<32}'[:32].encode())
		return Fernet(key).decrypt(message.encode())

	def _encrypt(self,message):
		key=b64encode(f'{self.key:<32}'[:32].encode())
		return Fernet(key).encrypt(message)

	def _disconnect(self):
		self.sock.close()
		self.issockconnected=False
		self._change_title("Disconnected")
		if self.debug:self._log(f'[{self._get_time()}] Connection is disconnected')

	def _log(self,what):
		with open("all.log") as f:
			f.write(f'{what}\n')
			f.close()
	def _get_time(self):
		dt = datetime.now().strftime("%I:%M:%S %p")
		return dt
	def _decode_json(self,data:bytes):
		return loads(data.decode("ascii"))

	def _process(self):
		while True:
			if window.state() != "normal":break
			if self.issockconnected:
				try:
					triple = select([self.sock], [], [],1)[0]
					message=triple[0].recv(2048)
					jj=self._decode_json(message)
					print(jj)
					who=jj["name"]
					mes=self._decrypt(jj["message"]).decode()
					self._print_message(who,mes)
				except:
					continue
			else:
				sleep(0.5)
	def _send_message_to_server(self,message):
		message=message.encode()
		message=self._encrypt(message)
		self.sock.send(message)
		if self.debug:self._log(f'[{_get_time()}] Message: {message} Key: {self.key}')

	def _print_message(self,who,message):
		txt.config(state="normal")
		message=f'[{self._get_time()}]<{who}> {message}\n'
		txt.insert(END,message)
		txt.config(state=DISABLED)
		txt.see("end")
	def _Get_send(self,event=""):
		text=message.get()
		if text:
			self._send_message_to_server(text)
			self._print_message("You",text)
			input_user.set('')
		return "break"
Client=client()

window = Tk()
window.title(title)
BF=Frame(window)
BF.pack(side=BOTTOM)
TF=Frame(window)
TF.pack(side=TOP)


Label(TF,text="IP:PORT").grid(row=0,padx=10,pady=10)
Label(TF,text="Name").grid(row=1,padx=10,pady=10)
Label(TF,text="Encryption Key").grid(row=1,column=2,padx=10,pady=10)
ip=Entry(TF)
ip.grid(row=0,column=1,padx=10,pady=10)

name=Entry(TF)
name.grid(row=1,column=1,padx=10,pady=10)

enc=Entry(TF)
enc.grid(row=1,column=3,padx=10,pady=10)

Button(TF,text="Connect",command=Client._connect).grid(row=0,column=2, columnspan=1,padx=10,pady=10)
Button(TF,text="Disconnect",command=Client._disconnect).grid(row=0,column=3, columnspan=1,padx=10,pady=10)


txt = scrolledtext.ScrolledText(BF, undo=True)
txt['font'] = ('arial', '10')
txt.grid(row=0,column=0,columnspan=2)
txt.config(state=DISABLED)


input_user = StringVar()
message = Entry(BF,width="70",text=input_user)
message.grid(row=1,column=0,sticky=SW,padx=10,pady=15)
message.bind("<Return>", Client._Get_send)

but = Button(BF,text="send",width=20,command=Client._Get_send)
but.grid(row=1,column=1,sticky=SE,padx=10,pady=10)

window.mainloop()
