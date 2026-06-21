import socket
import time

IP = "192.168.50.171"
PORT = 5000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(0.5)
s.connect((IP, PORT))

print("Scanning #01,01 through #01,30...")
for i in range(1, 31):
    cmd = f"#01,{i:02d}\r"
    s.send(cmd.encode())
    
    try:
        reply = s.recv(1024).decode().strip()
        if reply == "#00,02":
            pass # Invalid
        elif reply:
            print(f"Command {cmd.strip()} -> {reply}")
    except socket.timeout:
        print(f"Command {cmd.strip()} -> <timed out>")
    
    time.sleep(0.1)

s.close()
