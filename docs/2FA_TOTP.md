# 2FA/TOTP demo

Harmonogram projektu obejmowal 2FA. Repo zawiera minimalna demonstracyjna warstwe TOTP bez przebudowy pelnego modelu uzytkownikow VetClinic.

## Endpointy demo

### POST `/security/2fa/demo/setup`

Tworzy sekret TOTP dla `account_name` w pamieci procesu.

```json
{"account_name":"alice@example.test"}
```

Response zawiera `secret`, `provisioning_uri`, `issuer` i ostrzezenie demo.

### POST `/security/2fa/demo/verify`

Weryfikuje kod TOTP po `secret` albo po `account_name` zapisanym w demo store.

```json
{"account_name":"alice@example.test","code":"123456"}
```

### DELETE `/security/2fa/demo`

Czysci demo store. W strict mode wymaga naglowka `X-BFT-Admin-Token`.

## BFT secure demo

`POST /bft/client/submit-secure-demo` pokazuje jak TOTP moze bronic operacje:

- demo mode: brak TOTP jest akceptowany z warningiem;
- strict mode: poprawny TOTP jest wymagany.

## Generowanie i weryfikacja kodu

Sekret mozna wygenerowac przez endpoint setup albo helper `generate_totp_secret()`. URI `otpauth://` mozna dodac do aplikacji TOTP.

W testach kod jest generowany przez:

```python
pyotp.TOTP(secret).now()
```

## Ograniczenia

- Sekrety sa in-memory.
- Brak pelnego enrollmentu uzytkownika w bazie.
- Brak recovery codes.
- Brak renderowania QR.
- Brak polityki resetu 2FA i audytu logowania.
- To demonstracja mechanizmu, nie produkcyjny IAM.
