# Iterative client functionality
	- Client sends list of hostnames to be resolved to root server.
		- The hostnames are parsed on the client side and then sent via sockets.
	- Root server receives and either responds with the resolved entry or a new name server to request the data from.
		- The client distinguishes between requests by looking for a '*' char. If it's present, that means we need to request from Top server.
	- Client gathers data and exports it to RESOLVED.txt in the order it was requested.
	- All programs are following an object-oriented design with plenty of comments.
	- Both servers continually listen for new connections and new data.
		- Servers listen via threads to ensure concurrency.
		- Threads communicate with server via queue.
	- Servers can handle multiple requests and multiple clients at a time.
	- Requests are stored in a queue for better memory management.
# Problems I faced developing
	- Sending data from different threads back to the main thread.
	- Finding a way to distinguish between a resolved result and a redirection.
	- A set blocking attribute for the queue and sockets to ensure the while loops are continually running infinetly if we don't have any data.
	- I use a queue to ensure requests are handled in an orderly fashion. It also mimicks how DNS servers process requests.
# What I learned in this project
	- Learned how to use threads
	- Learned how to capture and send data via threads
	- Learned how to properly apply networking principles taught in lecture.
	- Understood the use and reasoning behind a queue data structure.
	- Understood the importance of generalizing functions (in the case of clientThread and listen functions) and utilizing helper functions.
