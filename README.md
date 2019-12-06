# Distributed-fault-tolerant-file-storage-system
A distributed file storage system, implemented the Raft Consensus Algorithm to ensure fault tolerant and version control

## How to start servers
The server should take in the name of a configuration file, and then the ID number of that server.  For example:

$ run-server.sh myconfig.txt 3

Would start the server with a configuration file of myconfig.txt.  It would tell the newly started server that it is server #3 in the set of processes.

## Configuration file
The server will receive a configuration file as part of its initialization.  The format is as follows:

M: number of servers

metadata0: <host>:<port>
  
metadata1: <host>:<port>
  
metadata2: <host>:<port>

As an example:

M: 5

metadata0: localhost:9001

metadata1: localhost:9002

metadata2: localhost:9003

metadata3: localhost:9004

metadata4: localhost:9005

## How to run tests
The tester.py under the src directory is used to test the file system by sending requests to the servers as a client.
To run the test, simple using command like:

$ run-tester.sh localhost:9001

where the argument is the server hostport

## API summary

| RPC call        | Description           | Who calls this?  |  Response during “crashed” state |
| ------------- |:-------------:| -----:|:----:|
| AppendEntries     | Replicates log entries; serves as a heartbeat mechanism| server | Should return an “isCrashed” error; procedure has no effect if server is crashed|
| RequestVote     | Used to implement leader election     |   server |Should return an “isCrashed” error; procedure has no effect if server is crashed|
| getfileinfomap() | Returns metadata from the filesystem     |    client | If the node is the leader, and if a majority of the nodes are working, should return the correct answer; if a majority of the nodes are crashed, should block until a majority recover.  If not the leader, should indicate an error back to the client |


