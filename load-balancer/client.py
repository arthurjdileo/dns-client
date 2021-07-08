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
	def __init__(self, lsHostname, lsListenPort, fileName):
		self.lsHostname = lsHostname
		self.lsListenPort = lsListenPort
		self.fileName = fileName

		self.exportedList = dict()

		self.domains = []
		self.clientChannelLS = Queue()

		# sockets
		self.serverLS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# threads
		self.clientLS = threading.Thread(target=self.clientThread, args=(self.clientChannelLS,))
		self.listenLS = threading.Thread(target=self.listen, args=(self.serverLS,self.clientChannelLS))

		self.initSockets()

	# parses hostname file
	# output: array of domain names
	def parse(self):
		f = open(self.fileName, 'r')
		self.domains = [domain.replace('\n', '').replace('\r', '') for domain in f.readlines()]

	# connect to root server
	def initSockets(self):
		try:
			self.serverLS.connect((self.lsHostname, self.lsListenPort))
			self.listenLS.start()
		except Exception as e:
			print("failed to establish socket: %s" % e)
			exit()

	# send hosts file to root server
	def sendHosts(self):
		msg = ""
		for d in self.domains:
			msg = msg + d + " "
		msg = msg + "\n"
		self.send(self.serverLS, msg)

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
	def clientThread(self, channel):
		while True:
			msg = channel.get(True)
			print("RECV: " + msg + "\n"),

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

	# send a message via sockets
	# input: server (socket), data (str)
	# output: sends a msg
	def send(self, server, data):
		server.send(data.encode())
		print("SEND: data: %s" % data),

def gracefulExit(client):
	# close sockets
	client.serverLS.close()
	sys.exit()

def main():
	if len(sys.argv) != 3:
		print("Invalid number of arguments.\nUse: python client.py lsHostname lsListenPort")
		return

	# get hostname, ports, and filename
	lsHostname = sys.argv[1]
	lsListenPort = int(sys.argv[2])
	fileName = "PROJ2-HNS.txt"
	
	client = Client(lsHostname, lsListenPort, fileName)

	# defer
	atexit.register(gracefulExit, client)

	client.parse()

	client.clientLS.start()

	# send request via sockets
	client.sendHosts()

	# wait until all data is received
	while (len(client.exportedList) != len(client.domains)):
		continue
	
	client.export("RESOLVED.txt")
	sys.exit()

if __name__ == "__main__":
	main()
