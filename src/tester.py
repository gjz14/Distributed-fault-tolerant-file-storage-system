import argparse
import xmlrpc.client

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="SurfStore client")
	parser.add_argument('hostport', help='host:port of the server')
	args = parser.parse_args()

	hostport = args.hostport

	try:
		client  = xmlrpc.client.ServerProxy('http://' + hostport)
		# Test ping
		client.surfstore.ping()
		print("Ping() successful")
		client.surfstore.isLeader()
		# client.surfstore.isCrashed()
		#client.surfstore.crash()
		client.surfstore.restore()
		# client.surfstore.getfileinfomap()
		#client.surfstore.updatefile("Test.txt", 6, [5,2,3])
		# client.surfstore.tester_getversion("Test.txt")

	except Exception as e:
		print("Client: " + str(e))
