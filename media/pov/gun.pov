#include "colors.inc"

/* 

 *** Animations ***

 * ANIMATION -- name: gun[1], 		frames: 20, 	duration: 0.5

 */


/* *** Gatling Gun *** */

#declare gun_texture = texture
{
    pigment
    {
	granite
	color_map
	{
	    [0.0	rgb <0.5, 0.5, 0.5>]
	    [0.5	rgb <0.4, 0.4, 0.4>]
	    [1.0	rgb <0.9, 0.5, 0.3>]
        }
    }

    normal 		{ wrinkles 1 scale 0.1 }
    finish		{ phong 1 metallic }
}

#declare platform = intersection
{
    sphere		{ <0, 0.1, 0>, 1 }
    box			{ <-0.5, -100, -0.5>, <0.5, 100, 0.5> }
    
    texture 		{ gun_texture }
}

#declare platform_bolts = intersection
{
    object		{ platform translate y*0.04 }
    
    union
    {
	#local i	= -0.5;
	
	#while( i < 0.51 )
	    #local j	= -0.5;
	
	    #while( j < 0.51 )
		#if( i = -0.5 )
		    cylinder		{ <i, -100, j>, <i, 100, j>, 0.05 }
		#else
		    #if( i = 0.5 )
			cylinder	{ <i, -100, j>, <i, 100, j>, 0.05 }
		    #end
		#end

		#if( j = -0.5 )
		    cylinder		{ <i, -100, j>, <i, 100, j>, 0.05 }
		#else
		    #if( j = 0.5 )
		        cylinder	{ <i, -100, j>, <i, 100, j>, 0.05 }
		    #end
		#end
	    
		#local j = j + 0.2;
	    #end
	
	    #local i = i + 0.2;
	#end
	
	scale				<0.8, 1, 0.8>
    }
    
    texture		{ gun_texture }
}

#declare platform = union
{
    object		{ platform }
    object		{ platform_bolts }

    /* stand */
    
    box			{ <-0.2, 0, -0.3>, <0.2, 1.4, 0.3> texture { gun_texture } }
    
    scale		<0.8, 1, 0.8>
}

#declare bandolier = union
{
    /* where it's going to be put */
    
    #local P 		= <0, 0.3, 0>;
    #local P		= <0, 1.4, -0.2> + vrotate( P, -45*z );

    #local s 	= seed( clock * 100 );
    #local i 	= 0;
    #local n	= 0.05;
    
    #local px 	= P.x;
    #local py	= P.y;
    #local pz	= P.z;

    #while( i < 1 )
	#if( (i / n) < 1 )
	    #local px 	= px + n;
	    #local py 	= py + n;
	#else
	    #if( vlength( <px, py, pz> ) > 1 )
		#local px	= px + 0.02;
		#local py 	= py - n;
		#local pz	= pz - 0.01;
	    #else
		#local px	= px + n;
		#local py 	= py - n;	    
	    #end
	#end
	
	#local q	= 0.3 * i * sin( (i + clock) * 2 * 3.14159 );
	#local r 	= <rand( s ), rand( s ), rand( s )> * 0.05;
	#local p 	= <px, py + q, pz> + r;
	#local r 	= <rand( s ), rand( s ), rand( s )> * 30;
	
	/* bullet */
	
	union
	{
	    cylinder	{ -0.5*z, 0.5*z, 0.03 pigment { color rgb <0.7, 0.7, 0.7> } }
	    cylinder	{ -0.3*z, 0.3*z, 0.0301 pigment { color Brown } }
	    
	    scale	<1, 1, 0.4>
	    
	    rotate	r
	    translate	p
	    
	    #local p1	= vrotate( -0.3*z*0.4, r ) + p;
	    #local p2	= vrotate( 0.3*z*0.4, r ) + p;
	}

	/* binding */
	
	#if( i > 0 )
	    triangle
	    {
		p1, p2, lp1

		pigment { color Brown }
	    }

	    triangle
	    {
		p2, lp2, lp1

		pigment { color Brown }
	    }
	#end

	#local lp1 = p1;
	#local lp2 = p2;

	#local i = i + n;
    #end
}

#declare gun = union
{
    /* main body */

    difference
    {
	union
	{
	    cylinder 	{ 0, 1.5*z, 0.3 }
	    cylinder	{ 1.3*z, 1.5*z, 0.32 }
	    
	    #local i = 0;
	    
	    #while( i < 360 )
		cylinder	
		{ 
		    0.4*z, 1.3*z, 0.02
		    
		    translate	0.3*y
		    rotate	i*z
		}
	
		#local i = i + 30;
	    #end
	}
	
	cylinder 	{ 0.1*z, 1.51*z, 0.23 }
    }
    
    cylinder 		{ 0, 1.7*z, 0.2 }
    
    /* bullet feed */
    
    difference
    {
	box		{ <-0.6, 0, -0.6>, <0.6, 0.5, 0.6> }
	box		{ <-0.5, 0, -0.5>, <0.5, 0.6, 0.5> }
	
	scale		<0.1, 0.2, 0.4>
	translate	<0, 0.3, 0.4>
	rotate		-45*z
    }

    /* sight */

    union
    {
        difference
        {
	    cylinder	{ -1*z, 1*z, 1.6 }
	    cylinder	{ -1.1*z, 1.1*z, 1.2 }
	}

	cylinder	{ <-sqrt(2)/2, -sqrt(2)/2, 0>, <-sqrt(2)/2, -2, 0>, 0.4 }
	cylinder	{ <sqrt(2)/2, -sqrt(2)/2, 0>, <sqrt(2)/2, -2, 0>, 0.4 }
	
	cylinder	{ -y, y, 0.1 pigment { color Black } scale <1, 1, 3> }
	cylinder	{ -x, x, 0.1 pigment { color Black } scale <1, 1, 3> }

	cylinder	{ -0.1*z, 0.1*z, 1.3 pigment { color rgbf <1.0, 0.6, 0.3, 0.2> } }
	
	scale		<0.1, 0.1, 0.01>
	translate	<0, 0.5, 1>
    }
    
    /* barrels */

    #local explosion	= object
    {
	sphere	{ 0, 0 pigment { color Yellow } }
    }

    difference
    {
	union
	{    
	    cylinder	{ 0, 1.8*z, 0.05 translate <-0.1, 0.1, 0> }
	    cylinder	{ 0, 1.8*z, 0.05 translate <0.1, 0.1, 0> }
	    cylinder	{ 0, 1.8*z, 0.05 translate <0, -0.1, 0> }
	
	    #local n	= rand( s ) * 3;
	
	    #if( n <= 1 )
		#local p		= <-0.1, 0.1, 1.9>;
	    #else
		#if( n <= 2 )
		    #local p		= <0.1, 0.1, 1.9>;
	    
		#else
		    #if( n <= 3 )
			#local p	= <0, -0.1, 1.9>;
		    #end
		#end
	    #end

	    object		{ explosion translate p }
	}

	union
	{    
	    cylinder	{ 0, 1.81*z, 0.04 translate <-0.1, 0.1, 0> }
	    cylinder	{ 0, 1.81*z, 0.04 translate <0.1, 0.1, 0> }
	    cylinder	{ 0, 1.81*z, 0.04 translate <0, -0.1, 0> }
	}

	#local p 	= <rand( s ), rand( s ), rand( s )> * 0.05;
	translate	p	
	//rotate		720 * clock * z
    }
    
    texture		{ gun_texture }
    
    translate		<0, 1.4, -0.6>
}

/* *** Scene *** */

camera
{
    location	<0, 1, 1> * 6
    look_at		<0, 1.4, 0>
}

light_source
{
					<0.2, 1, -0.9> * 600
    color rgb		0.9
}

light_source
{
					<0, -1, 1> * 600
    color rgb		0.5
}


#local s		= seed( clock * 100 );

union
{    
    object 		{ gun 			rotate y*clock*2*360 }
    object		{ bandolier 	rotate y*clock*2*360 }
    //object		{ platform 		rotate clock*360 }
}

