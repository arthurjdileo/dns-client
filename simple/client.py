# PROJECT 1
# client.py
# Authors: ajd320

import sys
from multiprocessing import Queue
import socket
import threading
import time
import atexit

class Result:
	def __init__(self, domain, ip, dType, hasError):
		self.domain = domain
		self.hasError = hasError
		if not self.hasError:
			self.ip = ip
			self.type = dType
	
	def getLine(self):
		if self.hasError:
			l = self.domain + " - Error:HOST NOT FOUND"
			return l
		l = self.domain + " " + self.ip + " " + self.type
		return l

class Client:
	def __init__(self, rsHostname, rsListenPort, tsListenPort, fileName):
		self.rsHostname = rsHostname
		self.rsListenPort = rsListenPort
		self.tsListenPort = tsListenPort
		self.fileName = fileName

		self.exportedList = dict()

		self.domains = []
		self.clientChannelRS = Queue()
		self.clientChannelTS = Queue()

		# sockets
		self.serverRS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serverTS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tsConnected = False

		# threads
		self.clientTS = threading.Thread(target=self.clientThread, args=(self.clientChannelTS, True))
		self.listenTS = threading.Thread(target=self.listen, args=(self.serverTS, self.clientChannelTS))

		self.clientRS = threading.Thread(target=self.clientThread, args=(self.clientChannelRS,))
		self.listenRS = threading.Thread(target=self.listen, args=(self.serverRS,self.clientChannelRS))

		self.initSockets()

	# parses hostname file
	# output: array of domain names
	def parse(self):
		f = open(self.fileName, 'r')
		self.domains = [domain.replace('\n', '').replace('\r', '') for domain in f.readlines()]

	# connect to root server
	def initSockets(self):
		try:
			self.serverRS.connect((self.rsHostname, self.rsListenPort))
			self.listenRS.start()
		except Exception as e:
			print("failed to establish socket: %s" % e)
			exit()

	# send hosts file to root server
	def sendHosts(self):
		for d in self.domains:
			self.send(self.serverRS, (d + "\n"))

	# processes server resp and stores in queue
	# input: socket, chan
	def listen(self, server, channel):
		server.setblocking(1)
		resp = ""
		while True:
			resp += server.recv(100).decode("UTF-8")
			cmd = resp.split("\n")
			while len(cmd) > 1:
				channel.put(cmd[0])
				resp = "\n".join(cmd[1:])
				cmd = resp.split("\n")

	# processes all server messages from queue
	def clientThread(self, channel, ts=False):
		while True:
			msg = channel.get(True)
			print("RECV: " + msg + "\n"),

			# did the root server redirect us?
			if not ts and '*' in msg:
				# call ts server
				self.sendToTS(msg)
				continue

			msg = msg.split(" ")
			r = None
			# did server return failure?
			if "Error:HOST" in msg: # error
				r = Result(msg[0], None, None, True)
				self.exportedList[r.domain] = r
				continue
			r = Result(msg[0], msg[1], msg[2], False)
			self.exportedList[r.domain] = r
	
	def export(self, filename):
		lines = []
		for d in self.domains:
			if d in self.exportedList.keys():
				r = self.exportedList[d]
				lines.append(r.getLine())
			else:
				print("ERROR: couldn't find result: %s" % d)
		with open(filename, 'w') as f:
			f.writelines("%s\n" % line for line in lines)

		print("Exported: %s" % filename)

	
	# sends msg to top server
	# input: msg(str)
	def sendToTS(self, msg):
		msg = msg.split(" ")
		if not self.tsConnected:
			self.connectToTS(msg[2])
		result = msg[0] + "\n"
		self.send(self.serverTS, result)

	# setup top server connection
	def connectToTS(self, address):
		try:
			self.serverTS.connect((address, self.tsListenPort))
			self.tsConnected = True
			self.listenTS.start()
			self.clientTS.start()
		except Exception as e:
			print("failed to connect to TS server: %s. %s:%s" % (e, address, self.tsListenPort))
			exit()
		

	# send a message via sockets
	# input: server (socket), data (str)
	# output: sends a msg
	def send(self, server, data):
		server.send(data.encode())
		print("SEND: data: %s" % data),

def gracefulExit(client):
	# close sockets
	print("hit")
	client.serverRS.close()
	client.serverTS.close()
	sys.exit()

def main():
	if len(sys.argv) != 4:
		print("Invalid number of arguments.\nUse: python client.py rsHostname rsListenPort tsListenPort")
		return

	# get hostname, ports, and filename
	rsHostname = sys.argv[1]
	rsListenPort = int(sys.argv[2])
	tsListenPort = int(sys.argv[3])
	fileName = "PROJI-HNS.txt"
	
	client = Client(rsHostname, rsListenPort, tsListenPort, fileName)

	# defer
	atexit.register(gracefulExit, client)

	client.parse()

	client.clientRS.start()

	# send request via sockets
	client.sendHosts()

	# wait until all data is received
	while (len(client.exportedList) != len(client.domains)):
		continue
	
	client.export("RESOLVED.txt")
	sys.exit()

if __name__ == "__main__":
	main()
