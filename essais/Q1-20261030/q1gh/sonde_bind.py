"""Envoie l'IMU virtuelle à une adresse donnée et lit imu.heading chez pypilot."""
import json, socket, sys, time
dest = sys.argv[1]
u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s = socket.create_connection(("localhost", 23322), 2)
s.sendall(b'imu.heading_offset=0\nwatch={"imu.heading":true}\n'); s.settimeout(0.3)
last = None; t0 = time.time()
while time.time() - t0 < 6:
    u.sendto(json.dumps({"heading": 123.4, "headingrate": 0.0, "roll": 0.0, "pitch": 0.0}).encode(), (dest, 20230))
    u.sendto(json.dumps({"rudder": 7.0}).encode(), (dest, 20231))
    try:
        for line in s.recv(65536).decode().splitlines():
            if line.startswith("imu.heading="): last = line.split("=", 1)[1]
    except socket.timeout:
        pass
    time.sleep(0.05)
print(f"envoi vers {dest} -> dernier imu.heading = {last}")
