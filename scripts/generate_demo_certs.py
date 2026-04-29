from __future__ import annotations

import argparse
import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "certs" / "demo"


def _private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _write_private_key(path: Path, key: rsa.RSAPrivateKey, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} exists; use --force to overwrite")
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def _write_cert(path: Path, cert: x509.Certificate, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} exists; use --force to overwrite")
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def _name(common_name: str) -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VetClinic BFT Demo"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )


def _create_ca() -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = _private_key()
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(_name("VetClinic BFT Demo CA"))
        .issuer_name(_name("VetClinic BFT Demo CA"))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    return key, cert


def _create_leaf(
    *,
    common_name: str,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    dns_names: list[str],
    client: bool = False,
) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = _private_key()
    now = datetime.now(timezone.utc)
    usages = [ExtendedKeyUsageOID.CLIENT_AUTH] if client else [ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]
    cert = (
        x509.CertificateBuilder()
        .subject_name(_name(common_name))
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=90))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName(name) for name in dns_names]
                + [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
            ),
            critical=False,
        )
        .add_extension(x509.ExtendedKeyUsage(usages), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    return key, cert


def generate_demo_certs(nodes: int, out: Path, force: bool) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    ca_key, ca_cert = _create_ca()
    ca_key_path = out / "demo-ca.key"
    ca_cert_path = out / "demo-ca.crt"
    _write_private_key(ca_key_path, ca_key, force)
    _write_cert(ca_cert_path, ca_cert, force)
    written.extend([ca_key_path, ca_cert_path])

    for node_id in range(1, nodes + 1):
        node = f"node{node_id}"
        key, cert = _create_leaf(
            common_name=node,
            ca_key=ca_key,
            ca_cert=ca_cert,
            dns_names=[node, "localhost"],
        )
        key_path = out / f"{node}.key"
        cert_path = out / f"{node}.crt"
        _write_private_key(key_path, key, force)
        _write_cert(cert_path, cert, force)
        written.extend([key_path, cert_path])

    client_key, client_cert = _create_leaf(
        common_name="demo-client",
        ca_key=ca_key,
        ca_cert=ca_cert,
        dns_names=["demo-client", "localhost"],
        client=True,
    )
    client_key_path = out / "client.key"
    client_cert_path = out / "client.crt"
    _write_private_key(client_key_path, client_key, force)
    _write_cert(client_cert_path, client_cert, force)
    written.extend([client_key_path, client_cert_path])
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local demo TLS/mTLS certificates for the BFT project.")
    parser.add_argument("--nodes", type=int, default=6, help="Number of node certificates to generate.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory, default certs/demo.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    written = generate_demo_certs(args.nodes, out, args.force)
    print(f"Generated {len(written)} demo certificate files in {out}")
    print("Private key material was written to disk but not logged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
