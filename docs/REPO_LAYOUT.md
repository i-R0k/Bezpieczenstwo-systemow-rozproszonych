# Struktura repozytorium

Ten dokument opisuje glowne katalogi projektu BSR/BFT.

| Sciezka | Przeznaczenie |
|---|---|
| `VetClinic/API` | Backend FastAPI, domena VetClinic, legacy blockchain/RPC/cluster oraz warstwa BFT `/bft/*`. |
| `VetClinic/API/vetclinic_api/bft` | Moduly BFT: Narwhal, HotStuff, SWIM, fault injection, checkpointing/recovery, crypto, observability, gRPC contract/runtime. |
| `VetClinic/GUI` | Klient PyQt, PyQt BFT Dashboard oraz integracja dashboardu z panelem administratora VetClinic. |
| `tests/bft` | Kontrakty i testy integracyjne demonstratora BFT. |
| `tests/security` | Security regression tests dla API, BFT, legacy endpointow, infrastruktury, mTLS, TOTP i GUI exposure. |
| `tests/pentest` | Testy kontraktowe lokalnego pentest harness. |
| `tests/gui` | Testy kontraktowe PyQt BFT Dashboard i dokumentacji GUI. |
| `docs` | Dokumentacja koncowa projektu, harmonogram, raport techniczny, instrukcje, ograniczenia i plany security/pentest. |
| `proto` | Kontrakty gRPC/protobuf, w tym `proto/bft.proto`. |
| `pentest` | Konfiguracja DAST, ZAP, Nuclei templates, ffuf wordlists i katalog raportow ignorowany przez git. |
| `scripts` | Runnery testbedow, pentest harness, raporty i narzedzia, w tym generator certyfikatow demo. |
| `certs` | Katalog toolingowy dla certyfikatow demo; prywatne pliki w `certs/demo` nie sa commitowane. |
| `reports` | Lokalnie generowane raporty security/pentest; katalog jest ignorowany poza `.gitkeep`. |

## Requirements

- `requirements-api.txt` - backend/API/CI i testbed BFT.
- `requirements-gui.txt` - PyQt GUI i testy kontraktowe GUI.
- `requirements-security.txt` - narzedzia security/SAST/SCA.
- `requirements.txt` - pelny lokalny bundle developerski API + GUI.

## Artefakty ignorowane

Repozytorium ignoruje cache Pythona, `.pytest_cache`, lokalne raporty, `.env`, wygenerowane stuby gRPC oraz prywatne certyfikaty demo. W repo zostaja tylko pliki zrodlowe, dokumentacja, konfiguracje i `.gitkeep` dla wymaganych pustych katalogow.
