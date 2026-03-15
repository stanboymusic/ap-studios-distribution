# ERN XMLDSig certificates

Generate local test certificates:

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

Files expected by the API:

- `backend/certs/key.pem`
- `backend/certs/cert.pem`

In production use a certificate issued by a trusted CA and secure secret storage.
