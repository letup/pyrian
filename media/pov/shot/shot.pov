#include "colors.inc"

/* 

 *** Animations ***

 * ANIMATION -- name: shot[1], 	frames: 24, 	duration: 0.5

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
    color rgb		0.9
}

/* *** Textures *** */

#declare hull_finish = finish
{
    phong 	1 
    //reflection 	1
    metallic
}

#macro glow_texture( a )
texture
{
    pigment
    { 
		bozo
		
		color_map
		{
		    [0		rgbf <0, 0, 1, a>]
		    [0.5	rgbf <0, 0, 1, a>]
		    [0.6	rgbf <0.8, 0.5, 0.1, a>]
		    [1.0	rgbf <0.8, 0.5, 0.1, a>]
		}
    }

    finish	{ hull_finish ambient 1 }
   	normal	{ wrinkles 1 scale 0.3*sin( clock*2*3.14159 ) + 0.1 }
}
#end

union
{

#local a = 0.1;
#while (a <= 1.0)
	sphere
	{
		0, 0.2*a
		glow_texture( 0.9 )
	}
	#local a = a+0.1;
#end

    scale 		20
    
    rotate		y*clock*3*360
}
