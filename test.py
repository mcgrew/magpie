#!/usr/bin/env python

# Test script for passkeeper

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#     This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.    If not, see <http://www.gnu.org/licenses/>.

from magpie import *
from base64 import b64encode
from random import randint
from distutils.spawn import find_executable
import unittest
import os


def main():

    PASSED = cbTest() 

    PASSED = DBTest() and PASSED    

    # print(the overall results)
    print
    if PASSED:
        print("All tests were passed")
    else:
        print("One or more tests did not succeed.")
    

def testGenerator(testLen=512):
    returnvalue = True
    testGen = PasswordDB.generate(testLen)
    if (len(testGen) == testLen):
        success = "passed"
    else:
        success = "failed"
        returnvalue = false
    print("Generated password of length %4d (%s) - %s" %
            (testLen, success, testGen))
    return returnvalue

class CBTest(unittest.TestCase):
    def setUp(self):
        # Test the Clipboard class
        self.testString = 'I want a shrubbery!' 

    @unittest.skipIf(not find_executable('xsel'), "Skipping xsel test")
    def test_xsel(self):
        cbType = 'xsel'
        testCB = Clipboard(cbType)
        testCB.write(self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        self.assertEqual(testCB.read(), self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        testCB.clear()
        self.assertFalse(len(testCB.read()))

    @unittest.skipIf(not find_executable('xclip'),"Skipping xclip test")
    def test_xclip(self):
        cbType = 'xclip'
        testCB = Clipboard(cbType)
        testCB.write(self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        self.assertEqual(testCB.read(), self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        testCB.clear()
        self.assertFalse(len(testCB.read()))

    # we can't test reading here, because clip.exe doesn't support it
    @unittest.skipIf(not find_executable('clip.exe'), "Skipping clip.exe test")
    def test_clip_exe(self):
        cbType = 'clip.exe'
        testCB = Clipboard(cbType)
        testCB.write(self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        testCB.close()
        cbType = 'clip.exe'
        testCB = Clipboard(cbType)
        testCB.clear()

    @unittest.skipIf(not sys.platform.startswith("windows"), "Skipping tk test")
    def test_tk(self):
        cbType = 'tk'
        testCB.write(self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        self.assertEqual(testCB.read(), self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        testCB.clear()
        self.assertFalse(len(testCB.read()))

    @unittest.skipIf(not find_executable('pbcopy'), "Skipping MacOS test")
    def test_pbcopy(self):
        cbType = 'pbcopy'
        testCB = Clipboard(cbType)
        testCB.write(self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        self.assertEqual(testCB.read(), self.testString)
        testCB.close()
        testCB = Clipboard(cbType)
        testCB.clear()
        self.assertFalse(len(testCB.read()))


class StaticMethodTest(unittest.TestCase):
    def test_generate(self):
        for i in range(128):
            testLen = randint(1, 1024)
            self.assertEqual(testLen, len(PasswordDB.generate(testLen)))

    def test_mask(self):
        self.assertEqual(
            PasswordDB.mask("user1\tbork_bork\twww.bork.com is borked"), 
            "user1\t(9)\twww.bork.com is borked")

class DBTest(unittest.TestCase):
    def setUp(self):
        self.testDB = '/tmp/passwd'
        self.testPass = 'bork'
        self.testSalt = '1234567890'
        self.testSaltFile = '/tmp/magpie_test_salt'
        saltFile = open(self.testSaltFile, 'w')
        saltFile.write(self.testSalt)
        saltFile.close()
        if os.path.exists(self.testDB):
            os.remove(self.testDB)
        self.pdb = PasswordDB(self.testDB, self.testPass, self.testSaltFile)
        self.testString = "What a lovely bunch of coconuts!"
        self.inputData = "Username\t    Password\t\tDescription\n" + \
                    "user1\tbork_bork\t www.bork.com is borked\n" + \
                    "user2\t\t \tblah_blah\twww.blah.com\tlogin\n" + \
                    "user3    \twoof_woof \tThe biggest of the big dogs" 
        self.testData = "Username\tPassword\tDescription\n" + \
                    "user1\tbork_bork\twww.bork.com is borked\n" + \
                    "user2\tblah_blah\twww.blah.com\tlogin\n" + \
                    "user3\twoof_woof\tThe biggest of the big dogs" 
        self.pdb.load(self.inputData)

    def test_encode_decode(self):
        encodedString = self.pdb.encrypt(self.testString.encode('utf-8'))
        decodedString = self.pdb.decrypt(encodedString)
        self.assertEqual(decodedString, self.testString.encode('utf-8'))
        # make sure it doesn't work with a bad password
        bad_pdb = PasswordDB(self.testDB, "bad_password", self.testSaltFile)
        bad_decodedString = bad_pdb.decrypt(encodedString)
        self.assertNotEqual(bad_decodedString, self.testString.encode('utf-8'))

    def test_import_export(self):
        self.assertEqual(self.pdb.dump(), self.testData)

    def test_save_read(self):
        self.pdb.close()
        self.pdb = PasswordDB(self.testDB, self.testPass, self.testSaltFile)
        self.assertEqual(self.pdb.dump(), self.testData)

    def test_find(self):
        self.assertEqual(self.pdb.find("biggest", "dogs"),
                        "user3\twoof_woof\tThe biggest of the big dogs")

    def test_add(self):
        self.pdb.add("user4", "jomo_baru!    ", "\tThe leader of the pack")
        self.assertEqual(self.pdb.dump(),
                self.testData + "\nuser4\tjomo_baru!\tThe leader of the pack")

    def test_remove(self):
        self.pdb.add("user4", "jomo_baru!    ", "\tThe leader of the pack")
        removeTest = self.pdb.remove("leader")
        self.assertEqual(removeTest,"user4\tjomo_baru!\tThe leader of the pack")
        self.assertEqual(self.pdb.dump(), self.testData)

    def tearDown(self):
        os.remove(self.testSaltFile)
        if os.path.exists(self.testDB):
            os.remove(self.testDB)

if __name__ == "__main__":
        unittest.main()

