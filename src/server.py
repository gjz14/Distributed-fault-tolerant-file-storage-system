from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from socketserver import ThreadingMixIn
from hashlib import sha256
import argparse
import threading
import time
import random
import xmlrpc.client
import copy


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class threadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class TimeHandler():
    def __init__(self):
        self.election_lower = 1500
        self.election_higher = 3000
        self.start = int(time.time() * 1000)
        self.timeout = 0

    def timecount(self):
        return int(time.time() * 1000 - self.start)

    def reset(self):
        self.start = int(time.time() * 1000)

    def set_election_timeout(self):
        self.timeout = random.randint(self.election_lower, self.election_higher)

    def set_heartbeat_timeout(self, interval):
        self.timeout = interval


# A simple ping, returns true
def ping():
    """A simple ping method"""
    print("Ping()")
    return True


# Gets a block, given a specific hash value
def getblock(h):
    """Gets a block"""
    print("GetBlock(" + h + ")")

    blockData = bytes(4)
    return blockData


# Puts a block
def putblock(b):
    """Puts a block"""
    print("PutBlock()")

    return True


# Given a list of hashes, return the subset that are on this server
def hasblocks(hashlist):
    """Determines which blocks are on this server"""
    print("HasBlocks()")

    return hashlist


# Retrieves the server's FileInfoMap
def getfileinfomap():
    global majority_live
    """Gets the fileinfo map"""
    start_time = time.time()
    if not isLeader():
        raise Exception("Not the leader")
    else:
        # block if the leader is crashed
        while isCrashed():
            if time.time() - start_time > 2.5:
                return True
            pass
        print("GetFileInfoMap()")
        log.append([current_term, [1]])

        # block until the majority of nodes alive alive
        while majority_live < (1 + num_servers) / 2:
            if time.time() - start_time > 2.5:
                return True
            pass
        print("successful get rid of block!!!")
        return fileinfomap


# Update a file's fileinfo entry
def updatefile(filename, version, hashlist):
    global current_term
    global majority_live
    """Updates a file's fileinfo entry"""
    start_time = time.time()
    if not isLeader():
        raise Exception("Not the leader")
    else:
        # block if the leader is crashed
        while isCrashed():
            if time.time() - start_time > 2.5:
                return True
            continue
        print("UpdateFile(" + filename + ")")

        log.append([current_term, [2, filename, version, hashlist]])

        # block until the majority of nodes alive
        while majority_live < (1 + num_servers) / 2:
            if time.time() - start_time > 2.5:
                return True
            continue
        print("Leader reply to client success")
        return True


def updatefile_allserver(filename, version, hashlist):
    """Updates a file's fileinfo entry"""

    fileinfomap[filename] = [version, hashlist]
    return True


# PROJECT 3 APIs below

# Queries whether this metadata store is a leader
# Note that this call should work even when the server is "crashed"
def isLeader():
    """Is this metadata store a leader?"""
    print("status: ", status)
    if status == 2:
        return True
    else:
        return False


# "Crashes" this metadata store
# Until Restore() is called, the server should reply to all RPCs
# with an error (unless indicated otherwise), and shouldn't send
# RPCs to other servers
def crash():
    """Crashes this metadata store"""
    global is_crashed
    global vote_counter
    global status
    is_crashed = True
    status = 0          # When crash, force leader to be follower
    vote_counter = 0
    print("Crash()")
    return True


# "Restores" this metadata store, allowing it to start responding
# to and sending RPCs to other nodes
def restore():
    """Restores this metadata store"""
    global is_crashed
    is_crashed = False
    print("Restore()")
    return True


# "IsCrashed" returns the status of this metadata node (crashed or not)
# This method should always work, even when the node is crashed
def isCrashed():
    """Returns whether this node is crashed or not"""
    print("IsCrashed()")
    return is_crashed


# Requests vote from this server to become the leader
def requestVote(my_id, serverid, term):
    """Requests vote to be the leader"""
    if is_crashed:
        raise Exception("Crash Error")
    global vote_counter
    global current_term
    global status
    global log
    try:
        c = xmlrpc.client.ServerProxy("http://" + serverid)
        response, external_term = c.surfstore.answerVote(my_id, term, len(log) - 1)
        if response:
            vote_counter += 1
        # downgrade a candidate node to a follower node
        elif external_term > current_term:
            current_term = external_term
            status = 0
            vote_counter = 0
    except:
        pass

    return True


def answerVote(candidate_id, candidate_term, last_log_index):
    if is_crashed:
        return False, -1
    global current_term
    global timer
    global status
    global voted_for
    global vote_counter 
    global log
    try:
        if current_term > candidate_term:
            return False, current_term
        if current_term < candidate_term:
            status = 0
            vote_counter = 0
            current_term = candidate_term
            voted_for = "Nobody"
        if voted_for == "Nobody" and last_log_index >= len(log) - 1:
            voted_for = candidate_id
            # reset the election timeout
            timer.reset()
            timer.set_election_timeout()
            return True, current_term
        else:
            print("I won't vote")
            return False, current_term
    except:
        pass

    


def appendEntries(serverid, term, fileinfomap, i):
    """Updates fileinfomap to match that of the leader"""
    if is_crashed:
        raise Exception("Crash Error")
    global status
    global current_term
    global match_index
    global next_index
    global commit_index
    global vote_counter
    global majority_live
    entries = log[next_index[i]:]
    prev_log_index = next_index[i] - 1          
    prev_log_term = log[prev_log_index][0]
    try:
        response, external_term = xmlrpc.client.ServerProxy("http://" + serverid).surfstore.\
            answerAppendEntries(term,
                                fileinfomap,
                                prev_log_index,
                                prev_log_term,
                                entries,
                                commit_index)
        if external_term == -1:   # follower is crashed
            return False
        if response and len(entries) != 0:
            print( "update nextIndex and matchIndex for the follower "+str(i))
            match_index[i] = len(log) - 1
            next_index[i] = len(log)



        if not response:
            # downgrade a leader node to a follower node
            if current_term < external_term:
                print("I am not leader now!!!!")
                current_term = external_term
                vote_counter = 0
                status = 0
            else:
                next_index[i] -= 1
        # print("Leader log: ", log)
    except:
        pass
    majority_live += 1
    return True


def answerAppendEntries(leader_term, leader_fileinfomap, prev_log_index, prev_log_term, entries, leader_commit):
    # When crashed, use term == -1 to label that server is crashed
    if is_crashed:
        return False, -1

    global commit_index
    global log
    global timer
    global status
    global vote_counter
    global current_term

    if current_term > leader_term:
        return False, current_term

    if log[prev_log_index][0] != prev_log_term:
        return False, current_term

    if len(entries) != 0:
        print("ready to update log as a follower "+str(entries))
        has_conflict = False
        for i in range(len(entries)):
            if prev_log_index + 1 + i < len(log):
                if log[prev_log_index + 1 + i][0] != entries[i][0]:
                    has_conflict = True
                    log[prev_log_index + 1 + i:] = list()
                    for j in range(i, len(entries)):
                        log.append(entries[j])
                    break

        if not has_conflict:
            print("no conflict")
            log[prev_log_index + 1:] = list()
            log.extend(entries)

    if leader_commit > commit_index:
        commit_index = min(leader_commit, len(log) - 1)
        print("Follower update commit index to " + str(commit_index))
    timer.reset()
    timer.set_election_timeout()
    status = 0
    vote_counter = 0
    current_term = leader_term
    return True, current_term


def tester_getversion(filename):
    if filename not in fileinfomap:
        return 0
    return fileinfomap[filename][0]


def get_commit_index():
    global commit_index
    return commit_index


def reset_next_and_match_index(n, log):
    global match_index
    global next_index
    match_index = [0 for _ in range(n)]
    print(match_index)
    next_index = [len(log) for _ in range(n)]

    print(next_index)


# Reads the config file and return host, port and store list of other servers
def readconfig(config, servernum):
    """Reads cofig file"""
    fd = open(config, 'r')
    l = fd.readline()

    maxnum = int(l.strip().split(' ')[1])

    if servernum >= maxnum or servernum < 0:
        raise Exception('Server number out of range.')

    d = fd.read()
    d = d.splitlines()

    for i in range(len(d)):
        hostport = d[i].strip().split(' ')[1]
        if i == servernum:
            host = hostport.split(':')[0]
            port = int(hostport.split(':')[1])

        else:
            serverlist.append(hostport)

    return maxnum, host, port


def raft():
    global status
    global majority_live
    global commit_index
    global current_term
    global vote_counter
    global voted_for
    global timer
    global last_applied
    global log
    global is_crashed
    timer = TimeHandler()
    timer.set_election_timeout()
    while True:
        while is_crashed:
            timer.reset()
            timer.set_election_timeout()
        # COMMIT UNAPPLIED LOGS
        if commit_index > last_applied:
            last_applied += 1
            filename = log[last_applied][1][1]
            version = log[last_applied][1][2]
            hashlist = log[last_applied][1][3]
            updatefile_allserver(filename, version, hashlist)
            print("Commit file: ",filename, version)
        # if it is a leader, just send heartbeats
        if status == 2:
            timer.set_heartbeat_timeout(250)

            if timer.timecount() > timer.timeout:
                timer.reset()
                thread_list = []
                majority_live = 0
                for i, s in enumerate(serverlist):
                    thread_list.append(threading.Thread(target=appendEntries, args=(s, current_term, fileinfomap, i)))
                    thread_list[-1].start()
                for t in thread_list:
                    t.join()
                # Control commit_index
                N = commit_index + 1
                while N < len(log):
                    flag = 0
                    for index in match_index:
                        if index >= N:
                            flag += 1
                    if flag >= len(match_index) / 2 and log[N][0] == current_term:
                        commit_index = N
                        print("Leader update commit index to " + str(commit_index))
                        break
                    N += 1
                
        else:
            # election time out
            if timer.timecount() > timer.timeout:
                timer.reset()
                timer.set_election_timeout()
                
                # MAKE IT AN CANDIDATE 
                status = 1  
                current_term += 1
                # vote for itself
                vote_counter = 1  
                voted_for = my_id


                # print("I am " + str(host) + ":" + str(port) + ",  I am requesting for vote, my current term is: " + str(
                #     current_term))
                thread_list = []
                for s in serverlist:
                    thread_list.append(threading.Thread(target=requestVote, args=(my_id, s, current_term)))
                    thread_list[-1].start()
                for t in thread_list:
                    t.join()

                # get majority votes, become leader
                # print(num_servers, vote_counter)
                if vote_counter > num_servers / 2:
                    status = 2  # make it a leader
                    print("A new leader " + str(host) + ":" + str(port) + " in term: " + str(current_term))
                    #
                    n = len(serverlist)
                    reset_next_and_match_index(n, log)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="SurfStore server")
        parser.add_argument('config', help='path to config file')
        parser.add_argument('servernum', type=int, help='server number')

        args = parser.parse_args()

        config = args.config
        servernum = args.servernum

        # server list has list of other servers
        serverlist = []

        # maxnum is maximum number of servers
        maxnum, host, port = readconfig(config, servernum)

        # My id
        my_id = host + ":" + str(port)

        hashmap = dict()

        fileinfomap = dict()

        voted_for = "Nobody"
        log = list()
        log.append([1, []])
        last_applied = 0
        commit_index = 0
        # value of log[i][2][0]: read: 1, write: 2

        # For leader
        next_index = list()
        match_index = list()

        print("Attempting to start XML-RPC Server...")
        print(host, port)
        server = threadedXMLRPCServer((host, port), requestHandler=RequestHandler)
        # Init variables
        num_servers = len(serverlist) + 1
        status = 0  # 0: follwer, 1: candidate, 2: leader
        is_crashed = False

        current_term = 0

        server.register_introspection_functions()
        server.register_function(ping, "surfstore.ping")
        server.register_function(getblock, "surfstore.getblock")
        server.register_function(putblock, "surfstore.putblock")
        server.register_function(hasblocks, "surfstore.hasblocks")
        server.register_function(getfileinfomap, "surfstore.getfileinfomap")
        server.register_function(updatefile, "surfstore.updatefile")
        # Project 3 APIs
        server.register_function(isLeader, "surfstore.isLeader")
        server.register_function(crash, "surfstore.crash")
        server.register_function(restore, "surfstore.restore")
        server.register_function(isCrashed, "surfstore.isCrashed")
        server.register_function(requestVote, "surfstore.requestVote")
        server.register_function(appendEntries, "surfstore.appendEntries")
        server.register_function(tester_getversion, "surfstore.tester_getversion")

        server.register_function(updatefile_allserver, "surfstore.updatefile_allserver")
        server.register_function(reset_next_and_match_index, "surfstore.reset_next_and_match_index")
        server.register_function(get_commit_index, "surfstore.get_commit_index")
        server.register_function(answerVote, "surfstore.answerVote")
        server.register_function(answerAppendEntries, "surfstore.answerAppendEntries")
        print("Started successfully.")
        print("Accepting requests. (Halt program to stop.)")

        t = threading.Thread(target=raft, )
        t.start()

        server.serve_forever()
    except Exception as e:
        print("Server: " + str(e))
