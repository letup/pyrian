import os, sys
import pygame
import random
import math
from pygame.locals import *
import Numeric

class Shield_Effect:
	def __init__( self, w, h, over ):
		self.w = w
		self.h = h
		self.last_update = pygame.time.get_ticks( )
		self.first_time = self.last_update
		self.surface = pygame.surface.Surface( (w, h), SRCALPHA, 32 )
		self.surface.convert_alpha( )
		self.over = over

		parray = pygame.surfarray.pixels3d( self.surface )
		parray[:,:] = (255, 255, 255)
		
		self.ttma = Numeric.zeros( (w, h), 'b' )
		self.dv = Numeric.zeros( (w, h), 'b' )
		self.rand_plus = Numeric.zeros( (w, h), 'b' )
		self.rand_minus = Numeric.zeros( (w, h), 'b' )
		self.active = False

		def center_dist( i, j ):
			x = w/2.0 - i
			y = h/2.0 - j
			d = math.sqrt( x*x + y*y )
			d = 1.0 - pow( d/max( w/2, h/2 ), 2.0 )
			if d < 0: return 0
			return int( d*255 )
		
		jr = range( 0, self.h )
		ir = range( 0, self.w )

		for j in jr:
			for i in ir:
				self.dv[i,j] = center_dist( i, j )
				self.rand_plus[i,j] = random.random( )*20
				self.rand_minus[i,j] = random.random( )*20
	
	def set_active( self, active, t ):
		self.active = active
		self.first_time = t
	
	def update( self, t ):
		if not self.active:
			return 

		dt = (t - self.last_update)
		self.last_update = t
		
		tt = (t - self.first_time)
		ttm = pow( 0.2*math.sin( tt*math.pi )+0.6, 2.0 )
		ttm = int( 1/ttm )
		
		if ttm < 2:	ttm = 2
		if ttm > 5:	ttm = 5
		
		ttm = 5 - ttm + 2
		
		self.ttma[:,:] = ttm
		aarray = pygame.surfarray.pixels_alpha( self.surface )
		Numeric.floor_divide( self.dv, self.ttma, aarray )
		
	def draw( self, surface, at ):
		if not self.active:
			return 
			
		r = self.surface.get_rect( )
		p = (at[0] - r.width/2, at[1] - r.height/2)
		surface.blit( self.surface, p )
