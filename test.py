#!/usr/bin/env python

from pwdkeeper import *
from base64 import b64encode

def main( ):

	testString = "What a lovely bunch of coconuts!"
	encodedString = encode( testString, 'password' )
	decodedString = decode( encodedString, 'password' )

	print "encodedString = " + b64encode( encodedString )
	print "decodedString = " + decodedString
	if ( decodedString == testString ):
		print "Test Successful"
	else:
		print "Test failed"

if __name__ == "__main__":
		main( )

