import math
import sys

import Numeric
from effects import *
from effects.starfield import Starfield
from effects.shield import Shield_Effect
from manager import *
from media import *
from media import Animation
import os
from physics import *

import pygame
from pygame import Rect
from pygame.locals import *

import random
import traceback

def combinations(items, n):
	if n==0: yield []
	else:
		for i in xrange(len(items)):
			for cc in combinations(items[i+1:],n-1):
				yield [items[i]]+cc

def char_plus_shift( c ):
	if c == "/": return "?"
	elif c == "-": return "_"
	elif c == ",": return "<"
	elif c == ".": return ">"
	elif c == ";": return ":"
	elif c == "'": return "\""
	elif c == "[": return "{"
	elif c == "]": return "}"
	elif c == "\\": return "|"
	elif c == "=": return "+"
	elif c == "0": return ")"
	elif c == "1": return "!"
	elif c == "2": return "@"
	elif c == "3": return "#"
	elif c == "4": return "$"
	elif c == "5": return "%"
	elif c == "6": return "^"
	elif c == "7": return "&"
	elif c == "8": return "*"
	elif c == "9": return "("
	elif c == "`": return "~"
	else: return c.upper( )

class Game:
	def __init__( self, media_base, width=200, height=100, interactive=False ):
		pygame.init( )
		self.width = width
		self.height = height
		self.screen = pygame.display.set_mode( (width, height), 0, 32 )
		self.media_base = media_base
		self.level = Level( )
		
	def get_dt( self ):
		return self.level.dt
		
	def get_time( self ):
		return self.level.get_time( )
		
	def run( self ):
		self.level.run( self.screen )
		
	def run_thread( self ):
		self.thread = Thread( target = self.run, args = [self] )

	def get_class( self, class_name ):
		return globals( )[class_name]

	def get_create_event( self ):
		return None
		
	def execute_event( self, event, time ):
		if isinstance( event, Object_Create_Event ):
			try:
				Event_Manager.event_manager.get_object( event.oid )
			except:
				o = event.klass( **event.kwargs )
				if event.oid == None:
					game.event_manager.set_object_id( o, str( event_manager.new_id( ) ) )
					event.oid = str( event_manager.new_id( ) )
				else:
					game.event_manager.set_object_id( o, str( event.oid ) )
				print "Game.create_object( %s, %s )" % (event.klass,
					game.event_manager.get_id( o ))
				o.source_connection = event.source_connection
				self.level.objects.append( o )
				self.level.collision_detector.add_object( o, Event_Manager.event_manager.get_time( ) )
				#print [(o.__class__.__name__, o.p) for o in self.level.objects]

		elif isinstance( event, Message_Event ):
			self.level.text_lines.insert( 0, (pygame.time.get_ticks( ), 
				"%s: %s" % (event.name,	event.msg)) )

		elif isinstance( event, Collision_Event ):
			self.level.collision_detector.execute_event( event, time )

class Ship (Object):
	__slots__ = ['name']

	def __init__( self, **kwargs ):
		Object.__init__( self, **kwargs )
		self.reg_anim = Animation( game.media_base + "/images/ship/ship[$2]$1.png", 3, 32 )
		self.fire_anim = Animation( game.media_base + "/images/ship/ship_firing[$2]$1.png", 3, 32 )
		self.anim = self.reg_anim
		self.thrust = 0
		self.key_events = {}
		self.damping_events = []
		self.shield = Shield_Effect( 120, 120, self )
		
#		self.name = Event_Manager.event_manager.username
		self.name = username
		self.__dict__.update( kwargs )

	def __repr__( self ):
		return "Ship( %s, %s )" % (self.name, event_manager.get_id( self ))
		
	def draw( self, surface, c ):
		self.anim.add_time( 0, game.get_dt( ), cyclic = True )
		self.anim.set_time( 1, self.get_orientation( 
			event_manager.get_time( ) ) / (2*math.pi) )
		self.anim.draw( surface, c )
		self.shield.update( event_manager.get_time( ) )
		self.shield.draw( surface, c )
		
	def execute_event( self, e, time ):
		if isinstance( e, Activation_Event ):
			for o in e.objs.keys( ):
				if self.__dict__.has_key( o ):
					self.__dict__[o].set_active( e.objs[o], time )
			
		Object.execute_event( self, e, time )
		
	def handle_input_event( self, event ):
		rem = []
		for e in self.damping_events:
			if not e.is_alive( ):
				rem.append( e )
		for e in rem:
			self.damping_events.remove( e )
			
		if event.type == KEYDOWN:
			if event.key == K_UP: 
				for e in self.damping_events:
					if isinstance( e, Damping_Force_Event ):
						try: event_manager.queue_event( End_Event( e.dest, 0, end_id = event_manager.get_id( e ) ) )
						except: pass
				self.key_events[K_UP] = [
					Oriented_Force_Event( self, 0, Event.INDEFINITE, m = 200.0, ro = 0 )]
				for e in self.key_events[K_UP]:
					event_manager.queue_event( e )
				
			elif event.key == K_LEFT:
				for e in self.damping_events:
					if isinstance( e, Rotational_Damping_Force_Event ):
						try: event_manager.queue_event( End_Event( e.dest, 0, end_id = event_manager.get_id( e ) ) )
						except: pass
				self.key_events[K_LEFT] = [
					Rotational_Force_Event( self, 0, Event.INDEFINITE, ra = 4.0 ),
					Rotational_Force_Event( self, 0.6, Event.INDEFINITE, ra = -4.0 )]
				event_manager.queue_event( self.key_events[K_LEFT][0] )
				event_manager.queue_event( self.key_events[K_LEFT][1] )

			elif event.key == K_RIGHT:
				for e in self.damping_events:
					if isinstance( e, Rotational_Damping_Force_Event ):
						try: event_manager.queue_event( End_Event( e.dest, 0, end_id = event_manager.get_id( e ) ) )						
						except: pass
				self.key_events[K_RIGHT] = [
					Rotational_Force_Event( self, 0, Event.INDEFINITE, ra = -4.0 ),
					Rotational_Force_Event( self, 0.6, Event.INDEFINITE, ra = 4.0 )]
				event_manager.queue_event( self.key_events[K_RIGHT][0] )
				event_manager.queue_event( self.key_events[K_RIGHT][1] )

			elif event.key == K_s:
				self.key_events[K_s] = [Activation_Event( self, 0, shield = True )]
				event_manager.queue_event( self.key_events[K_s][0] )

		elif event.type == KEYUP:
			rdamp = False
			damp = False
		
			if self.key_events.has_key( event.key ):
				for e in self.key_events[event.key]:
					if isinstance( e, Oriented_Force_Event ):
						event_manager.queue_event( End_Event( e.dest, 0, end_id = event_manager.get_id( e ) ) )
						damp = True
					elif isinstance( e, Rotational_Force_Event ):
						event_manager.queue_event( End_Event( e.dest, 0, end_id = event_manager.get_id( e ) ) )
						rdamp = True
					elif isinstance( e, Activation_Event ):
						event_manager.queue_event( Activation_Event( self, 0, shield = False ) )
						
				del self.key_events[event.key]

			if damp:
				ev = Damping_Force_Event( self, 0, 1.0, c = -10 )
				event_manager.queue_event( ev )
				self.damping_events.append( ev )

			if rdamp:
				ev = Rotational_Damping_Force_Event( self, 0, 1.0, c = -5 )
				event_manager.queue_event( ev )
				self.damping_events.append( ev )

class Camera:
	def __init__( self, rect, focus ):
		self.rect = rect
		self.focus = focus
		self.starfield = Starfield( rect.width, rect.height, 200 )

		self.black = pygame.Surface( (rect.width, rect.height), RLEACCEL )
		self.black.convert( )
		self.black.fill( (0, 0, 0) )

		self.blur = pygame.Surface( (rect.width, rect.height), 0 )
		self.blur.convert( )
		self.blur.fill( (0, 0, 0) )
		self.blur.set_alpha( 100 )
		
	def draw( self, objects, surface, at ):
		t = event_manager.get_time( )
		clip = surface.get_clip( )
		surface.set_clip( Rect( at[0], at[1], self.rect.width, self.rect.height ) )

		surface.blit( self.black, at )
		surface.blit( self.blur, at )
		self.starfield.set_velocity( -1.0 * self.focus.get_velocity( t ) )
		self.starfield.update( game.get_dt( ) )
		self.starfield.draw( surface, at )
		
		fp = self.focus.get_position( t )
		
		for o in objects:
			p = o.get_position( t )
			p = (p[0] - fp[0] + at[0] + self.rect.width/2, 
				 p[1] - fp[1] + at[1] + self.rect.height/2)
			o.draw( surface, p )
			#if o != objects[0]:
			#	print p
			#elif len( objects ) > 1:
			#	print p
		
		self.blur.blit( surface, (0, 0) )
		surface.set_clip( clip )

class Collision_Detector:
	def __init__( self, grid_size ):
		self.grid_size = int( grid_size )
		self.grid = {}
		self.positions = {}
		self.objects = []
		self.collisions = {}
		
	def position_to_grid( self, p ):
		return (int( p[0] / float( self.grid_size ) ),
			int( p[1] / float( self.grid_size ) ))
		
	def add_object( self, obj, time ):
		self.objects.append( obj )
		p = obj.get_position( time )
		self.positions[obj] = p
		p = self.position_to_grid( p )
		
		if self.grid.has_key( p ):
			self.grid[p].append( obj )
		else:
			self.grid[p] = [obj]
			
	def execute_event( self, event, time ):
		if isinstance( event, Collision_Event ):
			pass
		
	def compute_collisions( self, time ):
		for obj in self.objects:
			p1 = obj.get_position( time )
			p2 = self.positions[obj]
			self.positions[obj] = p1

			p1 = self.position_to_grid( p1 )
			p2 = self.position_to_grid( p2 )

			if p1[0] != p2[0] or p1[1] != p2[1]:
				if self.grid.has_key( p1 ):
					self.grid[p1].append( obj )
				else:
					self.grid[p1] = [obj]

				if self.grid.has_key( p2 ):
					if obj in self.grid[p2]:
						self.grid[p2].remove( obj )
						if len( self.grid[p2] ) == 0:
							del self.grid[p2]

		for gp in self.grid.keys( ):
			gpo = self.grid[gp]

			for gp2 in ((gp[0]-1,gp[1]), (gp[0], gp[1]+1), gp):
				if self.grid.has_key( gp2 ):
					gpo2 = self.grid[gp2]
				
					for pair in combinations( list( set( gpo + gpo2 ) ), 2 ):
						o1 = pair[0]
						o2 = pair[1]
							
						if o1 != o2:
							k = (o1, o2)
							if o1 > o2:
								k = (o2, o1)
						
							if (not self.collisions.has_key( k ) or
								time - self.collisions[k] > .5):
								if o1.collides( o2, time ):
									self.collisions[k] = time
									print "%s collides with %s" % (o1, o2)
									print self.collisions, time, self.collisions[k]
									
							elif (self.collisions.has_key( k ) and
								time - self.collisions[k] > .5):
								del self.collisions[k]
	
class Level:
	def __init__( self ):
		self.objects = []
		self.text_lines = []
		self.msg_buffer = None
		self.collision_detector = Collision_Detector( 200 )
	
	def get_time( self ):
		return Event_Manager.event_manager.get_time( )
	
	def run( self, surface ):
		font = pygame.font.Font( None, 18 )

		fps = 0		
		frames = 0
		last_fps = pygame.time.get_ticks( )		
		last_time = last_fps
		
		w = surface.get_size( )[0]
		h = surface.get_size( )[1]
		
		p = Numeric.array( [random.random( )*500.0, 0] )
		s = Ship( p = p )
		event_manager.set_object_id( s, event_manager.new_id( ) )
		self.objects.append( s )
		self.collision_detector.add_object( s, 0 )
		event_manager.queue_event( s.get_create_event( ) )
		
		camera = Camera( Rect( 0, 0, w, h ), s )
		
		while True:
			### Handle events. ###
			
			for event in pygame.event.get( ):
				if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
					print 'Exitting...'
					print Event_Manager.event_manager.objects
					print Event_Manager.event_manager.event_queue
					Event_Manager.event_manager.shutdown( )
					sys.exit( )
				elif event.type == KEYDOWN and event.key == K_RETURN:
					pygame.key.set_repeat( 500, 75 )
					if self.msg_buffer != None:
						if len( self.msg_buffer ) > 0:
							event_manager.queue_event( Message_Event( game, 0, msg = self.msg_buffer, name = username ) )
						self.msg_buffer = None
						pygame.key.set_repeat( )
					else:
						self.msg_buffer = ""
				elif event.type == KEYDOWN and self.msg_buffer != None:					
					try:
						if pygame.key.get_mods( ) & (KMOD_SHIFT|KMOD_CAPS):
							self.msg_buffer += char_plus_shift( chr( event.key ) )
						elif event.key == K_BACKSPACE:
							self.msg_buffer = self.msg_buffer[:len( self.msg_buffer )-1]
						else:
							self.msg_buffer += chr( event.key )
					except:
						pass
				elif event.type == USEREVENT+1:
					event_manager.handle_pygame_event( event )
				else:
					s.handle_input_event( event )

			### Compute frame-rate info. ###

			if pygame.time.get_ticks( ) - last_fps > 1000:
				fps = frames / (float( pygame.time.get_ticks( ) - last_fps ) / 1000.0)
				last_fps = pygame.time.get_ticks( )
				frames = 0

			if fps > 30:
				pygame.time.wait( 10 )

			dt = (pygame.time.get_ticks( ) - last_time) / 1000.0
			self.dt = dt
			last_time = pygame.time.get_ticks( )
			
			self.objects.sort( cmp = lambda o1, o2: int( o1.p[1] - o2.p[1] ) )

			self.collision_detector.compute_collisions( event_manager.get_time( ) )
			
			### Draw objects. ###

			camera.draw( self.objects, surface, (0, 0) )
			
			#text = font.render( "%f frames/s" % fps, 1, (255, 255, 255) )
			text = font.render( "%f" % Event_Manager.event_manager.get_time( ), 1, (255, 255, 255) )
			surface.blit( text, (10, 10) )
			
			oi = 1
			for o in self.objects:
				p = o.get_position( event_manager.get_time( ) )
				rp = o.get_speed( event_manager.get_time( ) )
				#print o.get_orientation( event_manager.get_time( ) ) * 180.0/3.14159, o.get_rotational_velocity( event_manager.get_time( ) ), len( o.forces )
				#print "%s = %s" % (o, p)
				text = font.render( "(%d, %d) (%.2f)" % 
					(p[0], p[1], rp), 1, (255, 255, 255) )
				surface.blit( text, (10, 590 - (oi * 20)) )
				oi += 1

			while len( self.text_lines ) > 0 and pygame.time.get_ticks( ) - self.text_lines[0][0] > 10000:
				self.text_lines.pop( 0 )

			oi = 1
			for o in self.text_lines:
				text = font.render( "%s" % o[1], 1, (255, 255, 255) )
				surface.blit( text, (200, 570 - (oi * 20)) )
				oi += 1
				
			if self.msg_buffer != None:
				text = font.render( "%s" % self.msg_buffer, 1, (255, 255, 0) )
				surface.blit( text, (200, 570) )
					
			pygame.display.flip( )
			frames += 1

if __name__ == "__main__":
	if len( sys.argv ) not in (5,6):
		print "Usage: %s <host> <port> <username> <password> [media-path]" % sys.argv[0]
		sys.exit( 1 )

	media_base = os.getcwd( ) + "/../media"

	host = sys.argv[1]
	port = int( sys.argv[2] )
	username = sys.argv[3]
	password = sys.argv[4]

	if len( sys.argv ) > 5:
		media_base = sys.argv[6]

	game = Game( media_base, 800, 600 )

	event_manager = Naive_Network_Event_Manager( host, port, game, 
		username, password, [
		Object_Create_Event,
		Newtonian_Force_Event,
		Linear_Force_Event,
		Rotational_Force_Event,
		Oriented_Force_Event,
		Message_Event,
		Damping_Force_Event,
		Rotational_Damping_Force_Event,
		End_Event,
		Object_Commit_Event,
		Set_Event,
		Add_Event,
		Activation_Event,
		Collision_Event,
		Clock_Event] )

	try:
		game.run( )
	except Exception, ex:
		traceback.print_exc( )
		sys.exit( )
