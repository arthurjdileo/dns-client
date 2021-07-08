# PROJECT 1
# ls.py
# Authors: ajd320

import sys
import socket
from multiprocessing import Queue
import threading
import atexit
import time

# Contains a resolved domain address
class Record:
	def __init__(self, domain, ip, dType):
		self.domain = domain
		self.ip = ip
		self.type = dType

	def __repr__(self):
		return "RECORD: domain: %s, ip: %s, type: %s" % (self.domain, self.ip, self.type)

class Result:
	def __init__(self, requestor, domain, ip, dType):
		if not requestor: self.requestor = requestor
		else: self.requestor = int(requestor)
		self.domain = domain
		self.ip = ip
		self.type = dType
	
	def getLine(self):
		return (self.domain + " " + self.ip + " " + self.type)
	
	def __repr__(self):
		if not self.requestor: return "Null"
		return "RESULT: req: %d, domain: %s, ip: %s, type: %s" % (self.requestor, self.domain, self.ip, self.type)

# Contains ts server
class TSClient:
	def __init__(self, host, port, tsID, channel):
		self.host = host
		self.port = port
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.id = tsID
		self.channel = channel
		self.listenTS = threading.Thread(target=self.listen)

	def connect(self):
		self.server.connect((self.host, self.port))
		self.listenTS.start()

	# send a message via sockets
	# input: data (str)
	# output: sends a msg
	def send(self, data):
		self.server.send(data.encode())
		print("SEND %s: data: %s" % (self.id, data)),
	
	# processes server resp and stores in queue
	# input: socket, chan
	def listen(self):
		self.server.setblocking(1)
		resp = ""
		while True:
			resp += self.server.recv(100).decode("UTF-8")
			cmd = resp.split("\n")
			while len(cmd) > 1:
				self.channel.put(cmd[0])
				resp = "\n".join(cmd[1:])
				cmd = resp.split("\n")

# Connected client info
class Client:
	# client obect, IP address, client id
	def __init__(self, client, address, idNum):
		self.client = client
		self.address = address
		self.id = idNum

	def __repr__(self):
		return "CLIENT: id: %d, addr: %s" % (self.id, self.address)

# contains requests
class Request:
	# client id, domain
	def __init__(self, cid, domains):
		self.id = cid
		self.domains = domains

	def __repr__(self):
		return "GET: id: %d, domains: %s" % (self.id, str(self.domains))

# root name server
class NameServer:
	def __init__(self, port, ts1Host, ts1Port, ts2Host, ts2Port):
		self.ts = [] # contain ts servers
		self.clients = []
		self.exportedList = dict()
		self.domains = {}
		# socket
		self.port = int(port)
		self.backlog = 1 # max clients
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.initSockets()
		self.listenThread = None

		# server
		self.serverChannel = Queue()
		# ts
		self.ts1Channel = Queue()
		self.ts2Channel = Queue()

		self.clientTS1 = threading.Thread(target=self.clientThread, args=(self.ts1Channel,))
		self.clientTS2 = threading.Thread(target=self.clientThread, args=(self.ts2Channel,))

		self.setupTS(ts1Host, ts1Port, ts2Host, ts2Port)

		print("socket open for connection on :%d" % (self.port))

	# connects to clients via sockets
	# output: stores clients in arr
	def waitForConnections(self):
		while True:
			client, address = self.server.accept()
			c = Client(client, address, len(self.clients)+1)
			self.clients.append(c)
			print("New connection established from: %s:%s" % (address[0], address[1]))
			self.domains[len(self.clients)] = []
			self.exportedList[len(self.clients)] = {}

			self.listenThread = threading.Thread(target=self.listen, args=(c,))
			self.listenThread.start()
	
	# listens to client and stores in a queue
	# input: client object
	# out: processes data and stores in serverChannel queue
	def listen(self, c):
		c.client.setblocking(1)
		resp = ""
		while True:
			resp += c.client.recv(100).decode("UTF-8")
			cmd = resp.split("\n")
			while len(cmd) > 1:
				tmp = cmd[0].split(" ")
				tmpArr = []
				for d in tmp:
					tmpArr.append(d)
				req = Request(c.id, tmpArr)
				self.serverChannel.put(req)
				resp = "\n".join(cmd[1:])
				cmd = resp.split("\n")

	# thread to get from queue and act on it
	def serverThread(self):
		while True:
			msg = self.serverChannel.get(True, None)
			# if len(self.ts) == 0:
			# 	self.send(msg.id, msg.domain + " - Error:HOST NOT FOUND")
			# 	continue
			msg.domains = msg.domains[:-1]
			for domain in msg.domains:
				if domain == '': continue
				self.domains[msg.id].append(domain)
				self.exportedList[msg.id][domain] = Result(None, None, None, None)
				# send to both ts servers
				# if there is no ts defined

				# send to TS1 and TS2
				for ts in self.ts:
					ts.send((str(msg.id) + " " + domain + "\n"))
			
			time.sleep(3)
			for d in self.domains[msg.id]:
				if d in self.exportedList[msg.id] and self.exportedList[msg.id][d].requestor != None:
					r = self.exportedList[msg.id][d]
					self.send(msg.id, (r.domain + " " + r.ip + " " + r.type + "\n"))
				else:
					self.send(msg.id, (d + " - Error:HOST NOT FOUND\n"))
			
	# processes all server messages from queue
	def clientThread(self, channel):
		while True:
			msg = channel.get(True)
			msg = msg.split(" ")
			r = Result(int(msg[0]), msg[1], msg[2], msg[3])
			self.exportedList[r.requestor][r.domain] = r

	def setupTS(self, ts1Host, ts1Port, ts2Host, ts2Port):
		ts1 = TSClient(ts1Host, ts1Port, 1, self.ts1Channel)
		ts2 = TSClient(ts2Host, ts2Port, 2, self.ts2Channel)
		self.ts.append(ts1)
		self.ts.append(ts2)
		ts1.connect()
		ts2.connect()
		self.clientTS1.start()
		self.clientTS2.start()

	# sends data to a client
	# input: idNum (int), data (str)
	# output: sends data via socket
	def send(self, idNum, data):
		c = self.getClientByID(idNum)
		if c == None:
			print("Invalid client ID: ", idNum)
			return
		
		c.client.send(data.encode("UTF-8"))
		print("SEND: id: %s, data: %s" % (idNum, data))

	# bind server and listen
	def initSockets(self):
		try:
			self.server.bind(('', self.port))
			self.server.listen(self.backlog)
			self.hostname = socket.gethostname()
		except Exception as e:
			print("failed to establish socket: %s" % e)
			exit()
		# self.ip = socket.gethostbyname(self.hostname)
	
	def printNS(self):
		for ts in self.ts:
			print(self.ts.ts)
	
	# gets client object by client id
	# input: id (int)
	# output: client object, None for error
	def getClientByID(self, idNum):
		for c in self.clients:
			if c.id == idNum:
				return c
		return None

def gracefulExit(ls):
	# close socket
	ls.server.close()
	exit()

# python ls.py lsListenPort ts1Hostname ts1ListenPort ts2Hostname ts2ListenPort
def main():
	if len(sys.argv) != 6:
		print("Invalid number of arguments.\nUse: python ls.py lsListenPort ts1Hostname ts1ListenPort ts2Hostname ts2ListenPort")
		return

	# get args
	lsListenPort = sys.argv[1]
	ts1Host = sys.argv[2]
	ts1Port = int(sys.argv[3])
	ts2Host = sys.argv[4]
	ts2Port = int(sys.argv[5])

	# setup root server
	ls = NameServer(lsListenPort, ts1Host, ts1Port, ts2Host, ts2Port)

	# ls.printRecords()
	# ls.printNS()

	# setup listening thread
	listen = threading.Thread(target=ls.serverThread)
	listen.start()

	# wait for new connections
	ls.waitForConnections()

	# defer
	atexit.register(gracefulExit, ls, listen)

if __name__ == "__main__":
	main()
