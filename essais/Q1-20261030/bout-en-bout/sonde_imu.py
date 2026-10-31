"""Q1-D — sonde : envoie une IMU virtuelle à pypilot et relit ce qu'il en calcule.

Phase 1 (6 s) : cap = 100 + 3 t (°), lacet 3 °/s, roulis 5°, à 20 Hz.
Phase 2 (2,5 s) : plus aucun envoi ; pypilot doit invalider ses valeurs IMU.
"""
import json
import socket
import time

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tcp = socket.create_connection(("localhost", 23322), 2)
tcp.sendall(b'watch={"imu.heading":true,"imu.heading_lowpass":true,'
            b'"imu.headingrate_lowpass":true,"imu.roll":true,"imu.frequency":true}\n')
tcp.setblocking(False)
vals, buf = {}, ""


def drain():
    global buf
    try:
        while True:
            chunk = tcp.recv(65536)
            if not chunk:
                break
            buf += chunk.decode()
    except BlockingIOError:
        pass
    *lines, buf = buf.split("\n")
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k] = v


t0 = time.monotonic()
while (t := time.monotonic() - t0) < 6.0:
    udp.sendto(json.dumps({"heading": 100 + 3 * t, "headingrate": 3.0, "roll": 5.0}).encode(),
               ("127.0.0.1", 20230))
    drain()
    time.sleep(0.05)
drain()
print(f"après 6 s d'envoi (cap envoyé ≈ {100 + 3 * 6:.1f}°) :")
for k in ("imu.heading", "imu.heading_lowpass", "imu.headingrate_lowpass", "imu.roll", "imu.frequency"):
    print(f"  {k:<26} = {vals.get(k)}")
time.sleep(2.5)
drain()
print("2,5 s après l'arrêt de l'envoi :")
for k in ("imu.heading_lowpass", "imu.headingrate_lowpass", "imu.frequency"):
    print(f"  {k:<26} = {vals.get(k)}")
