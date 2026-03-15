from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lxml import etree

from app.config.signing import (
    ERN_SIGNING_CERT_PATH,
    ERN_SIGNING_ENABLED,
    ERN_SIGNING_KEY_PATH,
    ERN_SIGNING_REQUIRE_CERT,
)


class XMLSigningError(RuntimeError):
    pass


@dataclass
class SigningResult:
    signed_xml: bytes
    applied: bool
    signature_algorithm: str | None = None
    digest_algorithm: str | None = None
    key_path: str | None = None
    cert_path: str | None = None
    message: str | None = None


def _read_file(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except Exception as exc:
        raise XMLSigningError(f"Unable to read file {path}: {exc}") from exc


def verify_ern_signature(xml_bytes: bytes, cert_bytes: bytes | None = None) -> bool:
    try:
        from signxml import XMLVerifier
    except Exception as exc:
        raise XMLSigningError(
            "signxml dependency is missing. Install with: pip install signxml cryptography"
        ) from exc

    try:
        if cert_bytes:
            XMLVerifier().verify(xml_bytes, x509_cert=cert_bytes)
        else:
            XMLVerifier().verify(xml_bytes)
        return True
    except Exception as exc:
        raise XMLSigningError(f"Signature verification failed: {exc}") from exc


def sign_ern_xml(
    xml_bytes: bytes,
    key_path: Optional[str] = None,
    cert_path: Optional[str] = None,
    force: bool = False,
) -> SigningResult:
    signing_enabled = ERN_SIGNING_ENABLED or force
    if not signing_enabled:
        return SigningResult(
            signed_xml=xml_bytes,
            applied=False,
            message="XML signing disabled",
        )

    resolved_key = Path(key_path) if key_path else ERN_SIGNING_KEY_PATH
    resolved_cert = Path(cert_path) if cert_path else ERN_SIGNING_CERT_PATH

    if not resolved_key.exists() or not resolved_cert.exists():
        message = (
            f"Signing certificate files not found (key={resolved_key}, cert={resolved_cert}). "
            "Generate files with: openssl req -x509 -newkey rsa:4096 -keyout key.pem "
            "-out cert.pem -days 365 -nodes"
        )
        if ERN_SIGNING_REQUIRE_CERT or force:
            raise XMLSigningError(message)
        return SigningResult(signed_xml=xml_bytes, applied=False, message=message)

    try:
        from signxml import XMLSigner, methods  # lazy import to keep app bootable without dependency
    except Exception as exc:
        raise XMLSigningError(
            "signxml dependency is missing. Install with: pip install signxml cryptography"
        ) from exc

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    key_data = _read_file(resolved_key)
    cert_data = _read_file(resolved_cert)

    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )
    signed_root = signer.sign(
        root,
        key=key_data,
        cert=cert_data,
        reference_uri="",
    )
    signed_xml = etree.tostring(
        signed_root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )
    verify_ern_signature(signed_xml, cert_bytes=cert_data)

    return SigningResult(
        signed_xml=signed_xml,
        applied=True,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        key_path=str(resolved_key),
        cert_path=str(resolved_cert),
        message="ERN signed with XMLDSig",
    )
