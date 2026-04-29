# mTLS, certyfikaty i bezpieczny transport

Harmonogram projektu obejmowal mTLS, certyfikaty i bezpieczny transport miedzy komponentami. W aktualnym stanie runtime mTLS nie jest aktywny domyslnie. Projekt dostarcza tooling demonstracyjny, dokumentacje i przyklad TLS, ale nie wdraza produkcyjnego service mesh.

## Obecny stan

- Domyslna sciezka wykonania to FastAPI/HTTP oraz in-memory BFT services.
- BFT ma Ed25519 message-level signatures, canonical JSON i replay protection.
- Endpoint `/bft/security/transport` raportuje, ze message signing i replay protection sa aktywne, ale `mtls_runtime_enabled=false`.
- Certyfikaty demo mozna wygenerowac lokalnie do `certs/demo`.

## Message signing vs mTLS

Message signing chroni integralnosc i pochodzenie pojedynczego komunikatu BFT. Podpis pozostaje czescia komunikatu i moze byc weryfikowany przez warstwe crypto/replay protection.

mTLS chroni kanal transportowy: szyfruje polaczenie i uwierzytelnia strony na poziomie TLS. mTLS nie zastepuje podpisow komunikatow BFT, bo po zakonczeniu polaczenia nie daje samodzielnego dowodu integralnosci konkretnej wiadomosci.

## Generowanie certyfikatow demo

```powershell
python scripts/generate_demo_certs.py --nodes 6 --out certs/demo --force
```

Skrypt generuje lokalne CA, certyfikaty `node1`..`node6` oraz certyfikat klienta. SAN obejmuje DNS `node1`..`node6`, `localhost` oraz IP `127.0.0.1`. Material prywatny jest ignorowany przez `.gitignore`.

## Przyklad TLS z uvicorn

```powershell
$env:PYTHONPATH="VetClinic/API"
uvicorn vetclinic_api.main:app --host 127.0.0.1 --port 8443 --ssl-certfile certs/demo/node1.crt --ssl-keyfile certs/demo/node1.key
```

Przyklad Docker Compose znajduje sie w `docker-compose.override.tls.example.yml`. Pokazuje lokalny TLS dla `node1`, ale nie wymusza pelnego mTLS.

## Docelowe warianty mTLS

- reverse proxy: nginx, Envoy albo Traefik z walidacja certyfikatow klienta;
- gRPC TLS credentials dla przyszlego runtime `BftNodeService`;
- rotacja certyfikatow i osobna konfiguracja zaufanego CA;
- oddzielne profile demo, test i produkcja.

## Ograniczenia

- mTLS nie jest wymuszany w domyslnym runtime.
- Certyfikaty z `scripts/generate_demo_certs.py` sa demonstracyjne i lokalne.
- Brak produkcyjnego service mesh, automatycznej rotacji certyfikatow i secret managera.
- Docker Compose nie jest modyfikowany; override TLS jest tylko przykladem.
