![Banner](banner.png)

# crypto-pem-format-converter

Converts a PEM encoded private key, public key, or Diffie-Hellman parameter set between container formats: PKCS8, TraditionalOpenSSL, SubjectPublicKeyInfo for public keys, and PKCS1 for RSA private keys (written in its TraditionalOpenSSL form, the `BEGIN RSA PRIVATE KEY` block).

## Requirements

- Python 3
- `cryptography` 41.0.7 or later (see requirements.txt)

## Install

```bash
git clone https://github.com/ShadowGuard-AI/crypto-pem-format-converter.git
cd crypto-pem-format-converter
pip install -r requirements.txt
```

## Usage

```bash
python3 main.py -i private.pem -f PKCS8 -t private
python3 main.py -i private.pem -f PKCS1 -t private
python3 main.py -i public.pem -t public
python3 main.py -i private.pem -t private -e best -pw "secret" -o encrypted.pem
```

With no `-f`, a private key defaults to PKCS8 and a public key to SubjectPublicKeyInfo. With no `-o`, the converted PEM is printed to stdout. Bad input, an unsupported format for the key type, or a wrong password exits 1.

## Parameters

- `-i`, `--input-file`: Path to the input PEM file. Alternatives are `-p` (paste a private key), `-u` (paste a public key), and `-params` (paste DH parameters); exactly one input source is required.
- `-o`, `--output-file`: Path to the output PEM file (default: stdout).
- `-f`, `--output-format`: `PKCS1`, `PKCS8`, `SubjectPublicKeyInfo`, or `TraditionalOpenSSL`.
- `-t`, `--key-type`: `private`, `public`, or `dhparams` (default: private). The type must match the input.
- `-e`, `--encryption`: `none` or `best` for private key output (default: none).
- `-pw`, `--password`: Password that decrypts an encrypted input key, and that encrypts the output when `-e best` is given. One password serves both jobs in a single run.

## Verified run note

The usage and parameters above are taken from the argument parser in `main.py`. A live run in this environment is blocked because the `cryptography` package is not installed here, so even `--help` stops at that import; no run result is claimed for this tool.

## License

Licensed under the terms in LICENSE.
