"""Validation and Windows trust boundaries shared by privileged actions."""
import ctypes
from ctypes import wintypes
import ipaddress
import re
import subprocess


def validate_host(value):
    host = str(value).strip()
    if '%' in host and not re.fullmatch(r'[A-Za-z0-9_.-]+', host.split('%', 1)[1]):
        raise ValueError('IPv6 scope không hợp lệ.')
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    if len(host) > 253 or not host or not all(
        re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label)
        for label in host.rstrip('.').split('.')
    ):
        raise ValueError('Tên máy hoặc IP không hợp lệ.')
    return host


def require_microsoft_signature(path):
    # Pass the path as data, never interpolate it into PowerShell source.
    import os
    env = os.environ.copy()
    env['ITTOOLS_VERIFY_FILE'] = str(path)
    script = (
        "$s=Get-AuthenticodeSignature -LiteralPath $env:ITTOOLS_VERIFY_FILE; "
        "if ($s.Status -ne 'Valid' -or "
        "$s.SignerCertificate.Subject -notmatch '(^|,\\s*)O=Microsoft Corporation(,|$)') { exit 1 }"
    )
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                            env=env, capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError('Bộ cài chưa có chữ ký Microsoft hợp lệ; đã chặn thực thi.')


def save_windows_credential(target, username, password):
    """Use CredWriteW so passwords never appear in process command lines."""
    class Credential(ctypes.Structure):
        _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
                    ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
                    ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
                    ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)), ('Persist', wintypes.DWORD),
                    ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
                    ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]
    if not username or '\0' in username or '\0' in password:
        raise ValueError('Thông tin đăng nhập không hợp lệ.')
    secret = password.encode('utf-16-le')
    blob = (ctypes.c_ubyte * len(secret)).from_buffer_copy(secret)
    write = ctypes.WinDLL('advapi32', use_last_error=True).CredWriteW
    write.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    write.restype = wintypes.BOOL
    saved = False
    try:
        for kind in (2, 1):  # Domain password and generic credential.
            credential = Credential(Type=kind, TargetName=target, UserName=username,
                                    CredentialBlobSize=len(secret), CredentialBlob=blob, Persist=2)
            saved = bool(write(ctypes.byref(credential), 0)) or saved
        if not saved:
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        ctypes.memset(blob, 0, len(secret))


def protect_backup_bytes(data, decrypt=False):
    """DPAPI current-user encryption; no plaintext fallback on failure."""
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source, output = Blob(len(data), buffer), Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    if decrypt:
        operation = crypt.CryptUnprotectData
        second = None
    else:
        operation = crypt.CryptProtectData
        second = 'ITTools browser backup'
    operation.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p if decrypt else wintypes.LPCWSTR,
                          ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD,
                          ctypes.POINTER(Blob)]
    operation.restype = wintypes.BOOL
    if not operation(ctypes.byref(source), second, None, None, None, 1, ctypes.byref(output)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        free = ctypes.WinDLL('kernel32').LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        free(output.data)


def restrict_backup_folder(path):
    import csv
    result = subprocess.run(['whoami.exe', '/user', '/fo', 'csv', '/nh'],
                            capture_output=True, text=True, check=True)
    sid = next(csv.reader([result.stdout.strip()]))[1]
    if not re.fullmatch(r'S-1-[0-9-]+', sid):
        raise ValueError('Không xác định được SID của tài khoản sao lưu.')
    subprocess.run(['icacls.exe', str(path), '/inheritance:r', '/grant:r',
                    f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'],
                   capture_output=True, check=True)
