import pygame
import SocketServer
from threading import *
from manager import Event_Manager, Event, End_Event
import socket
import copy
import traceback
import pickle
import struct
import sys
import random

from Numeric import array, zeros
import math

class Object_Commit_Event (Event):
	__slots__ = ['state']

	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )
		self.state = kwargs['state']

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

class Set_Event (Event):
	__slots__ = ['key', 'value']
	
	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )
		self.key = kwargs['key']
		self.value = kwargs['value']

class Add_Event (Event):
	__slots__ = ['key', 'value']
	
	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )
		self.key = kwargs['key']
		self.value = kwargs['value']

class Activation_Event (Event):
	__slots__ = ['objs']
	
	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )	
		if kwargs.has_key( 'objs' ):
			self.objs = kwargs['objs']
		else:
			self.objs = kwargs
	
class Collision_Event (Event):
	__slots__ = ['o1','o2','v1','v2','p1','p2']
	
	def __init__( self, dest, dtime, **kwargs ):
		Event.__init__( self, dest, dtime, dtime )	
		self.o1 = Event_Manager.event_manager.get_id( kwargs['o1'] )
		self.o2 = Event_Manager.event_manager.get_id( kwargs['o2'] )
		self.v1 = kwargs['v1']
		self.v2 = kwargs['v2']
		self.p1 = kwargs['p1']
		self.p2 = kwargs['p2']
	
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
		self.source_connection = None
	
	def execute_event( self, e, time ):
		"""
		Execute a simulation event.
		@param e The event.
		"""
		if isinstance( e, Newtonian_Force_Event ):
			self.commit_properties( time, e )
			self.forces.append( e )

		elif isinstance( e, End_Event ):
			e = e.get_event( )
			if e in self.forces:
				self.commit_properties( time, e )
				self.forces.remove( e )

		elif isinstance( e, Object_Commit_Event ) and e.source_connection != None:
			self.set_state( e.state, time )

		elif isinstance( e, Set_Event ):
			self.commit_properties( time, e )
			self.__dict__[e.key] = e.value

		elif isinstance( e, Add_Event ):
			self.commit_properties( time, e )
			self.__dict__[e.key] += e.value

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
			rp = -rm*(-rk*rv0 - rm*ra0)*math.exp( rk*t/rm )/(rk*rk) - rm*ra0*t/rk + self.rp + rm*(-rk*rv0 - rm*ra0)/(rk*rk)
		
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
			return ((-rk*rv0 - rm*ra0)*math.exp( rk*t/rm ) + rm*ra0) / (-rk)
		
	def commit_properties( self, time, commit_event ):
		"""
		Commit the current Newtonian properties of this object.
		@param time The simulation time.
		@param commit_event Event causing the commit.
		"""

		self.p = self.get_position( time )
		self.v = self.get_velocity( time )
		self.rp = self.get_orientation( time )
		self.rv = self.get_rotational_velocity( time )
		self.commit_time = time
		if commit_event.source_connection == None:
			e = Object_Commit_Event( self, 0, state = self.get_state( ) )
			Event_Manager.event_manager.queue_event( e )

	def get_state( self ):
		kwargs = {}
		
		for slot in self.__dict__.keys( ):
			if slot in (self.__slots__,'p','v','rp','rv'):
				kwargs[slot] = self.__dict__[slot]

		#print 'get_state( %s ) = %s' % (self, kwargs)

		return kwargs
		
	def set_state( self, state, time ):
		#print 'set_state( %s, %s )' % (self, state)
		self.__dict__.update( state )
		self.commit_time = time

	def get_create_event( self ):
		"""
		Get an Object_Create_Event which duplicates this object on a 
		another Event_Manager.
		@return The event.
		"""
		kwargs = self.get_state( )

		try:
			oid = Event_Manager.event_manager.get_id( self )
		except:
			oid = Event_Manager.event_manager.next_id( self )
				
		return Object_Create_Event( 
			Event_Manager.event_manager.game, 0,
			klass = self.__class__,
			oid = oid,
			args = None,
			kwargs = kwargs )

	def collides( self, obj, time ):
		p1 = self.get_position( time )
		p2 = obj.get_position( time )
		x = p1[0]-p2[0]
		y = p1[1]-p2[1]
		d = x*x + y*y
		
		if d < 10000:
			o1 = self
			o2 = obj
		
			p1 = o1.get_position( time )
			v1 = o1.get_velocity( time )
			s1 = o1.get_speed( time )
							
			p2 = o2.get_position( time )
			v2 = o2.get_velocity( time )
			s2 = o2.get_speed( time )
							
			dp = p1-p2
			d = math.sqrt( d )
			if d == 0: d = 1.0
			dp /= d
							
			ns = (s1+s2)/2.0
			v = (v1+v2)/2.0
			if v[0] == 0: v[0] = 1.0
			v /= math.sqrt( v[0]*v[0] + v[1]*v[1] )

			Event_Manager.event_manager.queue_event(
				Collision_Event( Event_Manager.event_manager.game, 0, o1 = o1, o2 = o2,
					p1 = p1+.5*dp*(150-d),
					p2 = p2-.5*dp*(150-d),
					v1 = v*ns,
					v2 = -v*ns ) )

			return True
			
		return False