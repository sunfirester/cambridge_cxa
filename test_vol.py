import socket
import time

IP = "192.168.50.171"
PORT = 5000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((IP, PORT))

print("Sending Volume UP (#01,06) three times...")
for _ in range(3):
    s.send(b"#01,06\r")
    time.sleep(0.5)

print("Waiting 1.5 seconds...")
time.sleep(1.5)

print("Sending Volume DOWN (#01,07) three times...")
for _ in range(3):
    s.send(b"#01,07\r")
    time.sleep(0.5)

s.close()
print("Done!")
