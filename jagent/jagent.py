import sys
import os
import io
import subprocess
import threading

def get_path():
  if len( sys.argv ) > 1:
    return " ".join(sys.argv[1:]);
  return ""

cmd = get_path()

class Process:
  __process = None
  __cmd     = None

  stdout = subprocess.PIPE
  stderr = subprocess.PIPE

  def __init__(self, cmd : str):
    self.__process = subprocess.Popen( cmd, stdout = self.stdout, stderr = self.stderr )
    self.__cmd     = cmd

  def stderr_lines(self):
    for line in iter( self.__process.stderr.readline, '' ):
      yield line.decode(sys.stderr.encoding).strip()

  def stdout_lines(self):
    for line in iter( self.__process.stdout.readline, '' ):
      yield line.decode(sys.stdout.encoding).strip()

  def stop(self):
    self.__process.kill()


class Daemon:
  __is_alive = False
  __process  = None
  __worker1  = None
  __worker2  = None
  
  def __init__( self, cmd:str ):
    self.__process = Process( cmd )

  def spawn( self ):
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
          callable( e )
      except:
        print( "something bad was happen" )

  def on_stderr_line_read( self, line ):
    print( "stderr: {}".format(line) )
    if '7' in line:
      print( "KILLING..." )
      self.kill()

  def on_stdout_line_read( self, line ):
    print( "stdout: {}".format(line) )

daemon = Daemon( cmd )
daemon.spawn()
