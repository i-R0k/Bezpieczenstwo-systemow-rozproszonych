# Certyfikaty demo

Katalog `certs/demo` jest przeznaczony na lokalnie generowane certyfikaty TLS/mTLS do demonstracji.

Material prywatny (`*.key`, `*.pem`, `*.crt`, `*.csr`, `*.srl`) jest ignorowany przez `.gitignore` i nie powinien byc commitowany.

Generowanie lokalnych certyfikatow demo:

```powershell
python scripts/generate_demo_certs.py --nodes 6 --out certs/demo --force
```

To nie jest produkcyjna infrastruktura PKI. Certyfikaty sluza do lokalnej demonstracji TLS i jako baza do przyszlego mTLS za proxy albo w runtime gRPC.
