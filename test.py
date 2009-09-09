#!/usr/bin/env python

# Test script for passkeeper

#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	 This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

from passkeeper import *
from base64 import b64encode
from random import randint

def main( ):

	testString = "What a lovely bunch of coconuts!"
	encodedString = encode( testString, 'password' )
	decodedString = decode( encodedString, 'password' )

	print "encodedString = " + b64encode( encodedString )
	print "decodedString = " + decodedString
	if ( decodedString == testString ):
		print "Encode/Decode test successful"
	else:
		print "Encode/Decode test failed"
	print

	testGenerator( 8 )
	testGenerator( 16 )
	testGenerator( 47 )
	testGenerator( 64 )
	testGenerator( 128 )
	testGenerator( 256 )
	testGenerator( 512 )
	testGenerator( 1024 )
	
	for i in xrange( 32 ):
		testGenerator( randint( 1, 128 ))


def testGenerator( testLen=512 ):
	testGen = generate( testLen )
	if ( len( testGen ) == testLen ):
		success = "successful"
	else:
		success = "failed"
	print "Generated password of length %4d (%s) - %s" % ( testLen, success, testGen )


if __name__ == "__main__":
		main( )

