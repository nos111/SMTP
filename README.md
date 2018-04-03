<h1>SMTP</h1>
<h2>Simple Mail Transfer Protocol</h2>

<h3>Overview:</h3>
This is a python SMTP server, without using the python smtp library, confirming to the rfc 5321
SMTP servers are used to send emails.

<h3>How it works:</h3>
The server is started and the IP that it should listen on should be provided as a command line argument. The port is already decided which is 25. 
A client (ex. telnet) will establish a connection to the server
The server will reply with it’s version and code “220”
The client to send “HELO domain” to start a new session where mail transactions can take place.
The server will reply with: “250 clientPort OK”
The client need to send “MAIL FROM:<email>” to start an email transaction
The server will reply with: “250 2.1.0 Ok”
The client need to send rcpt command to indicate the recipient “RCPT TO:<email>”
The server will reply with “250 2.1.5 Ok“
The client should send the data command now to supply the email data.
The server will reply with “354 End data with <CR><LF>.<CR><LF>“
The server will keep on receiving data until a dot followed by an enter is received.
The server will start the forwarding procedure:
Start a new thread for forwarding the email.
Perform a DNS lookup to retrieve the mail exchange addresses from the recipient address domain.
Find the mail exchange addresses with the lowest latency.
Connect to the prefered address
Send the commands we received in the correct order.
Notes:
The server will not wait until the session end to start forwarding to the receiving end.
Since this server is not tied to a domain, it’s only job is to forward emails.
No postmaster email is needed because the server that we will forward to will send from a postmaster email any errors that occur.

<h3>Compile:</h3>
<code>sudo python smtp.py localhost</code>

<h3>How to test:</h3>
The following steps will send an email from “nsaffour@gmail.com” to “nsaffour@gmail.com” with the subject “testing my smtp server” and a message body of “Dear Nour, This is me testing my server”.
Open a terminal
Go to the directory where the SMTP.py file is located
sudo python SMTP.py localhost
Open another terminal
telnet localhost 25
Send the following lines:
helo me.com
MAIL FROM:<nsaffour@gmail.com>
RCPT TO:<nsaffour@gmail.com>
Data
SUBJECT:  testing my smtp server
FROM: nsaffour@gmail.com
Dear Nour, This is me testing my server
The server will reply with queued.
The email should be available with in a few seconds in the spam.
However if you do the test with a vu email, the email will arrive to the inbox
We have tested the server with thunderbird mail client on ubuntu and the messages were sent properly to the inbox of the receiver.
Commands:
As specified by the rfc5321 section 4.5.1 we have implemented the following commands:
HELO \ EHLO:
Syntax: HELO Hostname
HELO: Marks the beginning of a session. 
EHLO: Should only be accepted if the server is an extended mail transfer server(Which is not in our case)
Upon receiving the correct syntax the server will respond with “250 OK”
If an error in the syntax is received the server will reply with: “501 Syntax: HELO hostname”
Sending the “HELO” command at any point in a mail session will reset the mail session, the state and clear all the buffers. As specified by the RFC
No mail transaction can be allowed before receiving the HELO command

MAIL:
Syntax: MAIL FROM:<test@test.com>
MAIL: Marks the beginning of a mail transaction. 
Upon receiving the correct syntax the server will respond with “250 OK”
If an error in the syntax is received the server will reply with: “501 5.5.4 Syntax: MAIL FROM:<address>”
The server will check the correction of the email address format since it’s important for the receiving end.
Nested mail commands are not allowed and the server will respond with “503 5.5.1 Error: nested MAIL command“
If a mail command is used before “HELO” a sequence error reply is returned: “503 5.5.1 Error: send HELO/EHLO first”

RCPT:
Syntax: RCPT TO:<test@test.com>
RCPT: gives the recipients) of an email. This command can be send multiple times to indicate multiple recipients. Mailing lists can be implemented but it’s discouraged by the RFC. 
Upon receiving the correct syntax the server will respond with “250 OK”
If an error in the syntax is received the server will reply with: “501 5.5.4 Syntax: RCPT TO:<address>”
The server will check the correction of the email address format since it’s crucial for the relaying process to have a domain to relay to.
If a “RCPT”  command is used before “MAIL” a sequence error reply is returned: “503 5.5.1 Error: need mail command”

DATA
Syntax: DATA
RCPT: Marks the beginning of the 
Upon receiving the correct syntax the server will respond with “354 End data with <CR><LF>.<CR><LF>”
The server will keep on receiving data until a “.\n” is received which will mark the end of the data and the sending operation will start in a new thread.
Data command can only be used after: “HELO”, “MAIL”, “RCPT”
Each mail transaction will have one data command.

RSET:
Syntax: RSET
RSET: Resets the mail session
Sending the “RSET” command at any point in a mail session will reset the mail session, the state and clear all the buffers. As specified by the RFC

NOOP
Syntax: NOOP
NOOP: This command does not affect any parameters or previously entered commands.  It specifies no action other than that the receiver send a "250 OK" reply

QUIT
Syntax: QUIT
QUIT: This command specifies that the receiver MUST send a "221 OK" reply, and then close the transmission channel.

VRFY
Syntax: VRFY emailAddress
VRFY: This command asks the receiver to confirm that the argument identifies a user or mailbox.  If it is a user name, information is returned as specified in Section 3.5.
Due to security concerns this command will never verify an email. However the syntax is checked.
Sessions:
Whenever a connection is received a new thread is started to handle the client. Each thread will maintain its own state variable and whenever “HELO” command is received a txt file is started, using the port number as a name for the file, to keep the sequence of commands used for relaying the email whenever the email transaction is completed.
State:
The state is thread seperate. 
 state = {
 'HELO': False,
 'MAIL': False,
 'RCPT': False,
 'loop': True,
 'data': False,
 'recipient': "",
 'file':0,
 'domain': "",
 'completedTransaction': False
 }
HELO is marked as true whenever the “HELO” command is recieved. Without HELO no mail transaction will be allowed.
MAIL is marked as true whenever a mail transaction has begun. Without the mail marked as true no recipient command will be allowed.
RCPT is marked as true if a mail transaction has already begun. Once marked as true the data command will be allowed.
Loop is used to keep the “handleClient” function alive. Whenever a “QUIT” command is received this variable will be marked as false.
Recipient is used to keep the email of the recipient in the state for easy access by the resolve domain function.
File is used to keep the name of the file being used to record the sequence of commands.
Domain is used to save the domain provided with the HELO command.
completedTransaction is used to keep track of a client has already completed a mail transaction in this session. If that’s the case than a new file will be started for the new transaction while the earlier transactions are being handled in a seperate thread for forwarding emails.

<h3>Multiple connections:</h3>
Multiple connections are supported by this server. There is no limit to how many users can connect to the server. We have tested this server with 3 connections on a local network and no problems were discovered by us.

<h3>Timeouts:</h3>
Unlike an SMTP client which has different timeouts for every state of the session, SMTP servers will timeout the connection after 5 minutes of inactivity.



