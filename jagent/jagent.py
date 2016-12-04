import sys
import os
import io
import subprocess
import threading
import multiprocessing
import atexit

def get_path():
  if len( sys.argv ) > 1:
    return " ".join(sys.argv[1:]);
  return ""

def any_of_words_in_line(words:list, line:str):
  for word in words:
    if str(line).find(word) > -1:
      return (word, True)
  return ("", False)

class Process:
  __process = None

  stdout = subprocess.PIPE
  stderr = subprocess.PIPE

  def __init__( self, cmd : str ):
    self.__process = subprocess.Popen( cmd, stdout = self.stdout, stderr = self.stderr )

  def stderr_lines( self ):
    for line in iter( self.__process.stderr.readline, '' ):
     yield line.decode(sys.stderr.encoding).strip()

  def stdout_lines( self ):
    for line in iter( self.__process.stdout.readline, '' ):
      yield line.decode(sys.stdout.encoding).strip()

  def stop( self ):
    self.__process.kill()

  def is_alive( self ):
    return self.__process.poll() is None

  def exit_code( self ):
    return self.__process.poll()


class Daemon:
  __is_alive  = False
  __process   = None
  __worker1   = None
  __worker2   = None
  __cmd       = ""
  __bad_words = []

  __respawn_lock = threading.Lock()
  __bool         = False

  def __init__( self, cmd:str, bad_words:list ):
    self.__cmd       = cmd
    self.__bad_words = bad_words
    self.spawn()
    atexit.register(lambda: print("USER STOP"))

  def spawn( self ):
    self.__process = Process( cmd )
    self.__worker1 = threading.Thread( target = lambda: self.forever(self.__process.stderr_lines(), self.on_stderr_line_read) )
    self.__worker2 = threading.Thread( target = lambda: self.forever(self.__process.stdout_lines(), self.on_stdout_line_read) )
    self.__is_alive = True
    self.__worker1.start()
    self.__worker2.start()

  def kill( self ):
    self.__is_alive = False
    self.__process.stop()

  def forever( self, range, callable ):
    while self.__is_alive:
      try:
        for e in range:
          if not self.__is_alive:
            break
          if not self.__process.is_alive() and self.__process.exit_code() is not 3221225786:
            self.__respawn_lock.acquire()
            if not self.__bool:
              self.__bool = True
              print( "PROCESS HAS STOPPED, RESTARTING ..." )
              self.respawn()
            self.__respawn_lock.release()
            break
          callable( e )
      except e:
        print( "something bad was happen: {}".format(sys.exc_info()[0]) )

  def on_stderr_line_read( self, line ):
    if len( line ):
      print( "stderr: {}".format(line) )

      (word, exist) = any_of_words_in_line( self.__bad_words, line )
      if exist:
        print( "BAD WORD FOUND: {} IN LINE: {}".format(word, line) )
        print( "RESTARTING ..." )
        self.respawn()
  
  def on_stdout_line_read( self, line ):
    if len( line ):
      print( "stdout: {}".format(line) )

  def respawn(self):
    print( "KILLING..." )
    self.kill()
    return Daemon( self.__cmd, self.__bad_words )

cmd = get_path()
bad_words = ["9", "12", "13"]


Daemon( cmd, bad_words )

