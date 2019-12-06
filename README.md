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

## RAFT implementation

Reference paper:
[chrome-extension://ihgdgpjankaehldoaimdlekdidkjfghe/viewer.html#https://raft.github.io/raft.pdf]

[A great visulization of the algorithm can might be helpful](http://thesecretlivesofdata.com/raft/)

### Leader election

For election to work, the RequestVote() RPC handler is implemented so that servers will vote for one another.

To implement heartbeats, the AppendEntries RPC handler is implemented, and have the leader send them out periodically. An AppendEntries RPC handler method that resets the election timeout is also writen so that other servers don’t step forward as leaders when one has already been elected.

The timers in different Raft peers are not synchronized. In particular, the election timeouts don’t always fire at the same time, otherwise all peers will vote for themselves and no one will become leader.

Implementation of leader election and heartbeats (empty AppendEntries calls) enables a single leader to be elected and–in the absence of failures–stay the leader, as well as redetermine leadership after failures.

### Log replication

Once a leader is elected, the leader sends AppendEntries calls to followers to update their file logs.

When a client sends a update file request to the leader, the leader first append the entry to its own log and send the message to followers with AppendEntries calls (heartbeat). When a follower receives the message, it will append the new entry 
to its log as well. If the leader got reponse from the majority of the followers, it repond to the client that the update file request is successful, otherwise the client will be blocked until the majority of the followers respond to the leader.
And after the leader respond to the client that the update file request is successful, it would commit the change to its file info map (the log entry is commited). In the next heartbeat, the followers will receive the message that the leader already commit the change, so they will also commit the change to their own file info maps.


## API summary

| RPC call        | Description           | Who calls this?  |  Response during “crashed” state |
| ------------- |:-------------:| -----:|:----:|
| AppendEntries     | Replicates log entries; serves as a heartbeat mechanism| server | Should return an “isCrashed” error; procedure has no effect if server is crashed|
| RequestVote     | Used to implement leader election     |   server |Should return an “isCrashed” error; procedure has no effect if server is crashed|
| getfileinfomap() | Returns metadata from the filesystem     |    client | If the node is the leader, and if a majority of the nodes are working, should return the correct answer; if a majority of the nodes are crashed, should block until a majority recover.  If not the leader, should indicate an error back to the client |
| updatefile() | Updates a file’s metadata | client | If the node is the leader, and if a majority of the nodes are working, should return the correct answer; if a majority of the nodes are crashed, should block until a majority |
| tester_getversion() | Returns the version of the given file, even when the server is crashed | client | Returns the version of the given file in the server’s metadata map, even if the server is in a crashed state |
| isleader() | True if the server thinks it is a leader | client | Always returns the correct answer |
| crash() | Cause the server to enter a “crashed” state | tester | Crashing a server , if that is already crashed has no effect |
| restore() | Causes the server to no longer be crashed | tester | Causes the server to recover and no longer be crashed |
| iscrashed() | True if the server is in a crashed state | tester | Always returns the correct answer |


