import socket
import sys
import dns.resolver
import re


state = {
  'HELO': False,
  'MAIL': False,
  'RCPT': False,
  'loop': True,
  'recipient': ""
}

#start a new file for this session and change the state of the HELO 
def HELO(args, socket, client_address, state):
    fileName = str(client_address[1]) + '.txt'
    if len(args) != 2:
      socket.send("501 Syntax: HELO hostname")
      return
    #check if helo has been sent before
    if state['HELO'] == False:
      with open(fileName, 'w') as the_file:
        the_file.write(" ".join(args) + "\n")
      state['HELO'] = True
      socket.send("250 "+ str(client_address[1]) + "OK \n")
    #if helo sent before reset all state and delete old file
    else:
      open(fileName, 'w').close()
      with open(fileName, 'a') as the_file:
        the_file.write(" ".join(args) + "\n")
      state['HELO'] = False
      state['MAIL'] = False
      state['RCPT'] = False
      print "the helo state is ", state['HELO']
      print "the mail state is ", state['MAIL']
      state['HELO'] = True
      socket.send("250 "+ str(client_address[1]) + " OK \n")

#start the mail transaction after checking the sessions has be inititalized
def MAIL(args, socket, client_address, state):
    fileName = str(client_address[1]) + '.txt'
    #first check that helo has been sent
    if state['HELO'] == False:
      socket.send("503 5.5.1 Error: send HELO/EHLO first \n")
    else:
      #make sure it's not a nested mail command
      if state['MAIL'] == False:
        #check if the arguments are provided
        if len(args) != 2:
          socket.send("501 5.5.4 Syntax: MAIL FROM:<address> \n")
          return
        checkSyntax = re.match("FROM:<\w+@\w+\.\w+>", args[1], re.IGNORECASE)
        if(checkSyntax):
          with open(fileName, 'a') as the_file:
            the_file.write(" ".join(args) + "\n")
          state['MAIL'] = True
          socket.send("250 2.1.0 Ok \n")
        else:
          socket.send("501 5.1.7 Bad sender address syntax \n")
      else:
        socket.send("503 5.5.1 Error: nested MAIL command \n")
    
def RCPT(args, socket, client_address, state):
  #check if a mail transaction has begon and helo is initiatied
  if state['MAIL'] == True and state['HELO'] == True:
    if len(args) != 2:
      socket.send("501 5.5.4 Syntax: RCPT TO:<address>")
      return
    #check the format of the email is valid
    checkSyntax = re.match("TO:<\w+@\w+\.\w+>", args[1], re.IGNORECASE)
    if(checkSyntax):
      state['recipient'] = checkSyntax.group()
      fileName = str(client_address[1]) + '.txt'
      print >>sys.stderr, "got Mail command", args
      with open(fileName, 'a') as the_file:
        the_file.write(" ".join(args) + "\n")
      state['RCPT'] = True
      socket.send("250 2.1.5 Ok \n")
    else:
      socket.send("501 5.1.3 Bad recipient address syntax \n")
  else:
    socket.send("503 5.5.1 Error: need MAIL command \n")

def DATA(args, socket, client_address, state):
  fileName = str(client_address[1]) + '.txt'
  if state['MAIL'] == True and state['HELO'] == True and state['RCPT'] == True:
    socket.send("354 End data with <CR><LF>.<CR><LF> \n")
    data = recieveData(socket)
    with open(fileName, 'a') as the_file:
      the_file.write("data \n")
      the_file.write(data + "\n")
    state['MAIL'] = False
    state['RCPT'] = False
    relayData(client_address)
  elif state['MAIL'] == True and state['RCPT'] == False:
    socket.send("554 5.5.1 Error: no valid recipients \n")
  else:
    socket.send("503 5.5.1 Error: need RCPT command \n")

def QUIT(args, socket, client_address, stat):
  state['loop'] = False



def relayData(client_address):
  filename = str(client_address[1]) + '.txt'
  # The remote host
  domain = re.search("@[\w.]+", state['recipient'])
  domain = domain.group()
  domain = domain[1:]
  mailExchangeServers = dns.resolver.query(domain, 'MX')
  lowestPref = ""
  pref = mailExchangeServers[0].preference
  for rdata in mailExchangeServers:
    if rdata.preference <= pref:
      lowestPref = rdata.exchange.__str__()
  lowestPref = lowestPref[:-1]
  print lowestPref
  HOST = lowestPref
  PORT = 25              # email port
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((HOST, PORT))
  data = s.recv(1024)
  print('Received', repr(data))
  with open(filename) as fp:
    for line in fp:
      print('sent', repr(line))
      s.sendall(line)
      if line == ".\\n":
        data = s.recv(1024)
        print('Received', repr(data))
  data = s.recv(1024)
  print('Received', repr(data))

#state['recipient'] = "TO:<alexander.t.said@gmail.com>"

#relayData((1, 1234))

def recieveData(socket):
    fragments = []
    while True: 
      line = linesplit(socket)
      fragments.append(line)
      if line == ".\r":
        print "got here"
        return "".join(fragments)
      
    

dispatch = {
    'helo': HELO,
    'mail': MAIL,
    'rcpt': RCPT,
    'data': DATA,
    'quit':QUIT
}
def process_network_command(command, args, socket, client_address):
  command = command.lower()
  try:
    dispatch[command](args, socket, client_address, state)
  except KeyError:
    socket.send("502 5.5.2 Error: command not recognized \n")

def linesplit(socket):
    #add timeout to the connection if no commands are recieved
    socket.settimeout(300)
    buffer = socket.recv(4096)
    #remove timeout if commands are recieved
    socket.settimeout(None)
    buffering = True
    while buffering:
        if "\n" in buffer:
            (line, buffer) = buffer.split("\n", 1)
            return line
        else:
            more = socket.recv(4096)
            if not more:
                buffering = False
            else:
                buffer += more

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#prevent address is already in use error
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Bind the socket to the port
server_address = ('localhost', 50)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
# Listen for incoming connections
sock.listen(10)

while state['loop']:
    # Wait for a connection
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    
    try:
        connection.send("220 SMTP Nour 1.0 \n")
        print >>sys.stderr, 'connection from', client_address
        # Receive the data in small chunks 
        while state['loop']:
            lines = linesplit(connection)
            args = lines.split()
            print >>sys.stderr, 'the data is ', lines.split()
            process_network_command(args[0], args, connection, client_address)
    finally:
        # Clean up the connection
        connection.close()


''' helo nours.com
MAIL FROM:<nsaffour@gmail.com>
RCPT TO:<nsaffour@gmail.com>
DATA
FROM: nsaffour@gmail.com
SUBJECT: testing my smtp server

let's try this out
. '''