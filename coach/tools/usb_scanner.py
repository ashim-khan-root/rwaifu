#!/usr/bin/env python3
"""
USB Malware Scanner
Scans external USB drives for suspicious files, autorun exploits, double extensions,
hidden executables, and known malware indicators.

Usage:
  py -3 coach/tools/usb_scanner.py D:                    Quick scan
  py -3 coach/tools/usb_scanner.py D: --deep             Deep scan (content heuristics)
  py -3 coach/tools/usb_scanner.py D: --defender         Also run Windows Defender
  py -3 coach/tools/usb_scanner.py D: --quarantine       Move suspicious files to quarantine
  py -3 coach/tools/usb_scanner.py --list-drives         List removable drives
  py -3 coach/tools/usb_scanner.py D: --json             Output as JSON
"""

import os
import sys
import json
import stat
import hashlib
import datetime
import shutil
import subprocess
import textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

SUSPICIOUS_EXTENSIONS = {
    '.exe', '.scr', '.pif', '.com', '.cmd', '.bat',
    '.vbs', '.vbe', '.js', '.jse', '.ps1', '.psm1',
    '.wsf', '.wsh', '.jar', '.msi', '.msp', '.cpl',
}

SCRIPT_EXTENSIONS = {'.vbs', '.vbe', '.js', '.jse', '.ps1', '.psm1', '.wsf', '.wsh', '.bat', '.cmd'}

DOUBLE_EXTENSIONS = {
    '.pdf.exe', '.doc.exe', '.docx.exe', '.xls.exe', '.xlsx.exe',
    '.ppt.exe', '.pptx.exe', '.jpg.exe', '.jpeg.exe', '.png.exe',
    '.gif.exe', '.mp3.exe', '.mp4.exe', '.zip.exe', '.rar.exe',
    '.pdf.vbs', '.doc.vbs', '.docx.vbs', '.xls.vbs', '.xlsx.vbs',
    '.pdf.js', '.doc.js', '.docx.js', '.pdf.scr', '.doc.scr',
    '.pdf.com', '.doc.com', '.pdf.pif', '.doc.pif',
}

SUSPICIOUS_NAMES = {
    'autorun.inf', '~$auto', 'ntdelect.com', 'ntdelect.bat',
    'ravmon.exe', 'svchost.exe', 'lsass.exe', 'smss.exe',
    'winlogon.exe', 'csrss.exe', 'explorer.exe', 'rundll32.exe',
    'recycle.exe', 'recycler', 'recycled', 'system.exe',
    'system32.exe', 'boot.exe', 'msconfig.exe', 'regedit.exe',
    'cmd.exe', 'powershell.exe', 'taskmgr.exe',
}

KNOWN_RANSOMWARE_NOTES = {
    'readme.txt', 'readme.html', 'how_to_decrypt.txt', 'decrypt.txt',
    'help_desktop.txt', 'help_restore.txt', 'restore_files.txt',
    'recover.txt', '!!!readme!!!.rtf', 'readme_decrypt.txt',
    'decrypt_instructions.txt', 'how_to_recover.txt',
    'encrypted.txt', 'lock_screen.html', 'index.html',
}

SUSPICIOUS_AUTORUN_KEYWORDS = ['open=', 'action=', 'shell\\', 'useautoplay=', 'shellexecute=']


@dataclass
class Finding:
    path: str
    risk: str  # low, medium, high, critical
    category: str
    detail: str
    size: int = 0
    is_hidden: bool = False
    is_system: bool = False
    md5: str = ''


@dataclass
class ScanResult:
    drive: str
    timestamp: str
    total_files: int = 0
    total_dirs: int = 0
    findings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    defender_result: str = ''
    scan_time_seconds: float = 0.0


def get_removable_drives():
    drives = []
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        path = f'{letter}:\\'
        if os.path.exists(path):
            try:
                drive_type = subprocess.run(
                    ['powershell', '-Command', f'(Get-WmiObject Win32_LogicalDisk -Filter "DeviceID=\'{letter}:\'").DriveType'],
                    capture_output=True, text=True, timeout=10
                ).stdout.strip()
                if drive_type == '2':
                    drives.append(path)
            except Exception:
                if os.path.exists(os.path.join(path, 'autorun.inf')):
                    drives.append(path)
    return drives


def get_file_attributes(path):
    try:
        attrs = os.stat(path).st_file_attributes
        is_hidden = bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)
        is_system = bool(attrs & stat.FILE_ATTRIBUTE_SYSTEM)
        return is_hidden, is_system
    except Exception:
        return False, False


def check_autorun_inf(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
        is_hidden, is_system = get_file_attributes(filepath)
        suspicious = [kw for kw in SUSPICIOUS_AUTORUN_KEYWORDS if kw in content]
        if suspicious:
            findings.append(Finding(
                path=filepath,
                risk='high' if any('open=' in s for s in suspicious) else 'medium',
                category='autorun',
                detail=f'Suspicious autorun.inf entries: {", ".join(suspicious)}',
                size=os.path.getsize(filepath),
                is_hidden=is_hidden,
                is_system=is_system,
            ))
        elif is_hidden and is_system:
            findings.append(Finding(
                path=filepath,
                risk='low',
                category='autorun',
                detail='autorun.inf present (hidden + system) but no obvious malicious entries',
                size=os.path.getsize(filepath),
                is_hidden=is_hidden,
                is_system=is_system,
            ))
    except Exception as e:
        findings.append(Finding(
            path=filepath, risk='low', category='autorun',
            detail=f'Could not read autorun.inf: {e}',
        ))
    return findings


def check_double_extension(name_lower):
    for ext in DOUBLE_EXTENSIONS:
        if name_lower.endswith(ext):
            readable = [e for e in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                                     '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.zip', '.rar']
                        if ext.startswith(e)]
            true_type = ext.split('.')[-1]
            return True, f"Double extension: appears as '{readable[0] if readable else '?'}' but is actually .{true_type}"
    return False, None


def check_lnk_target(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        if content[:4] != b'\x4c\x00\x00\x00':
            return None
        cmd_start = content.find(b'cmd.exe')
        powershell = content.find(b'powershell')
        wscript = content.find(b'wscript')
        cscript = content.find(b'cscript')
        if cmd_start >= 0 or powershell >= 0 or wscript >= 0 or cscript >= 0:
            return 'LNK shortcut targets a shell/script executable'
        return None
    except Exception:
        return None


def quick_scan(path, findings):
    if not os.path.exists(path):
        return
    resolved = os.path.realpath(path)
    try:
        is_hidden, is_system = get_file_attributes(resolved)
        name = os.path.basename(resolved)
        name_lower = name.lower()
        ext = os.path.splitext(name)[1].lower()
        size = os.path.getsize(resolved)

        if is_hidden and ext in SUSPICIOUS_EXTENSIONS and size > 0:
            findings.append(Finding(
                path=resolved, risk='high', category='hidden_executable',
                detail=f'Hidden executable: {name}',
                size=size, is_hidden=is_hidden, is_system=is_system,
            ))

        is_double, desc = check_double_extension(name_lower)
        if is_double:
            findings.append(Finding(
                path=resolved, risk='critical', category='double_extension',
                detail=desc, size=size, is_hidden=is_hidden, is_system=is_system,
            ))

        if name_lower in SUSPICIOUS_NAMES:
            findings.append(Finding(
                path=resolved, risk='high', category='suspicious_name',
                detail=f'Suspicious filename: {name}',
                size=size, is_hidden=is_hidden, is_system=is_system,
            ))

        if name_lower in KNOWN_RANSOMWARE_NOTES:
            findings.append(Finding(
                path=resolved, risk='high', category='ransomware_note',
                detail=f'Possible ransomware note: {name}',
                size=size, is_hidden=is_hidden, is_system=is_system,
            ))

        if ext == '.lnk':
            lnk_result = check_lnk_target(resolved)
            if lnk_result:
                findings.append(Finding(
                    path=resolved, risk='high', category='suspicious_shortcut',
                    detail=lnk_result, size=size, is_hidden=is_hidden, is_system=is_system,
                ))

        if ext == '.inf':
            try:
                with open(resolved, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                if 'open=' in content or 'action=' in content:
                    findings.append(Finding(
                        path=resolved, risk='medium', category='suspicious_inf',
                        detail=f'INF file with open/action command: {name}',
                        size=size, is_hidden=is_hidden, is_system=is_system,
                    ))
            except Exception:
                pass

        if is_hidden and is_system and ext not in ('.inf', '.ini', '.pf') and size > 1024:
            if name.lower() not in ('desktop.ini', 'thumbs.db', 'index.dat', 'thumbs.db:encryptable'):
                findings.append(Finding(
                    path=resolved, risk='medium', category='hidden_system_file',
                    detail=f'Hidden + system file: {name}',
                    size=size, is_hidden=is_hidden, is_system=is_system,
                ))

    except (PermissionError, OSError):
        pass


def deep_scan(path, findings):
    if not os.path.exists(path):
        return
    resolved = os.path.realpath(path)
    try:
        is_hidden, is_system = get_file_attributes(resolved)
        name = os.path.basename(resolved)
        name_lower = name.lower()
        ext = os.path.splitext(name)[1].lower()
        size = os.path.getsize(resolved)

        if ext in SCRIPT_EXTENSIONS:
            try:
                with open(resolved, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                dangerous_patterns = []
                if 'createobject' in content and ('wscript.shell' in content or 'shell.application' in content):
                    dangerous_patterns.append('WScript.Shell COM object')
                if 'powershell' in content and ('-enc' in content or '-encodedcommand' in content):
                    dangerous_patterns.append('PowerShell encoded command')
                if '.downloadfile(' in content or '.downloadstring(' in content:
                    dangerous_patterns.append('Web download in script')
                if 'base64' in content and len(content) > 2000:
                    dangerous_patterns.append('Large base64-encoded blob in script')
                if dangerous_patterns:
                    findings.append(Finding(
                        path=resolved, risk='high', category='malicious_script',
                        detail=f'Suspicious script ({", ".join(dangerous_patterns)}): {name}',
                        size=size, is_hidden=is_hidden, is_system=is_system,
                    ))
            except Exception:
                pass

        if ext in SUSPICIOUS_EXTENSIONS and size < 2048 and not is_hidden:
            try:
                with open(resolved, 'rb') as f:
                    header = f.read(4)
                if header in (b'MZ\x90\x00', b'MZ\x00\x00'):
                    findings.append(Finding(
                        path=resolved, risk='medium', category='tiny_executable',
                        detail=f'Very small PE executable in root: {name} ({size} bytes)',
                        size=size, is_hidden=is_hidden, is_system=is_system,
                    ))
            except Exception:
                pass

        if is_hidden and not is_system and name.startswith('.'):
            findings.append(Finding(
                path=resolved, risk='low', category='hidden_dotfile',
                detail=f'Hidden dotfile: {name}',
                size=size, is_hidden=is_hidden, is_system=is_system,
            ))

    except (PermissionError, OSError):
        pass


def compute_md5(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read(65536)).hexdigest()
    except Exception:
        return ''


def run_defender_scan(drive):
    try:
        result = subprocess.run(
            ['powershell', '-Command', f'''
                Start-MpScan -ScanType Custom -ScanPath "{drive}" -ErrorAction SilentlyContinue
                $threats = Get-MpThreatDetection | Where-Object {{ $_.InitialDetectionTime -gt (Get-Date).AddMinutes(-30) }}
                if ($threats) {{
                    $threats | Format-Table -Property Resources, ThreatName, Severity -AutoSize | Out-String
                }} else {{
                    "No threats detected by Windows Defender"
                }}
            '''],
            capture_output=True, text=True, timeout=300
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Windows Defender scan timed out (5 min limit)"
    except Exception as e:
        return f"Windows Defender unavailable: {e}"


def quarantine_file(filepath, quarantine_dir):
    try:
        os.makedirs(quarantine_dir, exist_ok=True)
        src = os.path.realpath(filepath)
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = os.path.basename(src)
        dest = os.path.join(quarantine_dir, f'{ts}_{fname}')
        shutil.move(src, dest)
        return True, dest
    except Exception as e:
        return False, str(e)


def format_size(size):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))


def print_report(result):
    c_red = '\033[91m'
    c_yellow = '\033[93m'
    c_cyan = '\033[96m'
    c_green = '\033[92m'
    c_reset = '\033[0m'
    c_bold = '\033[1m'

    risk_colors = {
        'critical': c_red,
        'high': c_yellow,
        'medium': c_cyan,
        'low': c_green,
    }

    safe_print('')
    safe_print(f'{c_bold}{"=" * 60}{c_reset}')
    safe_print(f'{c_bold}  USB SCAN REPORT — {result.drive}{c_reset}')
    safe_print(f'{c_bold}{"=" * 60}{c_reset}')
    safe_print(f'  Time:       {result.timestamp}')
    safe_print(f'  Duration:   {result.scan_time_seconds:.1f}s')
    safe_print(f'  Files:      {result.total_files}')
    safe_print(f'  Dirs:       {result.total_dirs}')
    safe_print(f'  Findings:   {len(result.findings)}')

    if not result.findings:
        safe_print(f'\n  {c_green}{c_bold}✓ No suspicious files detected — drive appears clean.{c_reset}')
    else:
        by_risk = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for f in result.findings:
            by_risk[f.risk] = by_risk.get(f.risk, 0) + 1

        safe_print(f'\n  {c_bold}Risk Breakdown:{c_reset}')
        for level in ('critical', 'high', 'medium', 'low'):
            count = by_risk.get(level, 0)
            if count:
                color = risk_colors[level]
                safe_print(f'    {color}{level.capitalize():>8}{c_reset}: {count}')

    if result.findings:
        safe_print(f'\n  {c_bold}Findings:{c_reset}')
        safe_print(f'  {"-" * 58}')
        risks = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for f in result.findings:
            risks[f.risk].append(f)

        for level in ('critical', 'high', 'medium', 'low'):
            items = risks[level]
            if not items:
                continue
            color = risk_colors[level]
            for f in items:
                flags = ''
                if f.is_hidden and f.is_system:
                    flags = ' [H+S]'
                elif f.is_hidden:
                    flags = ' [H]'
                short_path = f.path[:80] + '...' if len(f.path) > 80 else f.path
                safe_print(f'  {color}{level.upper():>8}{c_reset} | {f.category:22s} | {short_path}')
                safe_print(f'  {"":8}   | {f.detail}')
                if f.size:
                    safe_print(f'  {"":8}   | Size: {format_size(f.size)}{flags}')
                safe_print('')

    if result.defender_result:
        safe_print(f'\n  {c_bold}Windows Defender:{c_reset}')
        safe_print(f'  {result.defender_result[:500]}')

    safe_print(f'{c_bold}{"=" * 60}{c_reset}\n')


def main():
    import time
    import argparse

    parser = argparse.ArgumentParser(
        description='USB Malware Scanner — scan external drives for suspicious files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
            Examples:
              py -3 coach/tools/usb_scanner.py D:
              py -3 coach/tools/usb_scanner.py D: --deep
              py -3 coach/tools/usb_scanner.py D: --defender
              py -3 coach/tools/usb_scanner.py D: --quarantine
              py -3 coach/tools/usb_scanner.py --list-drives
              py -3 coach/tools/usb_scanner.py D: --json
        ''')
    )
    parser.add_argument('drive', nargs='?', help='Drive path to scan (e.g. D:\\)')
    parser.add_argument('--deep', action='store_true', help='Deep scan with content heuristics')
    parser.add_argument('--defender', action='store_true', help='Also run Windows Defender on the drive')
    parser.add_argument('--quarantine', action='store_true', help='Move suspicious files to quarantine folder')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--list-drives', action='store_true', help='List removable drives')

    args = parser.parse_args()

    if args.list_drives:
        drives = get_removable_drives()
        if drives:
            print('Removable drives detected:')
            for d in drives:
                try:
                    label = subprocess.run(
                        ['powershell', '-Command',
                         f'(Get-WmiObject Win32_LogicalDisk -Filter "DeviceID=\'{d[0]}:\'").VolumeName'],
                        capture_output=True, text=True, timeout=5
                    ).stdout.strip()
                    label = f' ({label})' if label else ''
                    total, used, free = shutil.disk_usage(d)
                    print(f'  {d}{label} — {format_size(free)} free / {format_size(total)} total')
                except Exception:
                    print(f'  {d}')
        else:
            print('No removable drives detected.')
        return

    if not args.drive:
        parser.print_help()
        return

    drive = args.drive.upper().rstrip('/\\') + '\\'
    if not os.path.exists(drive):
        print(f'Error: Drive {drive} not found.')
        sys.exit(1)

    start = time.time()
    result = ScanResult(
        drive=drive,
        timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )

    quarantine_dir = ''
    if args.quarantine:
        quarantine_dir = os.path.join(os.path.dirname(__file__), '..', 'quarantine', f'usb_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}')

    safe_print(f'Scanning {drive}...')
    scanned_files = 0
    scanned_dirs = 0

    for root, dirs, files in os.walk(drive):
        try:
            for d in dirs[:]:
                if d.startswith('$Recycle') or d.startswith('System Volume'):
                    dirs.remove(d)
            scanned_dirs += len(dirs)
        except Exception:
            pass

        rel = os.path.relpath(root, drive)
        if rel == '.':
            for fname in files:
                fpath = os.path.join(root, fname)
                scanned_files += 1
                quick_scan(fpath, result.findings)
                if args.deep:
                    deep_scan(fpath, result.findings)
            if args.deep or args.quarantine:
                for dname in dirs:
                    dpath = os.path.join(root, dname)
                    scanned_dirs += 1
                    check_path = os.path.join(dpath, 'desktop.ini')
                    if os.path.exists(check_path):
                        quick_scan(check_path, result.findings)

    for root, dirs, files in os.walk(drive):
        try:
            for d in dirs[:]:
                if d.startswith('$Recycle') or d.startswith('System Volume'):
                    dirs.remove(d)
        except Exception:
            pass

        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                scanned_files += 1
                if os.path.relpath(fpath, drive).startswith('..'):
                    continue
                quick_scan(fpath, result.findings)
                if args.deep:
                    deep_scan(fpath, result.findings)
            except (PermissionError, OSError):
                continue

    result.total_files = scanned_files
    result.total_dirs = scanned_dirs

    auto_run_path = os.path.join(drive, 'autorun.inf')
    if os.path.exists(auto_run_path):
        result.findings.extend(check_autorun_inf(auto_run_path))

    if args.deep:
        for finding in result.findings:
            if finding.risk in ('high', 'critical'):
                finding.md5 = compute_md5(finding.path)

    if args.defender:
        safe_print('Running Windows Defender scan (may take a few minutes)...')
        result.defender_result = run_defender_scan(drive)

    result.scan_time_seconds = time.time() - start

    if args.quarantine and result.findings:
        quarantined = []
        for finding in result.findings:
            if finding.risk in ('high', 'critical'):
                success, dest = quarantine_file(finding.path, quarantine_dir)
                if success:
                    quarantined.append((finding.path, dest))
        if quarantined:
            safe_print(f'\nQuarantined {len(quarantined)} file(s) to {quarantine_dir}:')
            for src, dest in quarantined:
                safe_print(f'  {src}  ->  {dest}')

    if args.json:
        print(json.dumps({
            'drive': result.drive,
            'timestamp': result.timestamp,
            'duration_seconds': result.scan_time_seconds,
            'total_files': result.total_files,
            'total_dirs': result.total_dirs,
            'findings_count': len(result.findings),
            'findings': [
                {
                    'path': f.path,
                    'risk': f.risk,
                    'category': f.category,
                    'detail': f.detail,
                    'size': f.size,
                    'is_hidden': f.is_hidden,
                    'is_system': f.is_system,
                    'md5': f.md5,
                }
                for f in result.findings
            ],
            'defender_result': result.defender_result,
        }, indent=2))
    else:
        print_report(result)


if __name__ == '__main__':
    main()
