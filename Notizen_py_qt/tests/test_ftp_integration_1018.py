from __future__ import annotations

from io import BytesIO

from notizen_py_qt.ftp_sync import FtpTarget


class FakeFTP:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.cwd_path = "/"
        self.storage = {"datei.alx": b"ALX"}

    def connect(self, host: str, timeout: int = 30) -> None:
        self.calls.append(("connect", host, timeout))

    def login(self, username: str | None = None, password: str | None = None) -> None:
        self.calls.append(("login", username, password))

    def set_pasv(self, passive: bool) -> None:
        self.calls.append(("set_pasv", passive))

    def cwd(self, directory: str) -> None:
        self.cwd_path = directory
        self.calls.append(("cwd", directory))

    def retrbinary(self, command: str, callback) -> None:
        self.calls.append(("retrbinary", command))
        callback(self.storage[command.split(" ", 1)[1]])

    def storbinary(self, command: str, stream: BytesIO) -> None:
        self.calls.append(("storbinary", command, stream.read()))

    def quit(self) -> None:
        self.calls.append(("quit",))

    def close(self) -> None:
        self.calls.append(("close",))


def test_ftp_target_decodes_legacy_url_parts() -> None:
    target = FtpTarget.from_fields("ftp://alex%20user:pass%21@example.org/Ordner/alte%20Datei.alx", "")
    assert target.host == "example.org"
    assert target.username == "alex user"
    assert target.password == "pass!"
    assert target.remote_path == "/Ordner/alte Datei.alx"
    assert target.safe_display_url == "ftp://alex%20user@example.org/Ordner/alte%20Datei.alx"


def test_ftp_download_uses_directory_filename_and_passive_mode() -> None:
    fake = FakeFTP()
    target = FtpTarget(
        host="example.org",
        remote_path="/daten/datei.alx",
        username="user",
        password="pw",
        passive=False,
        ftp_factory=lambda: fake,
    )
    payload = target.download()
    assert payload == b"ALX"
    assert fake.calls[:4] == [
        ("connect", "example.org", 30),
        ("login", "user", "pw"),
        ("set_pasv", False),
        ("cwd", "/daten"),
    ]
    assert ("retrbinary", "RETR datei.alx") in fake.calls
    assert ("quit",) in fake.calls


def test_ftp_upload_uses_stor_binary() -> None:
    fake = FakeFTP()
    target = FtpTarget(host="example.org", remote_path="/datei.alx", ftp_factory=lambda: fake)
    target.upload(b"NEU")
    assert ("login", None, None) in fake.calls
    assert ("storbinary", "STOR datei.alx", b"NEU") in fake.calls
