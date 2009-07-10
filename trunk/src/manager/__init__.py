import pygame
import SocketServer
from threading import *
import socket
import copy
import traceback
import pickle
import struct
import sys
import random

from Numeric import array, zeros
import math

class Event:
	"""
	Base class of events.
	"""
	
	INDEFINITE = -1.0
	
	__slots__ = ['dest', 'source_connection', 'game_lifetime', 'system_lifetime', 'alive', 'local']
	
	def __init__( self, dest, stime, etime ):
		"""
		Constructor.
		@param dest The destination object for this event.
		"""
		self.dest = dest
		self.source_connection = None
		self.game_lifetime = (stime, etime)
		self.system_lifetime = [stime, etime]
		self.alive = True
		self.local = False
		
	def set_is_local( self, local ):
		self.local = local
		
	def is_local( self ):
		return self.local
		
	def serialize( self ):
		spec_data = {
			'event_id' : Event_Manager.event_manager.get_id( self ),
			'event_lifetime' : self.game_lifetime,
			'event_class' : self.__class__.__name__,
			'dest_id' : Event_Manager.event_manager.get_id( self.dest )}
		
		for k in self.__slots__:
			if k not in Event.__slots__:
				spec_data[k] = self.__dict__[k]
				
		return pickle.dumps( spec_data )

	def __repr__( self ):
		return '%s' % (self.__class__.__name__)
			
	@staticmethod
	def deserialize( msg ):
		try:
			msg = pickle.loads( msg )
			dest = Event_Manager.event_manager.get_object( msg['dest_id'] )
			lifetime = msg['event_lifetime']
			klass = Event_Manager.event_manager.get_event_class( msg['event_class'] )
			try:
				e = klass( dest, *lifetime, **msg )
			except:
				e = klass( dest, lifetime[0], **msg )
			Event_Manager.event_manager.set_object_id( e, msg['event_id'] )
			return e
		except:
			traceback.print_exc( )
			
class End_Event (Event):
	__slots__ = ['end_id']

	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )
		self.forced = True
		self.end_id = kwargs['end_id']

	def get_event( self ):
		return Event_Manager.event_manager.get_object( self.end_id )

	def __repr__( self ):
		return '%s( %s )' % (self.__class__.__name__, self.end_id)

class Not_Executable_Exception (Exception):
	def __init__( self, event, msg ):
		self.event = event
		self.msg = msg
		
	def __str__( self ):
		return self.msg

class Event_Manager:
	EXECUTE_TIMER = pygame.USEREVENT + 1
	event_manager = None
	
	def __init__( self, game ):
		self.game = game
		self.objects = {}
		self.ids = {}
		Event_Manager.event_manager = self
		self.set_object_id( game, 0 )
		self.next_id = 0
		self.id_str = "".join( [chr( random.randint( 97, 122 ) ) for i in range( 3 )] )
		
	def get_id( self, object ):
		return self.objects[object]

	def get_object( self, id ):
		return self.ids[id]
		
	def set_object_id( self, object, id ):
		self.objects[object] = str( id )
		self.ids[str( id )] = object
		print 'Event_Manager.set_object_id( %s, %s )' % (object, id)

	def new_id( self ):
		self.next_id += 1
		return self.id_str + str( self.next_id )

class Local_Event_Manager (Event_Manager):
	def __init__( self, game ):
		Event_Manager.__init__( self, game )
		
		self.start_time = pygame.time.get_ticks( )
		self.event_queue = []
		pygame.time.set_timer( pygame.USEREVENT+1, 100 )
		self.lock = Lock( )
		
	def queue_event( self, event ):
		self.event_queue.append( event )
#		pygame.time.set_timer( pygame.USEREVENT+1, int( event.system_lifetime[0]+1 ) )
#		if event.system_lifetime[1] >= 0:
#			pygame.time.set_timer( pygame.USEREVENT+1, int( event.system_lifetime[1]+1 ) )

		if event.system_lifetime[0] >= 0:
			event.system_lifetime[0] += self.get_time( )
		if event.system_lifetime[1] >= 0:
			event.system_lifetime[1] += self.get_time( )
		
	def get_time( self ):
		return (pygame.time.get_ticks( ) - self.start_time) / 1000.0
	
	def handle_pygame_event( self, event ):
		tick = self.get_time( )
		
		for e in self.event_queue:
			#print e.__class__.__name__, e.system_lifetime, tick
			if e.system_lifetime[0] >= 0 and e.system_lifetime[0] <= tick:
				try:
					e.system_lifetime[0] = Event.INDEFINITE
					
					### Handle special events. ###
					
					e.dest.execute_event( e, self.get_time( ) )
					
					if isinstance( e, End_Event ):
						ev = e.get_event( )
						del self.objects[ev]
						del self.ids[e.end_id]
						self.event_queue.remove( ev )

						oid = self.get_id( e )
						del self.objects[e]
						del self.ids[oid]
						self.event_queue.remove( e )

				except Not_Executable_Exception, ex:
					print "Failed executing event:", ex
			
			elif e.system_lifetime[1] >= 0 and e.system_lifetime[1] <= tick:
				ee = End_Event( e.dest, 0, end_id = self.get_id( e ) )
				e.dest.execute_event( ee, self.get_time( ) )
					
				oid = self.get_id( e )
				del self.objects[e]
				del self.ids[oid]
				self.event_queue.remove( e )

class Network_Request_Handler_Factory:
	@staticmethod
	def get_handler_class( event_manager ):
		klass = copy.deepcopy( Network_Request_Handler )
		klass.event_manager = event_manager
		return klass

class Network_Request_Handler (SocketServer.BaseRequestHandler):
	event_manager = None

	def setup( self ):
		print self.client_address, 'connected.'
		
	def handle( self ):
		event_manager = Event_Manager.event_manager
		data = ' '
		pkt_data = ''
		
		username, pw = event_manager.server.recv_packet( self.request ).split( " " )
		
		if pw != Event_Manager.event_manager.password:
			Network_Server.send_packet( self.request, "0" )
			return
		else:
			Network_Server.send_packet( self.request, '1' )
			
		event_manager.usernames[self.request] = username

		event_manager.server.connections.append( self.request )
		
		### Send Object_Create_Event to the new client for all objects. ###
		
		for o in event_manager.objects.keys( ):
			if isinstance( o, Object ):
				e = o.get_create_event( )
				event_manager.set_object_id( e, event_manager.new_id( ) )
				print "%s %s" % (event_manager.get_id( o ), e.oid )
				print 'Server.connect_send( %s )' % e
				event_manager.server.send_event( e, self.request )
		
		### Request handling loop. ###

		while True:
			event_manager.server.recv_event( self.request )
			
	def finish( self ):
		Network_Request_Handler.event_manager.server.connections.remove( self.request )
		print self.client_address, 'disconnected.'
		Network_Request_Handler.event_manager.server.close_request( self.request )
		
		
class Network_Server (Thread):
	def __init__( self, host, port, manager, **kwargs ):
		Thread.__init__( self )
		self.connections = []
		self.host = host
		self.port = port
		self.event_manager = manager
		self.server = None
		self.recv_data = ''
		
		self.upstream = None
		if kwargs.has_key( 'upstream' ):
			self.upstream = kwargs['upstream']
			
			self.send_packet( self.upstream, "%s %s" % (Event_Manager.event_manager.username,
				Event_Manager.event_manager.password) )
			
			response = self.recv_packet( self.upstream )
			if response == '1':
				print "Authentication succeeded."
			else:
				raise ValueError, "Authentication failed (%s)." % response

			self.connections.append( self.upstream )

	def get_connections( self ):
		return self.connections
		
	def run( self ):
		if self.upstream == None:
			self.server = SocketServer.ThreadingTCPServer( (self.host, self.port),
				Network_Request_Handler_Factory.get_handler_class( self.event_manager ) )
			print 'Server running on port %d.' % self.port
			self.server.serve_forever( )
			
		else:
			while True:
				self.recv_event( self.upstream )

	def shutdown( self ):
		if self.upstream != None:
			print 'Closing connection to server.'
			self.upstream.close( )
		else:
			self.server.server_close( )
		
	def send_event( self, event, connection ):
		data = event.serialize( )
		self.send_packet( connection, data )

	@staticmethod
	def send_packet( connection, data ):
		connection.sendall( struct.pack( '>i', len( data ) ) + data )
		print "Sent %d bytes" % len( struct.pack( '>i', len( data ) ) + data )
		
	def recv_packet( self, connection ):
		size_data = event_data = self.recv_data

		while len( size_data ) < 4:
			size_data = connection.recv( 1024 )
			
		size = struct.unpack( '>i', size_data[:4] )[0]				
		event_data = size_data[4:]
	
		while len( event_data ) < size:
			event_data += connection.recv( 1024 )
			
		return_data = event_data[:size]
		self.recv_data = event_data[size:]
		return return_data

	def recv_event( self, connection ):
		data = self.recv_packet( connection )

		e = Event.deserialize( data )
		e.source_connection = connection
		print "Network_Server.recv( %s, %s )" % (e, connection)
		Event_Manager.event_manager.queue_event( e )

class Naive_Network_Event_Manager (Local_Event_Manager):
	"""
	Event manager running over a network that believes everything it hears
	and does not attempt to synchronize the game state at all.
	@param host Network host.
	@param port Network port.
	@param game Game we're in.
	@param event_classes Acceptable event classes.
	"""
	def __init__( self, host, port, game, username, password, event_classes ):
		"""
		Constructor.
		"""
		Local_Event_Manager.__init__( self, game )
		self.game = game
		self.event_classes = {}
		self.usernames = {None : username}
		self.username = username
		self.password = password
		for ec in event_classes:
			self.event_classes[ec.__name__] = ec

		game.event_manager = self

		try:
			#self.server = Network_Server( host, port, self )
			s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
			s.connect( (host, port) )
			self.server = Network_Server( host, port, self, 
				upstream = s )
		
		except ValueError, ex:
			raise ex
		
		except:
			self.server = Network_Server( host, port, self )

		self.server.start( )
		
	def queue_event( self, event ):
		"""
		Queue an event for processing.
		@param event The @ref Event to queue.
		"""
		self.lock.acquire( )
		Local_Event_Manager.queue_event( self, event )
		if not self.objects.has_key( event ):
			self.set_object_id( event, self.new_id( ) )

		if not event.is_local( ):
			for c in self.server.get_connections( ):
				if c != event.source_connection:
					print "Network_Event_Manager.send( %s )" % event
					self.server.send_event( event, c )
		self.lock.release( )

	def get_event_class( self, class_name ):
		return self.event_classes[class_name]
		
	def shutdown( self ):
		print 'Event manager shutting down.'
		self.server.shutdown( )

	def get_connection_name( self, conn ):
		return self.usernames[conn]