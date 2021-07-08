# PROJECT 1
# rs.py
# Authors: ajd320

import sys
import socket
from multiprocessing import Queue
import threading
import atexit

# Contains a resolved domain address
class Record:
	def __init__(self, domain, ip, dType):
		self.domain = domain
		self.ip = ip
		self.type = dType

	def __repr__(self):
		return "RECORD: domain: %s, ip: %s, type: %s" % (self.domain, self.ip, self.type)

# Contains other name server
class OtherNS:
	def __init__(self, ns):
		self.ns = ns

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
	def __init__(self, cid, domain):
		self.id = cid
		self.domain = domain

	def __repr__(self):
		return "GET: id: %d, domain: %s" % (self.id, self.domain)

# root name server
class NameServer:
	def __init__(self, fileName, port):
		self.fileName = fileName
		self.dns = dict()
		self.ns = None # only one NS
		self.clients = []
		# socket
		self.port = int(port)
		self.backlog = 1 # max clients
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.initSockets()
		self.listenThread = None

		# server
		self.serverChannel = Queue()

		print("socket open for connection on :%d" % (self.port))

	# connects to clients via sockets
	# output: stores clients in arr
	def waitForConnections(self):
		while True:
			client, address = self.server.accept()
			c = Client(client, address, len(self.clients)+1)
			self.clients.append(c)
			print("New connection established from: %s:%s" % (address[0], address[1]))

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
				req = Request(c.id, cmd[0])
				self.serverChannel.put(req)
				resp = "\n".join(cmd[1:])
				cmd = resp.split("\n")

	# thread to get from queue and act on it
	def serverThread(self):
		while True:
			msg = self.serverChannel.get(True, None)
			# lookup domain
			record = self.lookup(msg.domain)
			if not record:
				# if there is no ns defined
				if not self.ns:
					self.send(msg.id, msg.domain + " - Error:HOST NOT FOUND")
					continue
				# send to TS
				result = msg.domain + " * " + self.ns.ns + "\n"
				self.send(msg.id, result)
				continue
			result = msg.domain + " " + record.ip + " " + record.type + "\n"
			self.send(msg.id, result)

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

	# lookup domain
	# input: domain name
	# output: record object
	def lookup(self, domain):
		return self.dns.get(domain.lower())

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

	# parses file and store results
	# output: stores record objects in self.dns
	# and OtherNS objects in self.ns
	def parse(self):
		f = open(self.fileName, 'r')
		records = []
		# split by line and by space
		for l in f.read().splitlines():
			records.append(l.split(" "))
		# append to dns list
		for record in records:
			# is it an NS?
			if "-" in record:
				n = OtherNS(record[0])
				self.ns = n
				continue

			r = Record(record[0], record[1], record[2])
			# key is lowercase, result is case senstitive
			self.dns[record[0].lower()] = r
	
	def printRecords(self):
		for r in self.dns.values():
			print(r.domain, r.ip, r.type)
	
	def printNS(self):
		print(self.ns.ns)
	
	# gets client object by client id
	# input: id (int)
	# output: client object, None for error
	def getClientByID(self, idNum):
		for c in self.clients:
			if c.id == idNum:
				return c
		return None

def gracefulExit(rs):
	# close socket
	rs.server.close()
	exit()

def main():
	if len(sys.argv) != 2:
		print("Invalid number of arguments.\nUse: python rs.py rsListenPort")
		return

	# get port
	rsListenPort = sys.argv[1]

	fileName = "PROJI-DNSRS.txt"
	# setup root server
	rs = NameServer(fileName, rsListenPort)

	# parse file
	rs.parse()

	# rs.printRecords()
	# rs.printNS()

	# setup listening thread
	listen = threading.Thread(target=rs.serverThread)
	listen.start()

	# wait for new connections
	rs.waitForConnections()

	# defer
	atexit.register(gracefulExit, rs, listen)

if __name__ == "__main__":
	main()
