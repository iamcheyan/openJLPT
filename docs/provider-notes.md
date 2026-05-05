# Provider Notes

This document records provider-specific setup notes for `generate_bank.py`.
Do not put real API keys in this file.

## Google Gemini

### Current Configuration

Gemini uses the native Google Generative Language REST API, not the OpenAI-compatible chat completions format.

```env
GEMINI_API_KEY=
GEMINI_API_KEY_2=
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

```json
{
  "format": "gemini",
  "model": "gemini-2.5-flash-lite",
  "api_key_envs": ["GEMINI_API_KEY", "GEMINI_API_KEY_2"]
}
```

### Important Notes

- Use `GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta`.
- `generate_bank.py` calls Gemini as:

  ```text
  /models/{model}:generateContent?key=...
  ```

- Do not configure Gemini as an OpenAI-compatible `/chat/completions` provider.
- `gemini-2.0-flash-lite` returned 404 for the current account. The API error said the model is no longer available to new users.
- `gemini-2.5-flash-lite` passed testing and is the current default.
- Multiple Gemini keys are supported through `api_key_envs`. Calls rotate through available keys, and if one key fails the provider tries the next key before failing the provider call.

### Verification

Use:

```sh
python3 verify_gemini.py --model gemini-2.5-flash-lite --runs 3 --timeout 20
```

Expected result:

```text
API key #1 ... ok
API key #2 ... ok
```

### Fixes Applied

- Added support for multiple keys per provider in `generate_bank.py`.
- Added `GEMINI_API_KEY_2` to `.env.example`.
- Added `api_key_envs` to the Gemini config.
- Changed the default Gemini model from `gemini-2.0-flash-lite` to `gemini-2.5-flash-lite`.
- Added `verify_gemini.py` for isolated Gemini diagnostics.

## Volcengine Ark

### Current Configuration

The project uses Coding Plan's OpenAI-compatible endpoint, not the regular Ark public model endpoint.

```env
ARK_API_KEY=
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions
ARK_MODEL=doubao-seed-2-0-code
```

```json
{
  "format": "openai",
  "base_url_env": "ARK_BASE_URL",
  "model_env": "ARK_MODEL",
  "model": "doubao-seed-2-0-code"
}
```

### Important Notes

- For Coding Plan, use:

  ```text
  https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions
  ```

- The old path below returns 404 and should not be used:

  ```text
  https://ark.cn-beijing.volces.com/api/coding/chat/completions
  ```

- The regular Ark endpoint below is valid as an Ark endpoint, but it does not use Coding Plan entitlement:

  ```text
  https://ark.cn-beijing.volces.com/api/v3/chat/completions
  ```

- With the regular `/api/v3/chat/completions` endpoint, unactivated models return errors such as `ModelNotOpen`.
- The Coding Plan endpoint accepted `doubao-seed-2-0-code`.
- The Coding Plan endpoint also accepted `doubao-seed-2-0-pro-260215` in testing, but `doubao-seed-2-0-code` is the safer default because it matches the Coding Plan code model naming.
- `auto` returned `UnsupportedModel` for Coding Plan and should not be used in `generate_bank.py`.

### Verification

Use:

```sh
python3 verify_ark.py \
  --url https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions \
  --model doubao-seed-2-0-code \
  --timeout 20
```

Expected result:

```text
[OK] 200
Reply: OK
```

To test a model from the Ark console, pass it explicitly:

```sh
python3 verify_ark.py --model YOUR_MODEL_OR_ENDPOINT_ID --timeout 20
```

### Fixes Applied

- Added `verify_ark.py` for isolated Ark endpoint/model diagnostics.
- Updated `.env.example` to use the Coding Plan OpenAI-compatible endpoint.
- Added `ARK_MODEL` to `.env.example`.
- Updated `config.json` so Ark can read `ARK_MODEL` through `model_env`.
- Changed the default Ark model to `doubao-seed-2-0-code`.

## Shared Provider Resilience

`generate_bank.py` now has safer long-running behavior:

- It does not keep all approved vocabulary items in memory; it keeps a count after each item is saved.
- Vocabulary questions are saved one by one before marking state as generated.
- API calls rotate through all configured keys for a provider.
- Transient API failures such as `429`, `5xx`, timeout, DNS failure, and connection reset are retried once.
- Review calls are treated as three states:
  - approved
  - explicitly rejected by reviewer
  - reviewer call failed
- If reviewer calls fail, the word remains pending instead of being incorrectly marked as failed.
- If a vocabulary section makes no progress for three consecutive rounds, it exits that section and leaves pending words for a later retry.
