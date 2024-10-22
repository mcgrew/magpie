#!/usr/bin/env python3

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

from Crypto.Cipher import AES
from hashlib import sha256
from base64 import b64encode,b64decode
from tempfile import mkstemp
import os
import sys
import shutil
from optparse import OptionParser
from getpass import getpass
from shutil import which
import subprocess
import zlib
import re
import string
from typing import List, Union, Tuple

#    To Do:
#        add an --edit option
#        add the ability to --force certain types of characters
#        add an --append option as an alternative to --import (maybe --merge?)
#        add an --update option to update a password for an entry
#        change -u option to be username entry, change -a true/false, ask for
#            username if not specified
#        change to prompt for description if not specified.
#        confirm password when importing a database


B64_SYMBOLS = b'._'
SETS = {
    "alnum": b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "alpha": b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "digit": b"0123456789",
    "lower": b"abcdefghijklmnopqrstuvwxyz",
    "upper": b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}
HASH_ITERATIONS = 4096

def parseOpts():
    parser = OptionParser(version="%prog 0.3",
        usage="%prog [options] [description|keywords]")
    parser.add_option("-a", "--add", dest="username",
        help="Add a password to the stored passwords with the specified "
        "username.")
    parser.add_option("-f", "--file", dest="file",
        default=os.path.expanduser(os.path.join('~', ".config", "magpie",
            "database")),
        help="Use FILE instead of %default for storing/retrieving passwords.")
    parser.add_option("-g", "--generate", dest="generate", metavar="LENGTH",
        default=0, type="int",
        help="Generate a random password of the specified length instead of " +
        "prompting for one.")
    parser.add_option("-r", "--remove", action="store_true", dest="remove",
        help="Remove specific password(s) from the database.")
#    parser.add_option("-u", "--user", action="store_true", dest="get_user",
#        help="Retrieve the username instead of the password for the account."),
    parser.add_option("--debug", action="store_true",
        help="Print debugging messages to stderr.")
    parser.add_option("--list", action="store_true", dest="print_all",
        help="Print entire database to standard output with the passwords "
        "masked.")
    parser.add_option("--change-password", action="store_true", dest="change",
        help="Change the master password for the database.")
    parser.add_option("--find", action="store_true", dest="find",
        help="Find an entry in the database and print its value with the "
        "password masked.")
    parser.add_option("-e", "--edit", action="store_true", dest="edit",
        help="Edit the file in the default system text editor and import the " +
        "result as the new database.")
    parser.add_option("-o", "--export", dest="exportFile", metavar="FILE",
        help="Export the password database to a delimited text file. Keep this "
        "file secure, as it will contain all of your passwords in plain text. "
        "Specify - as the filename to print to stdout.")
    parser.add_option("-i", "--import", dest="importFile", metavar="FILE",
        help="Import a password database from a delimited text file. This will "
        "overwrite any passwords in your current database. Specify - as the "
        "filename to read from stdin.")
    parser.add_option("-s", "--salt", dest="saltfile", metavar="FILE",
        default=os.path.expanduser(os.path.join('~', ".config", "magpie",
            "salt")), help="Use FILE instead of %default for password salt.")
    parser.add_option("--tr", "--sub", dest="translate", metavar="SUBS",
        action="append",
        help="Takes an argument in the form chars:chars and translates " +
        "characters in generated passwords, replacing characters before the : "
        "with the corresponding character after the :.")
    parser.add_option("-p", "--print", action="store_true", dest="print_",
        help="Print the password to standard output instead of copying it to "
        "the clipboard.")

    return parser.parse_args()


def main(options, args):
    if not options.print_:
        clipboard = Clipboard()

    if options.generate and not options.username:
        newPass = translate(PasswordDB.generate(options.generate),
            options.translate)
        if options.print_:
            sys.stdout.write(newPass)
        else:
            clipboard.write(newPass)
        sys.exit()
    # prompt for password
    password = getpass("Master Password: ")

    #Remove the old file if it exist and we are importing new data.
#     if options.importFile and os.path.exists(options.file):
#         os.remove(options.file)

    try:
        pdb = PasswordDB(options.file, password, options.saltfile)
    except ValueError as e:
        sys.stderr.write(str(e) + '\n')
        sys.exit(-1)

    if options.change:
        newPass             = getpass("Enter new master password: ")
        newPassVerify = getpass("Re-enter password: ")
        while not(newPass == newPassVerify):
            print("\nPasswords do not match. please try again")
            newPass             = getpass("Enter new master password: ")
            newPassVerify = getpass("Re-enter password: ")
        pdb.password = newPass
        print("Master Password Changed")
        pdb.flush()
        sys.exit()

    if options.print_all:
        lines = pdb.dump().split('\n')
        try:
            termwidth = os.get_terminal_size().colums
        except:
            termwidth = 100
        format_ = f"%{min(int(termwidth // 2.5), 30)}s %8s %s"
        print(format_ % PasswordDB.splitLine(lines[0]))
        for line in lines[1:]:
            print(format_ % PasswordDB.splitLine(PasswordDB.mask(line)))
        sys.exit()

    if options.edit:
        fd, filename = mkstemp(text=True)
        os.write(fd, pdb.dump().encode('UTF-8'))
        os.close(fd)
        editors = (os.getenv('EDITOR', 'vim'), 'vim', 'nano', 'notepad.exe', 'emacs')
        for editor in editors:
            if which(editor):
                subprocess.run([editor, filename])
                try:
                    with open(filename, 'r') as f:
                        pdb.load(f.read())
                    pdb.flush()
                except ValueError as e:
                    sys.stderr.write(str(e))
                finally:
                    os.remove(filename)
                sys.exit()
        sys.stderr.write('Unable to find an appropriate editor.')
        sys.exit()

    if options.exportFile:
        if options.exportFile == '-':
            sys.stdout.write(pdb.dump())
        else:
            with open(options.exportFile, 'wb') as exportFile:
                exportFile.write(pdb.dump().encode('utf-8'))
        sys.exit()

    if options.importFile:
        if options.importFile == '-':
            pdb.load(sys.stdin.read())
        else:
            with open(options.importFile, 'rb') as importFile:
                pdb.load(importFile.read().decode('utf-8'))
        pdb.flush()
        sys.exit()

    if options.remove:
        removed = pdb.remove(*args)
        if removed:
            sys.stderr.write("Removed the following entry:\n%s\n" % removed)
        else:
            sys.stderr.write("Unable to locate the specified entry\n")
        pdb.flush()

    if options.username:
        if options.generate:
            newPass = translate(PasswordDB.generate(options.generate),
                options.translate)
            if options.print_:
                sys.stdout.write("Password: "+ newPass)
            else:
                clipboard.write(newPass)
        else:
            newPass = getpass("Enter password for new account: ")
            newPassVerify = getpass("Re-enter password: ")
            while not(newPass == newPassVerify):
                print("\nPasswords do not match. please try again")
                newPass = getpass("Enter password for new account: ")
                newPassVerify = getpass("Re-enter password: ")
        pdb.add(options.username, newPass, ' '.join(args))
        if options.generate:
            sys.stderr.write("Generated password saved\n")
        pdb.flush()

    # The exit is here to allow a person to add and remove at the same time.
    # In other words, replace an entry.
    if options.remove:
        sys.exit()

    found = pdb.find(*args)
    if not found:
        print("Unable to locate entry")
        return;

    if options.find:
        found = pdb.find(*args)
        if found:
            print("%20s %8s %s" % PasswordDB.splitLine(pdb.data.split('\n')[0]))
            print("%20s %8s %s" % PasswordDB.splitLine(PasswordDB.mask(found)))
            sys.exit()
        else:
            print("Unable to locate entry for search terms '%s'" %
                ' '.join(args))
            sys.exit(1)

    else:
        entry = found.split('\t', 2)

        if options.print_:
            sys.stdout.write(entry[1])
            sys.stdout.flush()
            sys.stderr.write("\n\n%s\n" % entry[2])
            sys.stderr.write("Username: %s\n\n" % entry[0])
        else:
            clipboard.write(entry[1])
            print("")
            print(entry[2])
            print("Username: %s" % entry[0])


    pdb.close()

def translate(st, replacements):
    if not replacements:
        return st
    for repl in replacements:
        if '~' in repl:
            for i in SETS.keys():
                repl = repl.replace('~%s'%i, SETS[i])
        _from_, to    = repl.split(':', 1)
        if len(_from_) > len(to):
            to += to[-1] * (len(_from_) - len(to))
        st = st.translate(string.maketrans(_from_, to[:len(_from_)]))
    return st

class PasswordDB(object):
    def __init__(self, filename, password, saltfile):
        self.filename = filename
        self.password = password
        self.saltfile = saltfile
        self.salt = self.getSalt() if saltfile and os.path.exists(saltfile) \
            else None
        try:
            self.open()
#             if not (self.data[:29] == "Username\tPassword\tDescription"):
#                 raise ValueError
        except (zlib.error,ValueError):
            raise ValueError("You entered an incorrect password")

    def flush(self) -> None:
        if os.path.exists(self.filename):
            shutil.copyfile(self.filename, self.filename+'~')
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename), 0o755)
        with open(self.filename, 'wb', 0o600) as passFile:
            passFile.write(b64encode(self.encrypt(zlib.compress(
                self.data.encode('utf-8')[::-1], 9))))

    def close(self) -> None:
        self.flush()

    def open(self) -> bool:
        if not (os.path.exists(self.filename)):
            self.data = "Username\tPassword\tDescription\n"
            return False
        with open(self.filename, 'rb') as passFile:
            self.data =    zlib.decompress(self.decrypt(
                b64decode(passFile.read())))[::-1].decode('utf-8')
        return True

    def dump(self) -> str:
        return self.data

    def load(self, data:str) -> None:
        data = data.strip().split("\n")
        self.data = ""
        for i in data:
            line = PasswordDB.splitLine(i.strip())
            if len(line) < 3:
                raise ValueError(f"Not enough arguments, aborting: {line}")
            self.data += '\t'.join(PasswordDB.splitLine(i.strip())) + '\n'
        self.data = self.data.strip()

    def add(self, username:str, password:str, description:str):
        if not self.data[-1] == '\n':
            self.data += '\n'
        self.data += '\t'.join((username.strip(), password.strip(),
            description.strip()))

    def find(self, *keywords:List[str]) -> str:
        lines = self.data.split('\n')
        for i in range(1, len(lines)):
            correctLine = True
            for j in range(len(keywords)):
                correctLine = correctLine and (keywords[j].lower() in lines[i].lower())
            if correctLine:
                return lines[i]
        return ''

    def remove(self, *keywords:List[str]) -> str:
        found = self.find(*keywords)
        if not found:
            return ''
        lines = self.data.split('\n')
        returnvalue =    lines.pop(lines.index(found))
        self.data = '\n'.join(lines)
        return returnvalue

    @staticmethod
    def mask(dbentry:str) -> str:
        lines = dbentry.split('\n')
        for i in range(len(lines)):
            newLine = lines[i].split('\t', 2)
            newLine[1] = '(%d)' % len(newLine[1])
            lines[i] = '\t'.join(newLine)
        return '\n'.join(lines)

    def encrypt(self, text:bytes) -> bytes:
        if not self.salt and not os.path.exists(self.saltfile):
            self.salt = PasswordDB.generateSalt(256, self.saltfile);
        key = sha256(self.password.encode("utf-8")).digest() + self.salt
        for i in range(HASH_ITERATIONS):
            key = sha256(key).digest()
        return AES.new(key, AES.MODE_CFB, key[:16]).encrypt(text)

    def decrypt(self, text:bytes) -> bytes:
        key = sha256(self.password.encode("utf-8")).digest()
        if (self.salt):
            key = key + self.salt
            for i in range(HASH_ITERATIONS):
                key = sha256(key).digest()
        try:
            return AES.new(key, AES.MODE_CFB, key[:16]).decrypt(text)
        except UnicodeDecodeError: # invalid password
            return ''

    @staticmethod
    def generate(length):
        # get a random string containing base64 encoded data, replacing /+ with
        # B64_SYMBOLS
        return b64encode(os.urandom(length), B64_SYMBOLS)[:length] \
                .decode('utf-8')

    @staticmethod
    def generateSalt(length, filename=None) -> bytes:
        returnvalue = os.urandom(length)
        if (filename):
            with open(filename, 'wb') as saltfile:
                saltfile.write(returnvalue)
        return returnvalue

    def getSalt(self) -> bytes:
        with open(self.saltfile, 'rb') as saltreader:
            returnvalue = saltreader.read()
        return returnvalue

    @staticmethod
    def splitLine(line:str) -> Tuple[str]:
        return tuple(re.split("(\s*\t\s*)+", line, 2)[::2])
#         return line.replace('\t', '  ').split(None, 2)[::2]

class Clipboard(object):
    backend = False
    def __init__(self, backend=None):
        object.__init__(self)
        if backend:
            self.backend = backend
        else:
            if bool(which('clip.exe')):
                self.backend = 'clip.exe'
            elif bool(which('xsel')):
                self.backend = 'xsel'
            elif bool(which('xclip')):
                self.backend = 'xclip'
            elif bool(which('pbcopy')):
                self.backend = 'pbcopy'
            elif bool(which('termux-clipboard-set')):
                self.backend = 'termux-clipboard'

        if not self.backend:
            sys.stderr.write("Unable to properly initialize clipboard - " +
                "no supported backends exist\n")

            # to do: check for Tk, Wx, Win32, etc.

    def read(self):
        """
        Returns the contents of the clipboard
        """
        if self.backend == 'pbcopy': # MacOS
            proc = subprocess.Popen(['pbpaste', '-Prefer', 'txt'],
                stdout=subprocess.PIPE)
        if self.backend == 'xsel': # Linux
            proc = subprocess.Popen(['xsel', '-o'], stdout=subprocess.PIPE)
        if self.backend == 'xclip': # Linux
            proc = subprocess.Popen(['xclip', '-o'], stdout=subprocess.PIPE)
        if self.backend == 'termux-clipboard': # Termux
            proc = subprocess.Popen(['termux-clipboard-get'], stdout=subprocess.PIPE)
        if self.backend == 'clip.exe': # Windows/WSL
            raise ValueError("Clipboard reading not supported with the clip.exe"
                    " backend")

        returnvalue = proc.stdout.read().decode('utf-8')
        proc.stdout.close()
        proc.wait()
        return returnvalue


    def write(self, text:str) -> None:
        """
        Copies text to the system clipboard
        """
        if self.backend == 'xsel': #Linux
            # copy to both XA_PRIMARY and XA_CLIPBOARD
            proc = subprocess.Popen(['xsel', '-p', '-i'], stdin=subprocess.PIPE)
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            proc.wait()
            proc = subprocess.Popen(['xsel', '-b', '-i'], stdin=subprocess.PIPE)
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            proc.wait()
            return
        if self.backend == 'xclip': #Linux
            # copy to both XA_PRIMARY and XA_CLIPBOARD
            proc = subprocess.Popen(['xclip', '-selection', 'primary', '-i'],
                    stdin=subprocess.PIPE)
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            proc.wait()
            proc = subprocess.Popen(['xclip', '-selection', 'clipboard', '-i'],
                    stdin=subprocess.PIPE)
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            proc.wait()
            return
        if self.backend == 'termux-clipboard': #Termux
            proc = subprocess.Popen(['termux-clipboard-set'], stdin=subprocess.PIPE)
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            proc.wait()
            return
        if self.backend == 'clip.exe': #Windows/WSL
            # copy to both XA_PRIMARY and XA_CLIPBOARD
            proc = subprocess.Popen(['clip.exe'], stdin=subprocess.PIPE)
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            proc.wait()
            return
        if self.backend == 'pbcopy': # MacOS
            proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            proc.wait()
            return

    def clear(self) -> None:
        """
        Clear the clipboard contents
        """
        if self.backend == 'xsel':
            subprocess.call(['xsel', '-pc'])
            subprocess.call(['xsel', '-bc'])
            return
        if self.backend == 'xclip':
            proc = subprocess.Popen(['xclip', '-i', '-selection', 'primary'],
                        stdin=subprocess.PIPE)
            proc.stdin.write(b'')
            proc.stdin.close()
            proc.wait()
            proc = subprocess.Popen(['xclip', '-i', '-selection', 'clipboard'],
                        stdin=subprocess.PIPE)
            proc.stdin.write(b'')
            proc.stdin.close()
            proc.wait()

        if self.backend == 'clip.exe':
            proc = subprocess.Popen(['clip.exe'],
                        stdin=subprocess.PIPE)
            proc.stdin.write(b'')
            proc.stdin.close()
            proc.wait()

        if self.backend == 'termux-clipboard':
            proc = subprocess.Popen(['termux-clipboard-set'], stdin=subprocess.PIPE)
            proc.stdin.write(b'')
            proc.stdin.close()
            proc.wait()

        if self.backend == 'pbcopy':
            proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            proc.stdin.write(b'')
            proc.stdin.close()
            proc.wait()


    def close(self) -> None:
        pass

if __name__ == "__main__":
    main(*parseOpts())

