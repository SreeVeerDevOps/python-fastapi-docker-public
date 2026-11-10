"""Upload files to an Azure Storage account using the server's Managed Identity (MSI).

Settings are read from Key Vault (same vault as routers/aws.py and routers/azure.py):
  storage-account-name    - name of the target storage account (required)
  storage-container-name  - blob container to upload into (optional, default "uploads")
  azure-client-id         - client ID of a *user-assigned* identity to use for storage
                            (optional; omit to use the AZURE_CLIENT_ID App Setting)

Key Vault itself is read with the identity in the AZURE_CLIENT_ID App Setting
(user-assigned), or the system-assigned identity when that setting is empty. The identity used
for storage needs the "Storage Blob Data Contributor" role on the storage account.
No keys or connection strings are used.
"""
import mimetypes
import os
from typing import List
from urllib.parse import quote

from azure.core.exceptions import AzureError, HttpResponseError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "100"))
PREVIEW_TEXT_BYTES = 8 * 1024          # first 8 KB of text files
PREVIEW_IMAGE_MAX_BYTES = 20 * 1024 * 1024
MAX_LISTED = 50

TEXT_TYPES = {"application/json", "application/xml", "application/javascript", "application/x-yaml",
              "application/yaml", "application/x-sh", "application/x-python", "application/sql"}
TEXT_EXTS = {".txt", ".md", ".csv", ".tsv", ".log", ".json", ".yaml", ".yml", ".xml", ".ini", ".cfg",
             ".conf", ".env", ".py", ".js", ".ts", ".sh", ".ps1", ".tf", ".tfvars", ".sql", ".html",
             ".htm", ".css", ".java", ".go", ".cs", ".dockerfile", ".toml"}

# Served file content is untrusted: never let the browser run it as a page on this site.
SAFE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox",
    "Cache-Control": "private, max-age=60",
}

key_vault_name = "azureb61kv"
key_vault_uri = f"https://azureb61kv.vault.azure.net"
secret_account = "storage-account-name"
secret_container = "storage-container-name"
#Client ID  Of MSI
secret_client_id = "azure-client-id"

_settings_cache = None
_container_client = None


def _get_secret(client, name, required=False):
    try:
        return client.get_secret(name).value
    except ResourceNotFoundError:
        if required:
            raise RuntimeError(f"Secret '{name}' was not found in Key Vault '{key_vault_name}'.")
        return None


def _settings():
    """Read storage settings from Key Vault once and cache them."""
    global _settings_cache
    if _settings_cache is None:
        kv_client = SecretClient(
            vault_url=key_vault_uri,
            credential=DefaultAzureCredential(managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")),
        )
        account = _get_secret(kv_client, secret_account, required=True)
        container = _get_secret(kv_client, secret_container) or "uploads"
        # Optional override for storage; otherwise use the same identity as the rest of the app.
        client_id = _get_secret(kv_client, secret_client_id) or os.getenv("AZURE_CLIENT_ID")
        print(f"Storage settings from Key Vault: account={account}, container={container}, "
              f"identity={'user-assigned' if client_id else 'system-assigned'}")
        _settings_cache = {"account": account, "container": container, "client_id": client_id}
    return _settings_cache


def _get_container_client():
    """Create the container client lazily so the app still starts if Key Vault/storage isn't ready."""
    global _container_client
    if _container_client is None:
        cfg = _settings()
        credential = DefaultAzureCredential(managed_identity_client_id=cfg["client_id"])
        service = BlobServiceClient(
            account_url=f"https://{cfg['account']}.blob.core.windows.net",
            credential=credential,
        )
        _container_client = service.get_container_client(cfg["container"])
    return _container_client


def _preview_kind(name: str, content_type: str) -> str:
    """'image', 'text' or 'none' - decides how the hover preview shows a file."""
    ct = (content_type or "").split(";")[0].strip().lower()
    if not ct or ct == "application/octet-stream":
        ct = (mimetypes.guess_type(name)[0] or "").lower()
    ext = os.path.splitext(name)[1].lower() or ("." + name.lower())
    if ct.startswith("image/"):
        return "image"
    if ct.startswith("text/") or ct in TEXT_TYPES or ext in TEXT_EXTS:
        return "text"
    return "none"


def _list_blobs(limit: int = MAX_LISTED):
    """Return (newest `limit` blobs, total blob count)."""
    blobs = []
    for blob in _get_container_client().list_blobs():
        content_type = blob.content_settings.content_type if blob.content_settings else ""
        blobs.append(
            {
                "name": blob.name,
                "size_kb": round((blob.size or 0) / 1024, 1),
                "content_type": content_type or "unknown",
                "kind": _preview_kind(blob.name, content_type),
                "last_modified": blob.last_modified.strftime("%Y-%m-%d %H:%M UTC")
                if blob.last_modified
                else "",
            }
        )
    blobs.sort(key=lambda b: b["last_modified"], reverse=True)
    return blobs[:limit], len(blobs)


def _render(request: Request, results=None, error=None):
    account, container = None, None
    blobs, total = [], 0
    list_error = None
    try:
        cfg = _settings()
        account, container = cfg["account"], cfg["container"]
        blobs, total = _list_blobs()
    except Exception as exc:  # show the page even if Key Vault or listing fails
        if account:
            list_error = _friendly_error(exc)
        else:
            error = error or _friendly_error(exc)
    return templates.TemplateResponse(
        request,
        "upload.html",
        {
            "account": account,
            "container": container,
            "max_mb": MAX_UPLOAD_MB,
            "results": results or [],
            "error": error,
            "blobs": blobs,
            "total": total,
            "list_error": list_error,
        },
    )


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, ResourceNotFoundError):
        container = (_settings_cache or {}).get("container", "uploads")
        return f"Container '{container}' was not found in the storage account."
    if isinstance(exc, HttpResponseError) and exc.status_code == 403:
        return (
            "Access denied (403). Check that the server's identity can read secrets in "
            f"Key Vault '{key_vault_name}' and has the 'Storage Blob Data Contributor' "
            "role on the storage account."
        )
    if isinstance(exc, (AzureError, RuntimeError)):
        return str(exc).splitlines()[0]
    return f"{type(exc).__name__}: {exc}"


@router.get("/upload", tags=["Azure Storage"])
def upload_page(request: Request):
    return _render(request)


@router.post("/upload", tags=["Azure Storage"])
def upload_files(request: Request, files: List[UploadFile] = File(...)):
    results = []
    try:
        container_client = _get_container_client()
    except Exception as exc:
        return _render(request, error=_friendly_error(exc))

    for upload in files:
        name = os.path.basename(upload.filename or "").strip()
        if not name:
            continue
        try:
            upload.file.seek(0, os.SEEK_END)
            size = upload.file.tell()
            upload.file.seek(0)
            if size > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(f"File exceeds the {MAX_UPLOAD_MB} MB limit.")
            container_client.upload_blob(
                name=name,
                data=upload.file,
                length=size,
                overwrite=True,
                content_settings=ContentSettings(content_type=upload.content_type),
            )
            results.append({"name": name, "ok": True, "label": f"Uploaded · {round(size / 1024, 1)} KB"})
        except Exception as exc:
            results.append({"name": name, "ok": False, "message": _friendly_error(exc)})
        finally:
            upload.file.close()

    return _render(request, results=results)


def _delete_blobs(container_client, names):
    results = []
    for name in names:
        try:
            container_client.delete_blob(name, delete_snapshots="include")
            results.append({"name": name, "ok": True, "label": "Deleted"})
        except ResourceNotFoundError:
            results.append({"name": name, "ok": True, "label": "Already gone"})
        except Exception as exc:
            results.append({"name": name, "ok": False, "message": _friendly_error(exc)})
    return results


@router.post("/upload/delete", tags=["Azure Storage"])
def delete_selected(request: Request, names: List[str] = Form(default=[])):
    names = [n for n in dict.fromkeys(names) if n]
    if not names:
        return _render(request, error="Select at least one file to delete.")
    try:
        container_client = _get_container_client()
    except Exception as exc:
        return _render(request, error=_friendly_error(exc))
    return _render(request, results=_delete_blobs(container_client, names))


@router.post("/upload/delete-all", tags=["Azure Storage"])
def delete_all(request: Request):
    try:
        container_client = _get_container_client()
        names = [b.name for b in container_client.list_blobs()]
    except Exception as exc:
        return _render(request, error=_friendly_error(exc))
    if not names:
        return _render(request, error="The container is already empty.")
    results = _delete_blobs(container_client, names)
    failed = [r for r in results if not r["ok"]]
    summary = {"name": f"{len(results) - len(failed)} of {len(results)} files", "ok": True, "label": "Deleted"}
    return _render(request, results=[summary] + failed)


@router.get("/upload/file/{name:path}", tags=["Azure Storage"])
def get_file(name: str, preview: bool = False):
    """Stream a blob through the server (MSI auth). preview=1 returns a small, safe preview."""
    try:
        blob_client = _get_container_client().get_blob_client(name)
        props = blob_client.get_blob_properties()
    except ResourceNotFoundError:
        return PlainTextResponse("File not found.", status_code=404)
    except Exception as exc:
        return PlainTextResponse(_friendly_error(exc), status_code=502)

    content_type = props.content_settings.content_type or ""
    kind = _preview_kind(name, content_type)

    if preview:
        if kind == "text":
            length = min(props.size, PREVIEW_TEXT_BYTES)
            data = blob_client.download_blob(offset=0, length=length).readall() if length else b""
            headers = dict(SAFE_HEADERS, **{"X-Truncated": "1" if props.size > length else "0"})
            return PlainTextResponse(data.decode("utf-8", errors="replace"), headers=headers)
        if kind == "image" and props.size <= PREVIEW_IMAGE_MAX_BYTES:
            media_type = content_type if content_type.startswith("image/") else mimetypes.guess_type(name)[0]
            return StreamingResponse(blob_client.download_blob().chunks(), media_type=media_type, headers=SAFE_HEADERS)
        return Response(status_code=415)

    # Full file: always as a download, never rendered inline.
    filename = quote(os.path.basename(name))
    headers = dict(SAFE_HEADERS, **{"Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                                    "Content-Length": str(props.size)})
    return StreamingResponse(blob_client.download_blob().chunks(),
                             media_type=content_type or "application/octet-stream", headers=headers)
