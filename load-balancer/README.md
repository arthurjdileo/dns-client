# Client functionality
	- The client sends a batch request to the LS server containing a list of domains to be looked up.
	- The LS server keeps note of the request by saving the domains that need to have a response.
	- The LS server will then send a request to each of the TS servers (as per the requirements).
	- Each response is funneled through a Queue channel on separate threads and then processed by the LS server.
	- We wait 3 seconds to ensure all responses from LS server are received.
	- Once all responses are received, we check those responses against the master list that the LS server notes in number 2.
	- If we do not have a valid response for any of the domains, we assume that the TS server has no data for that specific domain.
# Problems I faced developing
	- the biggest problem i faced was how to differeniate between a successful response and a domain that has no data attached to it. In the event,
	that there is no data, we do not send a response. This leaves the heavy-lifting up to the LS server on how it should handle it.
	- Another issue i had was i was unable to figure out when a client is done requesting. In our first project, we sent one off requests individually, whereas in this project, we sent batch requests to ensure that once a request is received by LS, that we need to generate a response to that single client. We also needed to account for sending requests to different clients and ensuring we can differeniate between requests from the TS server.
# What I learned in this project
	- I learned how to manage data ingestion between multiple sockets into a single processing function.

# Project Deep-Dive (Q & A w/ Prof)
"Why is it that we are not returning a response for any of the TS servers when we have no available data? How is this, by any means, practical? Say, one of the TS servers were to go down after we initiate a connection. How is the LS able to differeniate between the server being down/an error processing the request vs. a request that the TS server has no data for since we're only sending responses for successful requests? I feel like this project is teaching a crucial foundational concept in the wrong way. In my opinion, I believe a server should return a response regardless, especially if there is an error, so that the client can re-send the request in the event of a 500 error on the server side. In this case, it's impossible for the client to differeniate between an error on the server side vs. there being no data available for the TS server to send.

I would like to hear your thoughts/justification on this and if I can be corrected. I'm always looking to truly understand what would be practical in a production environment."

"The learning objective of the project is to get you to use sockets in a way that your application code chooses the first arriving response from sending out two requests. In large distributed applications, it's a common paradigm to send requests to multiple backends and choose the response that returns first. i.e., the application uses the "best of two choices". For example, see this famous paper from Google, "the tail at scale" https://dl.acm.org/doi/10.1145/2408776.2408794

That said, the implementation of the learning objective can be imperfect. The way we're modelling "slow" backends is somewhat reductive -- one of the servers doesn't respond at all. Further, there are alternative methods, rather than best-of-two-choices, that are acceptable to be graded successfully in this project -- like sending to one server first, timing out, then sending to the next server.

These choices have been made so that students can still (mostly) get to the learning objective without unduly complicating either the implementation of the project (for students) or the grading process (for TAs)."
