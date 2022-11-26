from socket import *
serverName = 'serverName'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.connect((serverName, serverPort))
sentence = raw_input('input lowercase sentence')
clientSocket.send(sentence.encode())
modifiedSentence = clientSocket.recv(1024)
print('from server:', modifiedSentence.decode())
clientSocket.close()