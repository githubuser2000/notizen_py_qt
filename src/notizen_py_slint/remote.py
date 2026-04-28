from __future__ import annotations

from dataclasses import dataclass
from ftplib import FTP, FTP_TLS, error_perm
import netrc
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from .storage import NotizenFileError, load_document_from_bytes, save_document_to_bytes
from .model import NoteDocument


class RemoteFileError(NotizenFileError):
    pass


@dataclass(frozen=True, slots=True)
class FtpLocation:
    scheme: str
    host: str
    port: int | None
    username: str
    password: str
    path: str

    @property
    def use_tls(self) -> bool:
        return self.scheme == "ftps"


def is_remote_uri(value: str | None) -> bool:
    if not value:
        return False
    scheme = urlparse(value).scheme.lower()
    return scheme in {"ftp", "ftps"}


def parse_ftp_url(url: str, *, default_user: str = "anonymous", default_password: str = "anonymous@") -> FtpLocation:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"ftp", "ftps"}:
        raise RemoteFileError(f"Nicht unterstützte Remote-URL: {parsed.scheme or 'ohne Schema'}")
    if not parsed.hostname:
        raise RemoteFileError("FTP-URL ohne Host.")

    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    if not username:
        auth = _netrc_auth(parsed.hostname)
        if auth is not None:
            username, _account, password = auth
    if not username:
        username = default_user
    if not password:
        password = default_password if username == default_user else ""

    path = unquote(parsed.path or "")
    if not path or path == "/":
        raise RemoteFileError("FTP-URL ohne Dateipfad.")
    return FtpLocation(scheme=scheme, host=parsed.hostname, port=parsed.port, username=username, password=password, path=path)


def download_bytes(url: str, *, timeout: int = 30) -> bytes:
    loc = parse_ftp_url(url)
    with _connect(loc, timeout=timeout) as ftp:
        chunks: list[bytes] = []
        try:
            ftp.retrbinary(f"RETR {loc.path}", chunks.append)
        except Exception as exc:  # noqa: BLE001 - normalize remote errors
            raise RemoteFileError(f"FTP-Download fehlgeschlagen: {exc}") from exc
        return b"".join(chunks)


def upload_bytes(url: str, payload: bytes, *, timeout: int = 30, make_dirs: bool = True) -> None:
    loc = parse_ftp_url(url)
    with _connect(loc, timeout=timeout) as ftp:
        remote_path = PurePosixPath(loc.path)
        directory = str(remote_path.parent)
        filename = remote_path.name
        old_dir = ftp.pwd()
        try:
            if directory not in {"", ".", "/"}:
                if make_dirs:
                    _ensure_remote_dir(ftp, directory)
                ftp.cwd(directory)
                stor_name = filename
            else:
                stor_name = loc.path
            from io import BytesIO

            ftp.storbinary(f"STOR {stor_name}", BytesIO(payload))
        except Exception as exc:  # noqa: BLE001
            raise RemoteFileError(f"FTP-Upload fehlgeschlagen: {exc}") from exc
        finally:
            try:
                ftp.cwd(old_dir)
            except Exception:
                pass


def load_uri(uri: str, password: str | None = None) -> NoteDocument:
    if is_remote_uri(uri):
        raw = download_bytes(uri)
        return load_document_from_bytes(raw, source=uri, password=password)
    from .storage import load_document

    return load_document(uri, password=password)


def save_uri(document: NoteDocument, uri: str | None = None, password: str | None | object = ..., backup_count: int = 30) -> str:
    target = uri or document.path or "unbenannt.alx"
    if is_remote_uri(target):
        payload = save_document_to_bytes(document, password=password)
        upload_bytes(target, payload)
        document.path = target
        if password is not ...:
            document.password = password if isinstance(password, str) and password.strip() else None
        document.modified = False
        return target
    from .storage import save_document

    return str(save_document(document, path=target, password=password, backup_count=backup_count))


def _connect(loc: FtpLocation, *, timeout: int) -> FTP:
    cls = FTP_TLS if loc.use_tls else FTP
    ftp = cls()
    try:
        ftp.connect(loc.host, loc.port or 21, timeout=timeout)
        ftp.login(loc.username, loc.password)
        if isinstance(ftp, FTP_TLS):
            ftp.prot_p()
        return ftp
    except Exception as exc:  # noqa: BLE001
        try:
            ftp.close()
        except Exception:
            pass
        raise RemoteFileError(f"FTP-Verbindung fehlgeschlagen: {exc}") from exc


def _ensure_remote_dir(ftp: FTP, directory: str) -> None:
    current = ftp.pwd()
    try:
        if directory.startswith("/"):
            ftp.cwd("/")
        for part in PurePosixPath(directory).parts:
            if part in {"/", "", "."}:
                continue
            try:
                ftp.cwd(part)
            except error_perm:
                ftp.mkd(part)
                ftp.cwd(part)
    finally:
        ftp.cwd(current)


def _netrc_auth(host: str) -> tuple[str, str | None, str] | None:
    try:
        return netrc.netrc().authenticators(host)
    except Exception:
        return None
