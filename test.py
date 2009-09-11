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

from magpie import *
from base64 import b64encode
from random import randint

PASSED = True

def main( ):
	global PASSED 
	testString = "What a lovely bunch of coconuts!"
	encodedString = encode( testString, 'password' )
	decodedString = decode( encodedString, 'password' )

	print "testString    = " + testString
	print "encodedString = " + b64encode( encodedString )
	print "decodedString = " + decodedString
	if ( decodedString == testString ):
		print "Encode/Decode test successful"
	else:
		failure( )
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

	PASSED = PASSED and cbTest( )
	

	# print the overall results
	print
	if PASSED:
		print "All tests were successful"
	else:
		print "One or more tests did not succeed."
	

def testGenerator( testLen=512 ):
	testGen = generate( testLen )
	if ( len( testGen ) == testLen ):
		success = "successful"
	else:
		failure( )
		success = "failed"
	print "Generated password of length %4d (%s) - %s" % ( testLen, success, testGen )

def failure( ):
	global PASSED
	PASSED = False

def cbTest( ):
	# Test the Clipboard class
	print
	try:
		testCB = Clipboard('xsel')
		testString = 'I want a shrubbery!' 
		print "Test string = " + testString
		testCB.write( testString )
		if testCB.read( ) == testString:
			print "Clipboard (xsel) copy test successful"
			passed = True 
		else:
			print "Clipboard (xsel) copy test failed"
			passed = False
		testCB.clear( )
		if len( testCB.read( ) ):
			print "Clipboard (xsel) clearing test failed"
			passed = False
		else:
			print "Clipboard (xsel) clearing test successful"
			passed = True and passed

	except Exception, e:
		passed = False
		print "Clipboard (xsel) tests raised an Exception:"
		print e.message
	
	cbPassed = passed
		
	print
	try:
		testCB = Clipboard( 'xclip' )
		testString = 'I want a shrubbery!' 
		print "Test string = " + testString
		testCB.write( testString )
		if testCB.read( ) == testString:
			print "Clipboard (xclip) copy test successful"
			passed = True
		else:
			print "Clipboard (xclip) copy test failed"
			passed = False
		testCB.clear( )
		if len( testCB.read( ) ):
			print "Clipboard (xclip) clearing test failed"
			passed = True and passed
		else:
			print "Clipboard (xclip) clearing test successful"
			passed = False

	except Exception, e:
		passed = False
		print "Clipboard (xclip) test raised an Exception:"
		print e.message
	
	print
	cbPassed = passed or cbPassed
	if cbPassed:
		print "Clipboard usability test successful"
	else:
		print "Clipboard usability test failed"
	return cbPassed

if __name__ == "__main__":
		main( )

