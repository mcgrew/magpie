#!/usr/bin/env python2

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
import os


def main( ):

	PASSED = cbTest( ) 

	PASSED = DBTest( ) and PASSED	

	# print( the overall results )
	print
	if PASSED:
		print( "All tests were passed" )
	else:
		print( "One or more tests did not succeed." )
	

def testGenerator( testLen=512 ):
	returnvalue = True
	testGen = PasswordDB.generate( testLen )
	if ( len( testGen ) == testLen ):
		success = "passed"
	else:
		success = "failed"
		returnvalue = false
	print( "Generated password of length %4d (%s) - %s" % ( testLen, success, testGen ))
	return returnvalue


def cbTest( ):
	# Test the Clipboard class
	cbTypes = ( 'tk', 'xsel', 'xclip' )
	cbPassed = False
	for cbType in cbTypes:
		print
		try:
			testCB = Clipboard( cbType )
			testString = 'I want a shrubbery!' 
			print( "Test string = " + testString )
			testCB.write( testString )
			testCB.close( )
			testCB = Clipboard( cbType )
			if testCB.read( ) == testString:
				print( "Clipboard('%s') copy test passed" % cbType )
				passed = True 
			else:
				print( "Clipboard('%s') copy test failed" % cbType )
				passed = False
			testCB.close( )
			testCB = Clipboard( cbType )
			testCB.clear( )
			if len( testCB.read( )):
				print( "Clipboard('%s') clearing test failed" % cbType )
				passed = False
			else:
				print( "Clipboard('%s') clearing test passed" % cbType )
				passed = True and passed
	
		except Exception as e:
			passed = False
			print( "Clipboard('%s') tests raised an Exception:" % cbType )
			print( str( e ))

		cbPassed = passed or cbPassed
		
	print
	if cbPassed:
		print( "Clipboard usability test passed" )
	else:
		print( "Clipboard usability test failed" )
	return cbPassed

def DBTest( ):
	returnValue = True

	print
	print( "################# PasswordDB Class tests: #####################" )
	
	print
	testDB = '/tmp/passwd'
	testPass = 'bork'
	if os.path.exists( testDB ):
		os.remove( testDB )
	pdb = PasswordDB( testDB, testPass )
	testString = "What a lovely bunch of coconuts!"
	encodedString = pdb.encode( testString )
	decodedString = pdb.decode( encodedString )

	print( "testString    = " + testString )
	print( "encodedString = " + b64encode( encodedString ))
	print( "decodedString = " + decodedString )
	if ( decodedString == testString ):
		print( "Encode/Decode test passed" )
	else:
		returnValue = false
		print( "Encode/Decode test failed" )
	print

	for i in xrange( 32 ):
		returnValue = testGenerator( randint( 1, 128 )) and returnValue

	print
	inputData = "Username\t  Password\t\tDescription\n" + \
				"user1\tbork_bork\t www.bork.com is borked\n" + \
				"user2\t\t \tblah_blah\twww.blah.com\tlogin\n" + \
				"user3  \twoof_woof \tThe biggest of the big dogs" 
	testData = "Username\tPassword\tDescription\n" + \
				"user1\tbork_bork\twww.bork.com is borked\n" + \
				"user2\tblah_blah\twww.blah.com\tlogin\n" + \
				"user3\twoof_woof\tThe biggest of the big dogs" 
	testData = testData.strip( )
	pdb.load( inputData )

	print( "Test data:" )
	print( inputData )

	print
	if pdb.dump( ) == testData:
		print( "Import/Export test passed" )
	else:
		print( "Import/Export test failed" )
		print( "New Data was:" )
		print( pdb.dump( ))
		returnValue = False
	
	print
	pdb.close( )
	pdb = PasswordDB( testDB, testPass )
	if pdb.dump( ) == testData:
		print( "Save/Read test passed" )
	else:
		print( "Save/Read test failed" )
		print( "New Data was:" )
		print( pdb.dump( ))
		returnValue = False

	print
	if pdb.find( "biggest", "dogs" ) ==  "user3\twoof_woof\tThe biggest of the big dogs":
		print( "Find test passed" )
	else:
		print( "Find test failed looking for ('biggest', 'dogs')" )
		print( "Find returned: " + pdb.find( "biggest", "dogs" ))
		print( "Instead of   : user3\twoof_woof\tThe biggest of the big dogs" )
		returnValue = False
	
	print
	if PasswordDB.mask( pdb.find( "bork" )) == "user1\t(9)\twww.bork.com is borked":
		print( "Mask Test passed" )
	else:
		print( "Mask Test failed" )
		print( "Mask returned: "+PasswordDB.mask( pdb.find( "bork" )))
		print( "Instead of   : user1\t*********\twww.bork.com is borked" )
		returnValue = False
	
	print
	pdb.add( "user4", "jomo_baru!  ", "\tThe leader of the pack" )
	if pdb.dump( ) == testData+"\nuser4\tjomo_baru!\tThe leader of the pack":
		print( "Add test passed" )
		print( "New Data was:" )
		print( pdb.dump( ))
	else:
		print( "Add test failed" )
		print( "New Data was:" )
		print( pdb.dump( ))
		returnValue = False

	print
	removeTest = pdb.remove( "leader" )
	if removeTest == "user4\tjomo_baru!\tThe leader of the pack" and pdb.dump( ) == testData:
		print( "Remove test passed" )
		print( "New Data was:" )
		print( pdb.dump( ))
	else:
		print( "Remove test failed looking for 'leader'" )
		print( "Remove returned: "+removeTest )
		print( "New Data was:" )
		print( pdb.dump( ))
		returnValue = False

	return returnValue
	
if __name__ == "__main__":
		main( )

