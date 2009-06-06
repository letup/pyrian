import os, sys
import pygame
import random
import math
from pygame.locals import *


class Starfield:
	__slots__ = ['width', 'height', 'n', 'stars', 'v']

	def __init__( self, width, height, n ):
		self.width = width
		self.height = height
		self.n = n

		self.stars = []
		self.v = (0, 0)
		
		for i in xrange( n ):
			v = random.random( )
			d = int( v*255 )
			x = int( random.random( ) * width )
			y = int( random.random( ) * height )
			self.stars.append( [x, y, (d,d,d), v, x, y] )
		
	def update( self, dt ):
		for s in self.stars:
			s[0] += dt*self.v[0]*s[3]
			s[1] += dt*self.v[1]*s[3]

			if s[0] < 0: 
				s[0] = self.width-1
				s[3] = random.random( )
				
			elif s[0] > self.width: 
				s[0] = 0
				s[3] = random.random( )
				
			elif s[1] < 0: 
				s[1] = self.height-1
				s[3] = random.random( )

			elif s[1] > self.height: 
				s[1] = 0
				s[3] = random.random( )

			s[4] = s[0]
			s[5] = s[1]					
				
	def draw( self, surface, at ):
		for s in self.stars:
			dv = int( s[2][0]*0.75 )
			dv2 = int( s[2][0]*0.35 )
			
			x = int( s[0]+at[0] )
			y = int( s[1]+at[1] )

			c1 = s[2]
			c2 = (dv, dv, dv)
			c3 = (dv2, dv2, dv2)
			
			pygame.draw.line( surface, c1, (int( s[4] ), int( s[5] )),
				(x, y), 3 );
			surface.set_at( (x,y), c1 )

			if s[3] > 0.1:
				surface.set_at( (x+1,y), c2 )
				surface.set_at( (x-1,y), c2 )
				surface.set_at( (x,y+1), c2 )
				surface.set_at( (x,y-1), c2 )

				surface.set_at( (x+1,y+1), c3 )
				surface.set_at( (x-1,y-1), c3 )
				surface.set_at( (x-1,y+1), c3 )
				surface.set_at( (x+1,y-1), c3 )

		
	def set_velocity( self, v ):
		self.v = v
