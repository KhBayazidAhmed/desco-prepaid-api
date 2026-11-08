# Privacy and reporting

This repository is an unofficial reference and a locally run example, not a hosted account service. Maintainers do not need your DESCO credentials, cookies, or personal account data to discuss the documented flow.

The example sends credentials to the official DESCO HTTPS endpoint, retains cookies in process memory, and prints balance results locally. It does not save session files or send telemetry. Balance output is private even when account identifiers are omitted. Do not run it with public CI credentials or publish its output.

## Before opening an issue or pull request

Use synthetic values or placeholders. Remove all passwords, session cookies, CSRF tokens, authorization headers, account IDs, account and meter numbers, names, addresses, phone numbers, and actual balances. Do not upload raw HAR files, cookie jars, full responses, or unredacted screenshots.

A useful report includes the endpoint template (for example `/api/accounts/{accountId}/balance`), HTTP status, a redacted error code, Python version, and steps using placeholders. Never include login request bodies.

## If you accidentally disclose data

Remove it from the public location and use the official portal's available password/session controls if credentials were involved. Deleting a file in a later commit does not erase earlier Git history or copies held by others. Do not post the secret again to request help.

The `.gitignore` excludes common local secret and capture files, but cannot detect every secret or prevent an explicit forced add. Review staged changes before publishing.
