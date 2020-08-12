from tkinter import *
import tkinter.scrolledtext as scrolledtext
from json import dumps, loads
from cryptography.fernet import Fernet
from base64 import b64decode,b64encode
from select import select
from datetime import datetime
from time import sleep
from threading import Thread
import socket, pyaudio
from io import BytesIO
import atexit, tempfile, binascii, os



# setup

title="Chat"

# setup end


class client:
	chunk_size = 1024
	audio_format = pyaudio.paInt16
	channels = 1
	rate = 20000
	MY_SUFFIX = b'"}'
	buffer = bytearray()
	def __init__(self,debug=False):
		self.player = pyaudio.PyAudio()
		self.debug=debug
		self.issockconnected=False
		self.isrecord = False
		self.isplay = False
	def __del__(self):
		self.issockconnected=False
		self.isrecord = False
		self.isplay = False
	def _connect(self):
		self.ips=ip.get().split(":")
		self.names=name.get()
		self.key=enc.get()
		jj={"name":self.names,"key":self.key}
		if self.ips and self.names and self.key:self._connect_socket(jj)
		Thread(target=self._process,daemon=True).start()
	def _change_title(self,new_title,ip=False):
		window.title(f'{title} {new_title} {":".join(self.ips)}')
	def _connect_socket(self,data):
		if not self.issockconnected:
			self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect((self.ips[0],int(self.ips[1])))
			self.sock.send(dumps(data).encode("ascii"))
			self.issockconnected=True
			self._change_title("Connected",True)
			if self.debug:self._log(f'[{self._get_time()}] Connection is connected')
		else:
			if self.debug:self._log(f'[{self._get_time()}] Socket is already connected')


	def _decrypt(self,message):
		key=b64encode(f'{self.key:<32}'[:32].encode())
		return Fernet(key).decrypt(message.encode())

	def _encrypt(self,message):
		key=b64encode(f'{self.key:<32}'[:32].encode())
		return Fernet(key).encrypt(message).decode()

	def _disconnect(self):
		self.sock.close()
		self.issockconnected=False
		self._change_title("Disconnected")
		self.head(reset=True)
		self.mic(reset=True)
		if self.debug:self._log(f'[{self._get_time()}] Connection is disconnected')

	def _record(self):
		jdau={"type":"voice","message":""}
		recording_stream = self.player.open(format=self.audio_format, channels=self.channels,
			rate=self.rate, input=True, frames_per_buffer=self.chunk_size)
		while self.isrecord and window.state() == "normal":
			voice=recording_stream.read(5000)
			jdau["message"]=self._encrypt(voice)
			try:
				self.sock.send(dumps(jdau).encode())
			except:
				self._disconnect()
	def _filter(self,pkt):
		self.buffer.extend(pkt)
		if pkt[-2:] == self.MY_SUFFIX:
			for n in self.buffer.replace(b' ',b'').replace(b'}{',b'} {').split(b' '):
				try:
					aa=loads(n)
					self._action(aa)
				except:
					print("Invalid JSON")
			self.buffer = bytearray()

	def _action(self,check):
		if check["type"]=="message":
			who=check["name"]
			mes=self._decrypt(check["message"]).decode()
			self._print_message(who,mes)
		elif check["type"]=="voice":
			mes=self._decrypt(check["message"])
			# self._plays(mes)
			Thread(target=self._plays,args=(mes,)).start()
			print("got voice packet")
		else:
			print("Invalid Packet")

	def _play_init(self):
		self.playing_stream = self.player.open(format=self.audio_format, channels=self.channels,
			rate=self.rate, output=True, frames_per_buffer=self.chunk_size)

	def _plays(self,voice):
		self.playing_stream.write(voice)

	def _log(self,what):
		with open("all.log","a") as f:
			f.write(f'{what}\n')
			f.close()
	def _get_time(self):
		dt = datetime.now().strftime("%I:%M:%S %p")
		return dt
	def _decode_json(self,data:bytes):
		return loads(data.decode("ascii"))

	def _process(self):
		while window.state() == "normal":
			if self.issockconnected:
				try:
					triple = select([self.sock], [], [])[0]
					message=triple[0].recv(2048)
					self._filter(message)
				except:
					self._disconnect()
			else:
				sleep(0.5)
	def _send_message_to_server(self,message):
		if self.issockconnected:
			message=message.encode()
			message=self._encrypt(message)
			jdau = {"type":"message","message":message}
			self.sock.send(dumps(jdau).encode("ascii"))
			if self.debug:self._log(f'[{_get_time()}] Message: {message} Key: {self.key}')
		else:
			if self.debug:
				print(f'[{self._get_time()}] Cannot send message socket aint connected')
				self._log(f'[{self._get_time()}] Cannot send message socket aint connected')

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
	def _send_head_settings(self,set):
		if self.issockconnected:
			jdau={"type":"setting","voice":set}
			self.sock.send(dumps(jdau).encode())
		else:
			if self.debug:
				print(f'[{self._get_time()}] cannot send microphone settings socket is not connected')
				self._log(f'[{self._get_time()}] cannot send microphone settings socket is not connected')

	def head(self,reset=False):
		if headB.config('relief')[-1] == 'sunken' or reset:
			headB.config(relief=FLAT)
			headB.config(image=headoff)
			headB.image = headoff
			self.isplay=True
			if not reset:
				self._send_head_settings("off")
		else:
			if self.issockconnected:
				self.isplay=True
				self._play_init()
				self._send_head_settings("on")
				headB.config(image=headon)
				headB.image = headon
				headB.config(relief="sunken")
		print(headB.config("relief")[-1])

	def mic(self,reset=False):
		if micB.config('relief')[-1] == 'sunken' or reset:
			self.isrecord=False
			micB.config(relief=FLAT)
			micB.config(image=micoff)
			micB.image = micoff
		else:
			if self.issockconnected:
				self.isrecord=True
				Thread(target=self._record).start()
				micB.config(image=micon)
				micB.image = micon
				micB.config(relief="sunken")
		print(micB.config("relief")[-1])

def _image_get(img):
	headoff=b"iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAAAAADhgtq/AAAABGdBTUEAALGPC/xhBQAAAAJiS0dEAP+Hj8y/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5AgGFzI19rDCjgAAAZNJREFUKM9j+IYCvgIBlMmAJPz9+/dvKDIffoAYP35+ePLw1befcHUMP65Hrvry4/v3c00euhoWyWte/4TLnDPhLXn8plWGgYGRiYGBw+fED5hpP+6kc9mFsDIZVC1dOzlYgEFt9w+YPT8+LVBhYM599PPXr1+fNukz6F35AXPb9x+XQtl9z/78DmT/OqHOkPEFJvOlf9urPgmF2WBH/prNInnuB0Tm+yNtsQO/DzlxJt74CeLpMUz/BZH5dVaI//ifX0+r+HXXfv3x40cUQyFE5vvrUibZbT1Pf37dZAh0/4aleQwGR76DZH5OZmFQbBU5+vPbz9vpXLb6LjkMDFZPv4P0pDIwKDYLHfkJdb9lPAOD2PkfIJkkuMy37z8vhHLzMzCInP2JJvPt28/3/VIMDKLnMGW+HHh62IWJf+8vkEwaikxE4ttnNYI6W74D3TabHeg24aMQma/B9q19rzaZ9v8A6nk3I6H4QNPj75B4XTF3UfL+X4/ffgeFDjAov//4Do2wH8Aw+wqMeJR0gAqoKwMA00jO1dt+yLkAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjAtMDgtMDZUMjM6NTA6NTMtMDQ6MDBbbHYBAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIwLTA4LTA2VDIzOjUwOjUzLTA0OjAwKjHOvQAAAABJRU5ErkJggg=="
	headon=b"iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAAAAADhgtq/AAAABGdBTUEAALGPC/xhBQAAAAJiS0dEAP+Hj8y/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5AgGFzMl8hzjqwAAATNJREFUKM+d0r1qwlAUB/CTgAjV0TcQRBzayQwuToEWfAAhIDiIQtuIo6tTO/gC4gPYvkDzCK2TmzgbAiY2qElzbq5Lk3sTNU0n/9OF3z2c+3HAS+QnDF+Cl6a/QigeDkgxgpMgWU06jUZnsiKYELIdl0QIIpbGW3IhxGhnhGJrNGoVhUzbICfB/aOQHyw9Sr3lIC887TEW/y2XfXXZTuK+ZHPvfiT4fQ/NXdQYd014sJGLPy/kNBqfnn7cFOY+l+MMKvpZ9IowOzJBswf1L83l4GqfdeiZyGqGIsjqrcEaoXH3LIM4DGvQqgHI3fKay7rclQFqFgayqV6KzqS6uVZMKS2SGYjnKGlRnPDUZKFI/alqc7HVaV9SFoTdhziW7TrxGziubTkk/h9MDgP+NyHnXCO/brjdpyx4uXAAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjAtMDgtMDZUMjM6NTE6MzctMDQ6MDCGjjCrAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIwLTA4LTA2VDIzOjUxOjM3LTA0OjAw99OIFwAAAABJRU5ErkJggg=="
	micon=b"iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAAAAADhgtq/AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfkCAYPISoIYnwhAAAByUlEQVQoz2P48f3HN6yA4UbN6Z8gxvdfEPAdLjOB3eg4UOr7k+UzQGDZY5gUw6sKNt2DP79/TGJlBAHW+A8wme8fGjjUd/96pKo4fcH8BTOUlR9ANTF8+/6pg1tp22MVk7e/f/1+b654/wdM5tv3L/18cjNUjF9+//b9tRmyzLfvX6cL8nOavsKU+fb923xRBhOsMj9+LJPinfb1O0Tm+3e4zLunH3+sleXr//IDJPPp6VuYzM8putt+/tyqxN3x+Y2Z4qNdehN/QmV+1TIsf7n4wx51joan5oqPVzNUwmXqGFY+0a39dUiXLVdP6fEaxiq4TD3D8ufq4j1vTxoxsWo9W8VQA5eZwdDwo0qQr+j9OUsG06etDFN/QWV+XJBWPfn51L6Db/9edmAJUJM+/wPm6m+d7JoTj5w6dfzEq5tuDIwNPxA+/dAlw8jJwyfA53/3rh9TwL2fcD3fv52flJ/jwGCXu/Hng1BGr1s/YTJAu759+TGFYcKPT59+PIlhcr76Eybz/XmKh6c2g5anR9LTn89TmGwu/ITJPHaUl1dQVpSXt3/0/cerHBazwzDTvjy8CwEPvwCNflsiOQMm8+0HDIA5r/d9AAAHeL/9JSghkQAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMC0wOC0wNlQxNTozMzo0Mi0wNDowMO639m0AAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjAtMDgtMDZUMTU6MzM6NDItMDQ6MDCf6k7RAAAAAElFTkSuQmCC"
	micoff=b"iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAQAAABu4E3oAAAABGdBTUEAALGPC/xhBQAAAAJiS0dEAP+Hj8y/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5AgGDx8Z9ncGSgAAAbxJREFUOMuVlLFrFFEQxn+zLzG5I5xKYhFJIYrIidoIaYSkSRG1OSz8AwRB7LXTShCClRaCWh6xsbMPgSCkTjQxSCwkGAIm5MBcQtzbzyJ373bfbg59r3jMzH7zZr795llT/OfqCx2Gy9gt1BtibLNAw1uj3KAcgppK74buqV/md1kzOlD2G0v3YvxiikMeU0JE/OQZU9SDUoPChBjmLhWEY5UX5NnJtQ8iJkYkxIWMRUVOC85/gCg4jynMCrPKx7pwf8s+OxxSvJrs8CeEOGaZ5lObzu5tBjjq3GTRUx11Qlss0whK61ibLKViuV6E4XAIR9TuIcJSyTKQhAjHBs85wZEW9nAYSaZYDxkF1qhxh9e89GmGqZHwjRJnPGdtjUV85TZl6lxmld+e3BEu8pH7XOUDJzverixf8ZTzPOA6Az7jHnO8ocVbbtHynLclva9dzWhMppKGVNEpVTSkAUW6ovfHid8QayywTovPzDOhazZIlUnGSIoEc0RnlUsk9PGOedXih/2xZyz1t7IjtssTNjB+8IUq5xDjPOo9YjHrfAeMCxywApzNKc6yj1LCdjBYg5zuDckPkHJT8xckEMliWwxQlgAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMC0wOC0wNlQxNTozMToyNS0wNDowMOmKEVkAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjAtMDgtMDZUMTU6MzE6MjUtMDQ6MDCY16nlAAAAAElFTkSuQmCC"
	return b64decode(locals()[img])
iconhexdata = "0000010001001919000001002000500A0000160000002800000019000000320000000100200000000000C4090000D70D0000D70D00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002B0000001D0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000045000000DB0000008600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000045000000DF000000FF00000098000000000000000000000000000000000000000000000000000000000000000000000020000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000044000000DF000000FF000000FF0000009700000000000000000000000000000000000000000000000000000000000000000000008C000000E60000005000000000000000010000000B0000000B0000000A0000000A0000000A0000000900000046000000DF000000FF000000FF000000FF0000009B000000090000000A00000002000000000000000000000000000000000000000000000098000000FF000000E6000000500000000100000065000000C2000000C7000000C7000000C6000000C7000000EC000000FF000000FF000000FF000000FF000000E7000000C2000000C2000000A0000000340000000000000000000000000000000000000097000000FF000000FF000000E60000004F000000110000007E000000A3000000A1000000A1000000A10000009F0000009E0000009E000000A1000000C4000000F8000000FF000000FF000000FF000000CF000000000000000700000012000000110000009F000000FF000000FF000000FF000000E6000000530000000F00000012000000120000001200000012000000120000001200000012000000100000000E0000005E000000E8000000FF000000FF000000FE0000003F000000B0000000D0000000D0000000EC000000FF000000FF000000FF000000FF000000F0000000D1000000D0000000D0000000D0000000D0000000D0000000D0000000D1000000CC000000870000000D00000070000000FD000000FF000000FF000000D6000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF0000006800000020000000E4000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF0000009500000014000000D5000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000F4000000970000007C0000007D0000007D0000007D0000007D0000007D0000007C000000B0000000FE000000FF000000FF000000FF000000FF000000FF000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000E7000000440000001E00000020000000200000002000000020000000200000001D0000006B000000FB000000FF000000FF000000FF000000FF000000FF000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000FF000000F0000000E7000000E7000000E7000000E7000000E7000000E7000000E7000000F5000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000F20000008A0000006D0000006E0000006E0000006E0000006E0000006E0000006E0000006D0000006D0000006D0000006D0000006D0000006C000000B5000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000E90000004D000000290000002A0000002A0000002A0000002A0000002A0000002A0000002A0000002A0000002A0000002A0000002A000000280000008B000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000FF000000F5000000ED000000ED000000ED000000ED000000ED000000ED000000ED000000ED000000ED000000ED000000EF000000ED000000ED000000F9000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000F00000007B0000005C0000005E0000005E0000005E0000005E0000005E0000005E0000005E0000005E0000005C000000A3000000FF000000FF000000FF000000FF000000FF0000009600000014000000D4000000FF000000FF000000FF000000FF000000EB000000580000003500000036000000360000003600000036000000360000003600000036000000360000003400000087000000FE000000FF000000FF000000FF000000FF0000009600000014000000D5000000FF000000F2000000FF000000FF000000FF000000F8000000F4000000F4000000F4000000F4000000F4000000F4000000F4000000F4000000F4000000F4000000FC000000FF000000FF000000FF000000FF000000FF0000009600000013000000D2000000EF00000080000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF0000009700000005000000430000003500000005000000EF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000FF000000820000000000000000000000000000000000000073000000E3000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F5000000F4000000C30000002900000000000000000000000000000000000000030000002F0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004C0000004D000000460000001A0000000000000000000000000000000000000000FFFF0180FFFE0180C0FC0180C0000000C0000000C000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000018000000180"

def on_closing(iconfile):
	try:
		os.remove(iconfile.name)
	except Exception:
		pass
with tempfile.NamedTemporaryFile(delete=False) as iconfile:
	iconfile.write(binascii.a2b_hex(iconhexdata))
	
atexit.register(lambda file=iconfile: on_closing(file))


Client=client(debug=True)

window = Tk()
window.iconbitmap(iconfile.name)
window.resizable(False, False)
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

headoff = PhotoImage(data=_image_get("headoff"))
headon = PhotoImage(data=_image_get("headon"))

micon = PhotoImage(data=_image_get("micoff"))
micoff = PhotoImage(data=_image_get("micon"))

headB = Button(TF,image=headoff, relief=FLAT,command=Client.head)
headB.grid(row=1,column=4,padx=15,pady=15)


micB = Button(TF,image=micoff, relief=FLAT,command=Client.mic)
micB.grid(row=0,column=4,padx=15,pady=15)





txt = scrolledtext.ScrolledText(BF, undo=True)
txt['font'] = ('arial', '10')
txt.grid(row=0,column=0,columnspan=3)
txt.config(state=DISABLED)


input_user = StringVar()

Label(BF,text="Message: ").grid(row=1,padx=10,pady=15)
message = Entry(BF,width="70",text=input_user)
message.grid(row=1,column=1,sticky=SW,padx=10,pady=15)
message.bind("<Return>", Client._Get_send)

but = Button(BF,text="send",width=20,command=Client._Get_send)
but.grid(row=1,column=2,sticky=SE,padx=10,pady=10)

window.mainloop()
