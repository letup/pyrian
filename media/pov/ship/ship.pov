#include "colors.inc"

/* 

 *** Animations ***

 * ANIMATION -- name: ship_firing[32], 	frames: 10, 	duration: 0.5
 * ANIMATION -- name: ship[32], 		frames: 10, 	duration: 0.5

 */

camera
{
    orthographic
    
    up			<0, 120, 0>
    right		<160, 0, 0>
    location	<0, 1, 0.5> * 500
    look_at		<0, 0, 0>
}

light_source
{
					<0.2, 1, -0.9> * 600
    color rgb		0.9
}

light_source
{
					<0, -1, 0> * 600
    color rgb		0.5
}

/* *** Textures *** */

#declare hull_finish = finish
{
    phong 	1 
    reflection 	1
    metallic
}

#declare glow_texture = texture
{    
    pigment
    { 
		bozo
		
		color_map
		{
		    [0		rgb <0, 0, 1>]
		    [0.5	rgb <0, 0, 1>]
		    [0.9	rgb <0.8, 0.8, 1>]
		    [1.0	rgb <0.8, 0.8, 0.1>]
		}
    }

    finish	{ hull_finish ambient (0.1*sin( clock*2*3.14159 ))+0.2 }
   	normal	{ wrinkles 1 scale sin( clock*2*3.14159 ) + 0.1 }
}

/* *** Object *** */

#declare gun = union
{
    sphere		
    { 
        0, 1 
        scale		<0.3, 0.3, 1>

        pigment		{ color rgb 0.7 }	
        finish		{ hull_finish }
    }


    difference
    {
	sphere		
	{ 
    	    0, 1 
    	    scale		<0.3, 0.3, 1> * 1.01

	    texture		{ glow_texture }
	}
	
	box
	{
	    <-1, -1, -0.8>, <1, 1, 0.8>
	    pigment 		{ color Blue }
	}
    }

    /* rings */
    
    #local i = 0.6;

    #while( i < 0.8 )
	torus		
	{ 
	    sqrt( 1 - (i*i) ) * 0.3, 0.04
	    
	    rotate	90*x
	    translate	i*z
	    
	    texture	{ glow_texture }
	}

	#local i = i + 0.1;
    #end

    #local i = -0.6;

    #while( i > -0.8 )
	torus		
	{ 
	    sqrt( 1 - (i*i) ) * 0.3, 0.04
	    
	    rotate	90*x
	    translate	i*z
	    
	    texture	{ glow_texture }
	}

	#local i = i - 0.1;
    #end
    
    /* zapper */
    
    cylinder
    {
	0, 1.3*z, 0.05
	
	texture		{ glow_texture }
    }
    
    sphere
    {
	1.3*z, 0.08

	texture		{ glow_texture }
    }
    
    torus
    {
	0.1, 0.04
	
	rotate		90*x
	translate	1.2*z
	
	texture		{ glow_texture }
    }
}

#declare wing = union
{
    sphere
    {
	0, 1
	scale		<1.1, 0.05, 0.4>

	translate	<0, 0, -0.1>

        pigment		{ color rgb 0.7 }	
        finish		{ hull_finish }
    }
    
    object		{ gun scale 0.5 translate <-1.1, 0, -0.1> }
    object		{ gun scale 0.5 translate <1.1, 0, -0.1> }
}

#declare gun_firing = union
{
	object { gun }

#local i = 0;
#local r = seed( 0 );
#while (i < 40)
	light_source
	{
						<(4*rand( r ))-2, (4*rand( r ))-2, 1.4 + 3*rand( r )>
		#if (rand( r ) > 0.2)
 	    	color rgb		<0, 0, 1>
 	    #else
 	    	color rgb		<1, 1, 0>    
 	    #end
	    spotlight
    	radius			2 + rand( r )
	    falloff			1
    	point_at		<0, 0, rand( r )>
	    tightness		2

    	rotate			z*clock*2*360
    }
    
    #local i = i+1;
#end
}

#declare rotation	= y * (ANIM_NUM/32) * 360;

union
{

#ifdef (ship)
    object		{ gun }
#else
    object		{ gun_firing }
#end
    object		{ wing rotate z * 18 }
    object		{ wing rotate z * -18 }
    
    scale 		20
    
    rotate		rotation + (-90 * y)
}
