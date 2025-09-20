import os
import json
import requests
from dotenv import load_dotenv, find_dotenv


def get_env(name: str, *alts: str) -> str:
    for n in (name,) + alts:
        val = os.getenv(n)
        if val:
            return val.strip()
    return None


def main():
    dotenv_path = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path)
    if dotenv_path:
        print(json.dumps({"dotenv": dotenv_path}))

    key = get_env("SINCH_FAX_KEY", "SINCH_KEY", "SINCH_KEY_ID")
    secret = get_env("SINCH_FAX_SECRET", "SINCH_SECRET", "SINCH_KEY_SECRET")
    project_id = get_env("SINCH_FAX_PROJECT_ID", "SINCH_PROJECT_ID")

    if not key or not secret or not project_id:
        raise SystemExit("Missing SINCH credentials: set SINCH_(FAX_)KEY/SECRET and SINCH_(FAX_)PROJECT_ID in .env")

    # The local test PDF endpoint exposed via your FastAPI + ngrok
    ngrok_base = get_env("NGROK_BASE_URL", "ngrok_base_url") or "https://0e261b5c8cde.ngrok-free.app"

    to_number = get_env("TEST_FAX_TO_NUMBER", "SINCH_TO_NUMBER", "SINCH_PHONE_NUMBER")
    if not to_number:
        raise SystemExit("Set TEST_FAX_TO_NUMBER (or SINCH_TO_NUMBER or SINCH_PHONE_NUMBER) in .env to your E.164 number, e.g. +12085551234")

    use_from = (os.getenv("USE_SINCH_FROM", "").strip().lower() in ("1", "true", "yes"))
    from_number = None
    if use_from:
        from_number = get_env("SINCH_FROM_NUMBER", "TEST_FAX_FROM_NUMBER", "SINCH_PHONE_NUMBER")

    callback_url = get_env("TEST_FAX_CALLBACK_URL", "test_fax_callback_url") or f"{ngrok_base}/auth/fax-webhook/sinch"
    content_url = f"{ngrok_base}/test-faxes/test-pdf"

    url = f"https://fax.api.sinch.com/v3/projects/{project_id}/faxes"
    payload = {
        "to": to_number,
        "contentUrl": content_url,
        "callbackUrl": callback_url,
    }
    if from_number:
        payload["from"] = from_number

    headers = {"Content-Type": "application/json"}
    # Debug print of the request (mask secret)
    debug = {
        "url": url,
        "project_id": project_id,
        "key": f"{key[:4]}...{key[-4:]}" if key and len(key) > 8 else key,
        "to": to_number,
        "from": from_number,
        "contentUrl": content_url,
        "callbackUrl": callback_url,
    }
    print(json.dumps({"request": debug}, indent=2))

    resp = requests.post(url, json=payload, headers=headers, auth=(key, secret), timeout=60)
    try:
        data = resp.json()
    except Exception:
        data = {"text": resp.text}
    print(json.dumps({"status": resp.status_code, "body": data}, indent=2))
    if resp.status_code == 401:
        print("Hint: 401 Unauthorized – verify SINCH key/secret pair and project_id. Re-copy from dashboard (no spaces).")


if __name__ == "__main__":
    main()


