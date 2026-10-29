"""Launch the pinned, unmodified MIT FluentCleaner Modern distribution."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

VERSION = '26.09.01'
RUNTIME_URL = 'https://aka.ms/windowsappsdk/2.0/2.0.1/windowsappruntimeinstall-x64.exe'
_process = None


def protect_host_runtime():
    """Preserve existing cleaner settings while excluding the host's live files."""
    settings_path = Path(os.environ['APPDATA']) / 'FluentCleaner' / 'settings.json'
    settings = json.loads(settings_path.read_text(encoding='utf-8-sig')) if settings_path.exists() else {}
    protected = [Path(os.environ['LOCALAPPDATA']) / 'ITToolSAGSCXR']
    if getattr(sys, 'frozen', False):
        protected.append(Path(sys._MEIPASS))
    exclusions = settings.setdefault('GlobalExclusions', [])
    for folder in protected:
        rule = 'PATH|' + str(folder.resolve())
        if rule.lower() not in {str(value).lower() for value in exclusions}:
            exclusions.append(rule)
    settings['GlobalExclusionsEnabled'] = True
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    fd, pending = tempfile.mkstemp(prefix='.ittools-', dir=settings_path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(settings, stream, ensure_ascii=False, indent=2)
        os.replace(pending, settings_path)
    finally:
        if os.path.exists(pending):
            os.unlink(pending)


def bundle_directory():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    return root / 'vendor' / 'fluentcleaner'


def verify_files(directory, manifest):
    root = Path(directory).resolve()
    for name, digest in manifest['files'].items():
        target = (root / name).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError('Thiếu hoặc sai đường dẫn bộ FluentCleaner.')
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('FluentCleaner đã thay đổi hoặc bị hỏng; cần khôi phục bộ cài gốc.')
    expected = {name.lower() for name in manifest['files']}
    for target in root.rglob('*'):
        if target.is_file() and target.suffix.lower() in ('.exe', '.dll'):
            if target.relative_to(root).as_posix().lower() not in expected:
                raise ValueError('Có file thực thi ngoài bản phát hành FluentCleaner đã duyệt.')


def launch():
    global _process
    if sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64'):
        return {'success': False, 'message': 'Bản tích hợp này yêu cầu Windows x64.'}
    if _process is not None and _process.poll() is None:
        return {'success': True, 'message': 'FluentCleaner đang mở. Hãy chuyển sang cửa sổ FluentCleaner.'}
    try:
        protect_host_runtime()
        bundle = bundle_directory()
        manifest = json.loads((bundle / 'release-manifest.json').read_text(encoding='utf-8'))
        verify_files(bundle, manifest)
        # Persist outside PyInstaller's extraction folder so closing IT Tool does
        # not remove files still needed by the separate cleaner window.
        cache = Path(os.environ['LOCALAPPDATA']) / 'ITToolSAGSCXR' / 'tools' / 'FluentCleaner' / VERSION
        if not cache.exists():
            cache.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='prepare-', dir=cache.parent) as pending:
                staged = Path(pending) / VERSION
                shutil.copytree(bundle, staged)
                verify_files(staged, manifest)
                staged.rename(cache)
        verify_files(cache, manifest)
        _process = subprocess.Popen([str(cache / 'FCleaner.exe')], cwd=str(cache), shell=False)
        try:
            code = _process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return {'success': True, 'message': 'Đã mở FluentCleaner. Chọn mục cần quét, xem kết quả rồi mới dọn dẹp.'}
        _process = None
        return {'success': code == 0, 'message':
                'FluentCleaner đã đóng.' if code == 0 else
                f'FluentCleaner không khởi động được (mã {code}). Kiểm tra Windows App Runtime 2.0.1 x64.',
                'runtime_url': RUNTIME_URL}
    except Exception as exc:
        return {'success': False, 'message': f'Không mở được FluentCleaner: {exc}'}
