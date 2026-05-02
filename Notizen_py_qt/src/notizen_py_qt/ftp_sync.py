from __future__ import annotations

from dataclasses import dataclass
from ftplib import FTP, all_errors
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse


class FtpSyncError(Exception):
    """Raised when legacy FTP open/save fails."""


@dataclass(slots=True)
class FtpTarget:
    host: str
    remote_path: str
    username: str = ""
    password: str = ""
    timeout: int = 30

    @classmethod
    def from_fields(cls, host: str, remote_path: str, username: str = "", password: str = "") -> "FtpTarget":
        raw_host = (host or "").strip()
        parsed = urlparse(raw_host if "://" in raw_host else f"ftp://{raw_host}")
        normalized_host = parsed.hostname or raw_host.strip("/")
        if not normalized_host:
            raise FtpSyncError("FTP-Host fehlt.")
        if parsed.username and not username:
            username = parsed.username
        if parsed.password and not password:
            password = parsed.password
        path = (remote_path or parsed.path or "").strip()
        if not path:
            raise FtpSyncError("FTP-Pfad fehlt.")
        if not path.startswith("/"):
            path = "/" + path
        if not path.lower().endswith(".alx"):
            raise FtpSyncError("FTP-Pfad muss auf eine .alx-Datei zeigen.")
        return cls(host=normalized_host, remote_path=path, username=username.strip(), password=password)

    @property
    def display_url(self) -> str:
        user = f"{self.username}@" if self.username else ""
        return f"ftp://{user}{self.host}{self.remote_path}"

    def _login(self) -> FTP:
        ftp = FTP()
        try:
            ftp.connect(self.host, timeout=self.timeout)
            if self.username:
                ftp.login(self.username, self.password)
            else:
                ftp.login()
            return ftp
        except all_errors as exc:
            try:
                ftp.close()
            except Exception:
                pass
            raise FtpSyncError(f"FTP-Verbindung fehlgeschlagen: {exc}") from exc

    def _directory_and_filename(self) -> tuple[str, str]:
        posix_path = PurePosixPath(self.remote_path)
        directory = str(posix_path.parent)
        if directory == ".":
            directory = "/"
        filename = posix_path.name
        return directory, filename

    def download(self) -> bytes:
        ftp = self._login()
        buffer = BytesIO()
        directory, filename = self._directory_and_filename()
        try:
            if directory and directory != "/":
                ftp.cwd(directory)
            ftp.retrbinary(f"RETR {filename}", buffer.write)
            return buffer.getvalue()
        except all_errors as exc:
            raise FtpSyncError(f"FTP-Download fehlgeschlagen: {exc}") from exc
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def upload(self, payload: bytes) -> None:
        ftp = self._login()
        directory, filename = self._directory_and_filename()
        try:
            if directory and directory != "/":
                ftp.cwd(directory)
            ftp.storbinary(f"STOR {filename}", BytesIO(payload))
        except all_errors as exc:
            raise FtpSyncError(f"FTP-Upload fehlgeschlagen: {exc}") from exc
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()
