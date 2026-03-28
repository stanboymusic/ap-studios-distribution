"""Local fallback shim for environments without external aiosmtplib installed."""
from __future__ import annotations


async def send(*args, **kwargs):
    raise RuntimeError("aiosmtplib package is not installed in this environment")
