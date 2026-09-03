"""Voice-note recording storage.

Render's free web-service tier (and most similar hosts) wipe the local
filesystem on every deploy/restart/spin-down. Saving recordings to local
disk works fine for local dev but silently loses every recording in
production the next time the service restarts.

This module adds an optional S3-compatible object storage backend (works
with Cloudflare R2, Backblaze B2, AWS S3, or anything else that speaks the
S3 API) that activates automatically once its env vars are set, and falls
back to today's local-disk behavior when they aren't - so this is a no-op
until someone actually configures a bucket.
"""
import os
import uuid

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads", "notes")
os.makedirs(UPLOADS_DIR, exist_ok=True)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        from botocore.config import Config

        access_key = os.getenv("S3_ACCESS_KEY_ID")
        secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
        public_url_base = os.getenv("S3_PUBLIC_URL_BASE")
        if not access_key or not secret_key or not public_url_base:
            raise RuntimeError(
                "S3_BUCKET_NAME is set but S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY and/or "
                "S3_PUBLIC_URL_BASE are missing - all four are required together to use "
                "object storage for voice notes."
            )
        _s3_client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=os.getenv("S3_REGION", "auto"),
            config=Config(signature_version="s3v4"),
        )
    return _s3_client


def save_audio_bytes(original_filename: str, data: bytes) -> str:
    """Save a recorded voice note and return the URL it can be fetched from."""
    ext = os.path.splitext(original_filename or "")[1] or ".webm"
    filename = f"{uuid.uuid4().hex}{ext}"

    if S3_BUCKET_NAME:
        client = _get_s3_client()
        key = f"notes/{filename}"
        client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=data)
        public_url_base = os.getenv("S3_PUBLIC_URL_BASE").rstrip("/")
        return f"{public_url_base}/{key}"

    file_path = os.path.join(UPLOADS_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(data)
    return f"/uploads/notes/{filename}"


def delete_audio_file(audio_url: str):
    """Best-effort removal of a previously uploaded note recording."""
    if not audio_url:
        return
    if S3_BUCKET_NAME and not audio_url.startswith("/uploads/notes/"):
        try:
            key = "notes/" + audio_url.rsplit("/notes/", 1)[-1]
            _get_s3_client().delete_object(Bucket=S3_BUCKET_NAME, Key=key)
        except Exception as e:
            print(f"[WARN] Could not remove audio object {audio_url}: {e}")
        return

    try:
        filename = os.path.basename(audio_url)
        file_path = os.path.join(UPLOADS_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    except OSError as e:
        print(f"[WARN] Could not remove audio file {audio_url}: {e}")
