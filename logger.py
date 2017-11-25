import os
import datetime




def createLog(name):

  # Create folder 'log' if it doesn't exist to contain log files
  if not os.path.exists('./log'):
    os.mkdir('log')

  # Get the time and date that script to appropriately name the log
  time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d_%H:%M:%S')
  
  # Name the log file
  name = name + '_' + time + '.txt'

  # Create new log file
  open('log/' + name, 'a')

  # Set log file as global variable so it can be written to by other functions
  global logFile
  logFile = 'log/' + name



def console(string):
  """Prints a string to the console and the log"""
  print (string)
  log(string)



def log(string):
  """Prints a string to the log"""
  log = open(logFile, "a")
  log.writelines(string + '\n')
  log.close()



def main():
  return
 
  
      
# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
  main()
