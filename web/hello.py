import cherrypy

class HelloWorld:
	def index(self):
		return "Hello world!"
	index.exposed = True

cherrypy.root = HelloWorld()

if __name__ == '__main__':
	# Use the configuration file tutorial.conf.
	cherrypy.config.update({'server.socket_host': '0.0.0.0',
							'server.socket_port': 8081
							})
	# Start the CherryPy server.
	cherrypy.server.start()
