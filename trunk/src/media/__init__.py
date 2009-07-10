import os, sys
import pygame
import random
import math
from pygame.locals import *
import gc

class Image (object):
	__slots__ = ['path', 'image', 'rect', 'images', 'last_draw']

	def __init__( self, path, rect = None ):
		self.path = path
		self.image = None
		self.images = {}
		self.rect = rect
		self.last_draw = -1

	def load_image( self ):
		if self.image == None:
			#print 'loading image', self.path
			self.image = pygame.image.load( self.path )
			self.rect = self.image.get_rect( )
		
	def get_image( self ):
		if self.image == None:
			self.load_image( )
			
		return self.image

	def get_rect( self ):
		if self.rect == None:
			self.load_image( )
			
		return self.rect
	
	def free_memory( self, *copies ):
		if len( copies ) > 0:
			for c in copies:
				if self.images.has_key( c ):
					del self.images[c]
		
	def draw( self, surface, at, *copies ):
		self.get_rect( )

		rect = self.rect
		
		
		x = at[0] - self.rect.w/2
		y = at[1] - self.rect.h/2

 		rect.move_ip( x, y )
		time = pygame.time.get_ticks( )

		if rect.colliderect( surface.get_rect( ) ):
			self.get_image( )
			
			if len( copies ) > 0:
				for c in copies:
					surface.blit( self.images[c], (x,y) )
		
			else:
				surface.blit( self.image, (x,y) )

			self.last_draw = time
			
		elif time - self.last_draw > 500 and self.last_draw > -1:
			#print 'freeing image', self.path
			self.image = None
			self.images = None
			self.last_draw = -1

		rect.move_ip( -x, -y )

		#pygame.draw.circle( surface, (255,0,0), (int( at[0] ), int( at[1] )), 3, 2 )
		
	def get_copy( self, name ):
		if not self.images.has_key( name ):
			self.images[name] = self.image.copy( )
			
		return self.images[name]

class Animation:
	__slots__ = ['image_map', 'state_times', 'state_offsets',
		'state_ranges']
	
	def __init__( self, path_pattern, *state_ranges ):
		self.image_map = {}

		def build_images_rec( path_pattern, image_map, n, d, *state_ranges ):
			if len( state_ranges ) == 0:
				image_map[tuple( n )] = Image( path_pattern )
				return
		
			child_state_ranges = state_ranges[1:]
			n = n[:]
		
			for i in xrange( state_ranges[0] ):
				var = "$" + str( d+1 )
				path = path_pattern.replace( var, str( i ) )
				n[d] = i
				build_images_rec( path, image_map, n, d+1, *child_state_ranges )
			
		build_images_rec( path_pattern, self.image_map, 
			[0 for s in state_ranges], 0, *state_ranges )
			
		rect = self.image_map.values( )[0].get_rect( )
		for img in self.image_map.values( ):
			img.rect = rect
			
		self.state_ranges = state_ranges[:]
		self.state_times = [0 for s in self.state_ranges]
		self.state_offsets = [0 for s in self.state_ranges]

	def set_time( self, state, time ):
		if time < 0: time = 0.0
		if time > 1: time = 1.0
		self.state_times[state] = time
		self.state_offsets[state] = int( time * self.state_ranges[state] )

	def add_time( self, state, dt, **kwargs ):
		self.state_times[state] += dt
		t = self.state_times[state]
		
		if kwargs.has_key( 'cyclic' ) and kwargs['cyclic']:
			while t > 1.0: t -= 1.0
			while t < 0: t += 1.0
		else:
			if t > 1.0: t = 1.0
			elif t < 0: t = 0.0

		self.state_times[state] = t		
		self.state_offsets[state] = min( int( t * self.state_ranges[state] ), self.state_ranges[state]-1 )

	def draw( self, surface, at ):
		img = self.image_map[tuple( self.state_offsets )]
		img.draw( surface, at )
