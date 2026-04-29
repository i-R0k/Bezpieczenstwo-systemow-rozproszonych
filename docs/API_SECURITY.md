# API security demo

## 2FA/TOTP

### POST `/security/2fa/demo/setup`

Tworzy sekret TOTP w pamieci procesu.

Request:

```json
{"account_name":"alice@example.test"}
```

Response: `account_name`, `secret`, `provisioning_uri`, `issuer`, `demo_warning`.

Typowe bledy: `422` dla pustego `account_name`.

### POST `/security/2fa/demo/verify`

Weryfikuje kod TOTP po `secret` albo po `account_name`.

Request:

```json
{"account_name":"alice@example.test","code":"123456"}
```

Response: `valid`, `account_name`, `issuer`.

Typowe bledy: `400` gdy nie podano ani `secret`, ani `account_name`; `404` gdy konto nie ma sekretu w demo store.

### DELETE `/security/2fa/demo`

Czysci demo store. W strict mode wymaga `X-BFT-Admin-Token`.

Typowe bledy: `401`/`403` w strict mode bez poprawnego tokena, `503` przy blednej konfiguracji strict mode.
