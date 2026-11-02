#!/usr/bin/env python3
"""
simulate_gps_rmc.py

Simule un GPS qui avance en ligne droite et envoie des phrases NMEA 0183 "RMC"
(position, vitesse, cap) a OpenCPN, pour tester des alarmes de zone a terre,
sans bateau.

Bibliotheque standard de Python seulement (aucune installation).

Exemples :
  # Voir les phrases sans rien envoyer
  python simulate_gps_rmc.py --print-only --duration 5

  # Envoyer a OpenCPN (connexion TCP configuree dans OpenCPN, voir le mode d'emploi)
  python simulate_gps_rmc.py --lat 45.40 --lon -71.89 --heading 90 --speed 4

  # Envoyer en UDP vers un autre ordinateur
  python simulate_gps_rmc.py --protocol udp --host 192.168.1.20 --port 10110

Arret : Ctrl+C.
"""

import argparse
import math
import socket
import sys
import time
from datetime import datetime, timezone

EARTH_RADIUS_M = 6371000.0   # rayon moyen de la Terre, en metres
KNOT_TO_MS = 0.514444        # 1 noeud = 0,514444 m/s


def checksum(body: str) -> str:
    """Somme de controle NMEA : XOR de tous les caracteres entre '$' et '*'."""
    value = 0
    for ch in body:
        value ^= ord(ch)
    return f"{value:02X}"


def nmea_sentence(body: str) -> str:
    """Construit la phrase complete : $corps*XX suivi de fin de ligne."""
    return f"${body}*{checksum(body)}\r\n"


def format_lat(lat: float):
    """Latitude au format NMEA ddmm.mmmm et hemisphere N ou S."""
    hemisphere = "N" if lat >= 0 else "S"
    units = round(abs(lat) * 60 * 10000)          # dix-millièmes de minute
    degrees, remainder = divmod(units, 60 * 10000)
    return f"{degrees:02d}{remainder / 10000:07.4f}", hemisphere


def format_lon(lon: float):
    """Longitude au format NMEA dddmm.mmmm et hemisphere E ou W."""
    hemisphere = "E" if lon >= 0 else "W"
    units = round(abs(lon) * 60 * 10000)
    degrees, remainder = divmod(units, 60 * 10000)
    return f"{degrees:03d}{remainder / 10000:07.4f}", hemisphere


def rmc_sentence(lat, lon, speed_knots, course_deg, when: datetime) -> str:
    """Phrase RMC : heure, etat A (valide), position, vitesse, cap, date."""
    lat_text, ns = format_lat(lat)
    lon_text, ew = format_lon(lon)
    time_text = when.strftime("%H%M%S") + ".00"
    date_text = when.strftime("%d%m%y")
    body = (
        f"GPRMC,{time_text},A,{lat_text},{ns},{lon_text},{ew},"
        f"{speed_knots:.1f},{course_deg % 360:.1f},{date_text},,,A"
    )
    return nmea_sentence(body)


def advance(lat, lon, heading_deg, speed_knots, seconds):
    """Avance en ligne droite (approximation valable sur de petites distances)."""
    distance_m = speed_knots * KNOT_TO_MS * seconds
    heading = math.radians(heading_deg)
    d_lat = (distance_m * math.cos(heading)) / EARTH_RADIUS_M
    d_lon = (distance_m * math.sin(heading)) / (
        EARTH_RADIUS_M * math.cos(math.radians(lat))
    )
    return lat + math.degrees(d_lat), lon + math.degrees(d_lon)


class Sender:
    """Envoie du texte en TCP ou en UDP. En mode 'print-only', n'envoie rien."""

    def __init__(self, protocol, host, port, print_only):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.print_only = print_only
        self.sock = None

    def open(self):
        if self.print_only:
            return
        if self.protocol == "tcp":
            try:
                self.sock = socket.create_connection((self.host, self.port), timeout=5)
            except OSError as error:
                print(
                    f"Connexion TCP impossible vers {self.host}:{self.port} ({error}).\n"
                    "Verifie que OpenCPN est ouvert et qu'une connexion reseau TCP est "
                    "configuree avec l'adresse 0.0.0.0 et le port indique "
                    "(OpenCPN joue alors le role de serveur).",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, text):
        if self.print_only:
            return
        data = text.encode("ascii")
        if self.protocol == "tcp":
            self.sock.sendall(data)
        else:
            self.sock.sendto(data, (self.host, self.port))

    def close(self):
        if self.sock is not None:
            self.sock.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simule un GPS et envoie des phrases NMEA RMC a OpenCPN."
    )
    parser.add_argument("--host", default="127.0.0.1",
                        help="adresse de l'ordinateur qui recoit (defaut : 127.0.0.1, cet ordinateur)")
    parser.add_argument("--port", type=int, default=10110,
                        help="port reseau (defaut : 10110, le port habituel d'OpenCPN)")
    parser.add_argument("--protocol", choices=["tcp", "udp"], default="tcp",
                        help="tcp (defaut) ou udp")
    parser.add_argument("--lat", type=float, default=45.40,
                        help="latitude de depart en degres decimaux (defaut : 45.40, region de Sherbrooke ; a remplacer par ton plan d'eau)")
    parser.add_argument("--lon", type=float, default=-71.89,
                        help="longitude de depart en degres decimaux, negative a l'ouest (defaut : -71.89)")
    parser.add_argument("--heading", type=float, default=90.0,
                        help="cap vrai en degres, 0 = nord, 90 = est (defaut : 90)")
    parser.add_argument("--speed", type=float, default=4.0,
                        help="vitesse en noeuds (defaut : 4)")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="duree en secondes, 0 = jusqu'a Ctrl+C (defaut : 120)")
    parser.add_argument("--rate", type=float, default=1.0,
                        help="phrases par seconde (defaut : 1)")
    parser.add_argument("--print-only", action="store_true",
                        help="affiche les phrases sans rien envoyer")
    parser.add_argument("--quiet", action="store_true",
                        help="n'affiche pas chaque phrase")
    args = parser.parse_args()
    if args.rate <= 0:
        parser.error("--rate doit etre superieur a 0")
    if not -90 <= args.lat <= 90 or not -180 <= args.lon <= 180:
        parser.error("latitude ou longitude hors limites")
    if args.speed < 0:
        parser.error("--speed ne peut pas etre negatif")
    return args


def main():
    args = parse_args()
    sender = Sender(args.protocol, args.host, args.port, args.print_only)
    sender.open()

    period = 1.0 / args.rate
    lat, lon = args.lat, args.lon
    start = time.monotonic()
    next_tick = start
    count = 0

    print(
        f"Depart : {lat:.5f}, {lon:.5f} | cap {args.heading:.0f} deg | "
        f"{args.speed:.1f} noeuds | "
        + ("impression seule" if args.print_only else f"{args.protocol.upper()} vers {args.host}:{args.port}")
    )
    print("Arret : Ctrl+C")

    try:
        while True:
            elapsed = time.monotonic() - start
            if args.duration > 0 and elapsed > args.duration:
                break
            sentence = rmc_sentence(lat, lon, args.speed, args.heading,
                                    datetime.now(timezone.utc))
            sender.send(sentence)
            count += 1
            if not args.quiet:
                print(f"{sentence.strip()}   ({lat:.5f}, {lon:.5f})")
            lat, lon = advance(lat, lon, args.heading, args.speed, period)
            next_tick += period
            pause = next_tick - time.monotonic()
            if pause > 0:
                time.sleep(pause)
    except KeyboardInterrupt:
        print("\nArret demande.")
    except (BrokenPipeError, ConnectionResetError):
        print("\nLa connexion a ete fermee par le recepteur.", file=sys.stderr)
    finally:
        sender.close()
    print(f"{count} phrases envoyees. Position finale : {lat:.5f}, {lon:.5f}")


if __name__ == "__main__":
    main()
