import socket
import sys
import dns.resolver


def HELO(args, socket, client_address):
    print "got HELO", args
    with open('somefile.txt', 'a') as the_file:
      the_file.write(" ".join(args))

def MAIL(args, socket, client_address):
    print >>sys.stderr, "got Mail command", args

dispatch = {
    'helo': HELO,
    'mail': MAIL,
}

def process_network_command(command, args, socket, client_address):
  command = command.lower()
  try:
    dispatch[command](args, socket, client_address)
  except KeyError:
    socket.send("502 5.5.2 Error: command not recognized")

def linesplit(socket):
    buffer = socket.recv(4096)
    buffering = True
    while buffering:
        if "\n" in buffer:
            (line, buffer) = buffer.split("\n", 1)
            return line + "\n"
        else:
            more = socket.recv(4096)
            if not more:
                buffering = False
            else:
                buffer += more

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 25)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
# Listen for incoming connections
sock.listen(10)

while True:
    # Wait for a connection
    print >>sys.stderr, 'waiting for a connection'
    

    answers = dns.resolver.query('gmail.com', 'MX')
    for rdata in answers:
      print 'Host', rdata.exchange, 'has preference', rdata.preference
        #print socket.getaddrinfo('gmail.com', 25)
    connection, client_address = sock.accept()
    connection.send("220 SMTP Nour 1.0 \n")

    try:
        print >>sys.stderr, 'connection from', client_address

        # Receive the data in small chunks and retransmit it
        while True:
            lines = linesplit(connection)
            args = lines.split()
            print >>sys.stderr, 'the data is ', lines.split()
            process_network_command(args[0], args, connection, client_address)
            
    finally:
        # Clean up the connection
        connection.close()


''' helo nours.com
MAIL FROM:<Yannregev@gmail.com>
RCPT TO:<ilmari.kaskia@gmail.com>
DATA
FROM: Yannregev@gmail.com
SUBJECT: Don't come to school tomorrow

I don't want you to come tomorrow.
. '''