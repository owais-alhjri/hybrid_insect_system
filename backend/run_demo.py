import subprocess
import sys
import time
import os
import socket
import warnings
import ipaddress
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SSL_DIR = os.path.join(os.path.dirname(__file__), "ssl")
CERT_FILE = os.path.join(SSL_DIR, "server.crt")
KEY_FILE = os.path.join(SSL_DIR, "server.key")


def kill_zombies():
    if os.name == 'nt':
        os.system("for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %a >nul 2>&1")


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def banner(local_ip: str):
    print("=" * 40)
    print(" 🛰️  OMAN AGRI-TECH SYSTEM  🛰️ ")
    print(f" Backend  : https://{local_ip}:8000")
    print(f" Camera   : https://{local_ip}:8000/camera")
    print(" Frontend : Ensure React is running on :3000")
    print(" NOTE     : Accept the self-signed security warning on the phone")
    print("=" * 40)


def create_self_signed_cert(hostname: str):
    Path(SSL_DIR).mkdir(parents=True, exist_ok=True)
    if Path(CERT_FILE).exists() and Path(KEY_FILE).exists():
        return

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Hybrid Insect System"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])
    san_list = [
        x509.DNSName(hostname),
        x509.DNSName("localhost"),
    ]
    try:
        san_list.append(x509.IPAddress(ipaddress.ip_address(hostname)))
    except ValueError:
        san_list.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(KEY_FILE, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


if __name__ == "__main__":
    kill_zombies()
    time.sleep(1)

    local_ip = get_local_ip()
    create_self_signed_cert(local_ip)
    banner(local_ip)

    warnings.filterwarnings("ignore")
    print("[INFO] Starting FastAPI Backend with HTTPS...")
    backend = subprocess.Popen([
        sys.executable,
        "-m",
        "uvicorn",
        "server.api:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--ssl-keyfile", KEY_FILE,
        "--ssl-certfile", CERT_FILE,
        "--log-level", "info"
    ])

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN]")
    finally:
        backend.terminate()
        kill_zombies()