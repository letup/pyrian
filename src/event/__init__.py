import pygame
import SocketServer
from threading import *
import socket
import copy
import traceback
import pickle
import struct
import sys

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
			e = klass( dest, *lifetime, **msg )
			Event_Manager.event_manager.set_object_id( e, msg['event_id'] )
			return e
		except:
			traceback.print_exc( )
			
class End_Event (Event):
	__slots__ = ['event_id']

	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )
		self.forced = True
		
		if kwargs.has_key( 'forced' ):
			self.forced = kwargs['forced']
			
		self.event_id = Event_Manager.event_manager.get_id( kwargs['event'] )

	def get_event( self ):
		return Event_Manager.event_manager.get_object( self.event_id )

	def __repr__( self ):
		return '%s( %s )' % (self.__class__.__name__, self.event_id)

class Message_Event (Event):
	"""
	Text message send event.
	"""
	__slots__ = ['msg', 'name']
	
	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )
		self.name = kwargs['name']
		self.msg = kwargs['msg']
		
class Object_Create_Event (Event):
	"""
	Event corresponding to a shared object creation.
	"""

	__slots__ = ['klass', 'oid', 'args', 'kwargs']
	
	def __init__( self, dest, dtime, **kwargs ):
		"""
		Constructor.
		@param kwargs Required keywords are:
			- klass : Class to instantiate.
			- args : Arguments to class constructor.
			- oid : Event_Manager ID to assign to the created object.
			- kwargs : Arguments to class constructor.
		"""
		Event.__init__( self, dest, dtime, dtime )
		self.klass = kwargs['klass']
		self.args = kwargs['args']
		self.oid = kwargs['oid']
		self.kwargs = kwargs['kwargs']

class Newtonian_Force_Event (Event):
	"""
	Abstract base class of Newtonian force events.
	"""

	def get_linear_force( self, time ):
		"""
		Get the force vector induced by this event.
		@return The force vector.
		"""
		return array( [0.0, 0.0], 'f' )

	def get_rotational_force( self, time ):
		"""
		Get the constant force vector induced by this event.
		@return The force vector.
		"""
		return 0
		
	def get_damping_coefficient( self, time ):
		return 0

	def get_rotational_damping_coefficient( self, time ):
		return 0
	
class Linear_Force_Event (Newtonian_Force_Event):
	"""
	Class corresponding to a constant linear Netwonian force.
	"""

	__slots__ = ['vec']
	
	def __init__( self, dest, stime, etime, **kwargs ):
		"""
		Basic constructor.
		@param dest The destination object.
		@param kwargs Required keys are:
			- vec : A 2D @ref Numeric.array with the force vector.
		"""
		Newtonian_Force_Event.__init__( self, dest, stime, etime )
		self.vec = kwargs['vec']
		
	def get_linear_force( self, time ):
		"""
		Get the constant force vector induced by this event.
		@return The force vector.
		"""
		return self.vec

class Rotational_Force_Event (Newtonian_Force_Event):
	"""
	Class corresponding to a constant rotational Netwonian force.
	"""

	__slots__ = ['ra']
	
	def __init__( self, dest, stime, etime, **kwargs ):
		"""
		Basic constructor.
		@param dest The destination object.
		@param kwargs Required keys are:
			- ra : The magnitude of the rotational force.
		"""
		Newtonian_Force_Event.__init__( self, dest, stime, etime )
		self.ra = kwargs['ra']
		
	def get_rotational_force( self, time ):
		"""
		Get the constant force vector induced by this event.
		@return The force vector.
		"""
		return self.ra

class Oriented_Force_Event (Newtonian_Force_Event):
	"""
	Class corresponding to a Netwonian force relative to the direction of the 
	object's orientation.
	"""

	__slots__ = ['m', 'ro']
	
	def __init__( self, dest, stime, etime, **kwargs ):
		"""
		Basic constructor.
		@param kwargs Required keys are:
			- m : Magnitude of the force.
			- ro : Offset from the orientation in radians.
		"""
		Newtonian_Force_Event.__init__( self, dest, stime, etime )
		self.m = float( kwargs['m'] )
		self.ro = kwargs['ro']
		
	def get_linear_force( self, time ):
		"""
		Get the force vector induced by this event.
		@return The force vector.
		"""
		v = self.dest.get_orientation( time )
		v = array( [float( math.cos( v + self.ro )*self.m ), 
			float( math.sin( v + self.ro )*self.m )], 'f' )
		return v

class Damping_Force_Event (Newtonian_Force_Event):
	__slots__ = ['c']
	
	def __init__( self, dest, stime, etime, **kwargs ):
		"""
		Basic constructor.
		@param kwargs Required keys are:
			- c : Damping coefficient.
		"""
		Newtonian_Force_Event.__init__( self, dest, stime, etime )
		self.c = kwargs['c']
		
	def get_damping_coefficient( self, time ):
		return self.c

class Rotational_Damping_Force_Event (Newtonian_Force_Event):
	__slots__ = ['c']
	
	def __init__( self, dest, stime, etime, **kwargs ):
		"""
		Basic constructor.
		@param kwargs Required keys are:
			- c : Damping coefficient.
		"""
		Newtonian_Force_Event.__init__( self, dest, stime, etime )
		self.c = kwargs['c']
		
	def get_rotational_damping_coefficient( self, time ):
		return self.c

class Object:
	__slots__ = ['p','v','rp','rv']
	
	def __init__( self, **kwargs ):
		"""
		Basic constructor for Newtonian physics objects.
		@param kwargs Acceptable values are:
		@li p - Set the position to a 2D @ref Numeric.array.
		@li v - Set the position to a 2D @ref Numeric.array.
		@li rp - Set the rotational orientation.
		@li rv - Set the rotational velocity.
		"""
		
		if kwargs.has_key( 'p' ): self.p = kwargs['p']
		else: self.p = zeros( (2,), 'float' )
		if kwargs.has_key( 'v' ): self.p = kwargs['v']
		else: self.v = zeros( (2,), 'float' )
		if kwargs.has_key( 'rp' ): self.p = kwargs['rp']
		else: self.rp = 0
		if kwargs.has_key( 'rv' ): self.p = kwargs['rv']
		else: self.rv = 0
	
		self.forces = []
		self.commit_time = 0
	
	def execute_event( self, e, time ):
		"""
		Execute a simulation event.
		@param e The event.
		"""
		if isinstance( e, Newtonian_Force_Event ):
			self.commit_properties( time )
			self.forces.append( e )

		elif isinstance( e, End_Event ):
			e = e.get_event( )
			if e in self.forces:
				self.commit_properties( time )
				self.forces.remove( e )

		else:
			raise Not_Executable_Exception

	def get_position( self, time ):
		"""
		Get the position of this object at a time.
		@param time The simulation time. 
		@return A @ref Numeric.array containing the position.
		"""
		a0 = zeros( (2,), 'float' )
		k = 0
		
		for e in self.forces:
			if isinstance( e, Newtonian_Force_Event ):
				a0 += e.get_linear_force( time )				
				k += e.get_damping_coefficient( time )
		
		v0 = self.v
		m = 1
		
		t = time - self.commit_time
		if k == 0:
			return self.p + t*v0 + t*t*a0
		else:
			return -m*(-k*v0 - m*a0)*math.exp( k*t/m )/(k*k) - m*a0*t/k + self.p + m*(-k*v0 - m*a0)/(k*k)

	def get_velocity( self, time ):
		"""
		Get the velocity of this object at a time.
		@param time The simulation time. 
		@return A @ref Numeric.array containing the position.
		"""
		a0 = zeros( (2,), 'float' )
		k = 0
		
		for e in self.forces:
			if isinstance( e, Newtonian_Force_Event ):
				a0 += e.get_linear_force( time )				
				k += e.get_damping_coefficient( time )
		
		v0 = self.v
		m = 1
		
		t = time - self.commit_time
		if k == 0:
			return v0 + t*a0
		else:
			return ((-k*v0 - m*a0)*math.exp( k*t/m ) + m*a0) / (-k)

	def get_speed( self, time ):
		"""
		Get the speed of this object at a time.
		@param time The simulation time. 
		@return A @ref Numeric.array containing the position.
		"""
		v = self.get_velocity( time )
		return math.sqrt( v[0]**2.0 + v[1]**2.0 )
		
	def get_orientation( self, time ):
		"""
		Get the orientation of this object at a time.
		@param time The simulation time. 
		@return The orientation between 0 and 2*\pi radians.
		"""
		ra0 = 0
		rk = 0
		
		for e in self.forces:
			if isinstance( e, Newtonian_Force_Event ):
				ra0 += e.get_rotational_force( time )				
				rk += e.get_rotational_damping_coefficient( time )
		
		rv0 = self.rv
		rm = 1
		
		t = time - self.commit_time
		if rk == 0:
			rp = self.rp + t*rv0 + t*t*ra0
		else:
			rp = self.rp - (-rm*(-rk*rv0 - rm*ra0)*math.exp( rk*t/rm )/(rk*rk) - rm*ra0*t/rk + rm*(-rk*rv0 - rm*ra0)/(rk*rk))
		
		tp = 2.0*math.pi
		while rp > tp: rp -= tp
		while rp < 0: rp += tp
		return rp

	def get_orientation_vector( self, time ):
		"""
		Get the orientation of this object as a vector at a time.
		@param time The simulation time. 
		@return The unnormalized orientation vector.
		"""
		a = self.get_orientation( time )
		return array( [float( math.cos( a ) ), float( math.sin( a ) )] )

	def get_rotational_velocity( self, time ):
		"""
		Get the rotational velocity of this object at a time.
		@param time The simulation time. 
		@return The rotational velocity in radians/second.
		"""
		ra0 = 0
		rk = 0
		
		for e in self.forces:
			if isinstance( e, Newtonian_Force_Event ):
				ra0 += e.get_rotational_force( time )				
				rk += e.get_rotational_damping_coefficient( time )
		
		rv0 = self.rv
		rm = 1
		
		t = time - self.commit_time
		if rk == 0:
			return rv0 + t*ra0
		else:
			return ((-rk*rv0 - rm*ra0)*math.exp( rk*t/rm ) + rm*ra0) / rk
		
	def commit_properties( self, time ):
		"""
		Commit the current Newtonian properties of this object.
		@param time The simulation time.
		"""
		self.p = self.get_position( time )
		self.v = self.get_velocity( time )
		self.rp = self.get_orientation( time )
		self.rv = self.get_rotational_velocity( time )
		self.commit_time = time

	def get_create_event( self ):
		"""
		Get an Object_Create_Event which duplicates this object on a 
		another Event_Manager.
		@return The event.
		"""
		kwargs = {}
		
		for slot in self.__slots__:
			kwargs[slot] = self.__dict__[slot]

		try:
			oid = Event_Manager.event_manager.get_id( self )
		except:
			oid = id( self )
				
		return Object_Create_Event( 
			Event_Manager.event_manager.game, 0,
			klass = self.__class__,
			oid = oid,
			args = None,
			kwargs = kwargs )

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
		
	def get_id( self, object ):
		return self.objects[object]

	def get_object( self, id ):
		return self.ids[id]
		
	def set_object_id( self, object, id ):
		self.objects[object] = str( id )
		self.ids[str( id )] = object
		print 'Event_Manager.set_object_id( %s, %s )' % (object, id)

class Local_Event_Manager (Event_Manager):
	def __init__( self, game ):
		Event_Manager.__init__( self, game )
		
		self.start_time = pygame.time.get_ticks( )
		self.event_queue = []
		pygame.time.set_timer( pygame.USEREVENT+1, 100 )
		
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
						del self.ids[e.event_id]
						self.event_queue.remove( ev )

						oid = self.get_id( e )
						del self.objects[e]
						del self.ids[oid]
						self.event_queue.remove( e )

				except Not_Executable_Exception, ex:
					print "Failed executing event:", ex
			
			elif e.system_lifetime[1] >= 0 and e.system_lifetime[1] <= tick:
				ee = End_Event( e.dest, 0, event = e )
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
		event_manager.server.connections.append( self.request )
		data = ' '
		
		username, pw = Network_Server.recv_packet( self.request ).split( " " )
		
		if pw != Event_Manager.event_manager.password:
			Network_Server.send_packet( self.request, "0" )
			return
		else:
			Network_Server.send_packet( self.request, '1' )
			
		event_manager.usernames[self.request] = username
		
		### Send Object_Create_Event to the new client for all objects. ###
		
		for o in event_manager.objects.keys( ):
			if isinstance( o, Object ):
				e = o.get_create_event( )
				event_manager.set_object_id( e, id( e ) )
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
		
		self.upstream = None
		if kwargs.has_key( 'upstream' ):
			self.upstream = kwargs['upstream']
			self.connections.append( self.upstream )
			
			self.send_packet( self.upstream, "%s %s" % (Event_Manager.event_manager.username,
				Event_Manager.event_manager.password) )
			
			response = self.recv_packet( self.upstream )
			if response == '1':
				print "Authentication succeeded."
			else:
				raise ValueError, "Authentication failed (%s)." % response

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
		
	@staticmethod
	def recv_packet( connection ):
		total_len = 0
		total_data = []
		size = sys.maxint
		size_data = sock_data = ''
		recv_size = 8192
		
		while total_len < size:
			sock_data = connection.recv( recv_size )
			if not total_data:
				if len( sock_data ) > 4:
					size_data += sock_data
					size = struct.unpack( '>i', size_data[:4] )[0]
					recv_size = size
					if recv_size > 524288: recv_size = 524288
					total_data.append( size_data[4:] )
				else:
					size_data += sock_data
			else:
				total_data.append( sock_data )
			total_len = sum( [len( i ) for i in total_data] )
			
		data = ''.join( total_data )
		return data

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
		Local_Event_Manager.queue_event( self, event )
		if not self.objects.has_key( event ):
			self.set_object_id( event, id( event ) )

		if not event.is_local( ):
			for c in self.server.get_connections( ):
				if c != event.source_connection:
					print "Network_Event_Manager.send( %s )" % event
					self.server.send_event( event, c )

	def get_event_class( self, class_name ):
		return self.event_classes[class_name]
		
	def shutdown( self ):
		print 'Event manager shutting down.'
		self.server.shutdown( )

	def get_connection_name( self, conn ):
		return self.usernames[conn]