from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
from cryptography.hazmat.primitives import serialization

@dataclass(frozen=True)
class KeyPair:
    private: Ed25519PrivateKey
    public: Ed25519PublicKey

def generate_keypair() -> KeyPair:
    priv = Ed25519PrivateKey.generate()
    return KeyPair(priv, priv.public_key())

def save_keypair(kp: KeyPair, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "dev_private.pem").write_bytes(kp.private.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    (directory / "dev_public.pem").write_bytes(kp.public.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))

def load_keypair(directory: Path) -> KeyPair:
    priv = serialization.load_pem_private_key(
        (directory / "dev_private.pem").read_bytes(), password=None)
    pub = serialization.load_pem_public_key((directory / "dev_public.pem").read_bytes())
    return KeyPair(priv, pub)

def load_or_create(directory: Path = Path("keys")) -> KeyPair:
    if (directory / "dev_private.pem").exists():
        return load_keypair(directory)
    kp = generate_keypair()
    save_keypair(kp, directory)
    return kp
