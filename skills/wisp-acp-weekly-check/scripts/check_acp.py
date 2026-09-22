"""Read Wisp's configured ACP packages and compare with the official npm latest tag."""
import argparse
from contextlib import closing
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request

PACKAGES = {
    '@agentclientprotocol/codex-acp': None,
    '@agentclientprotocol/claude-agent-acp': None,
    '@zed-industries/codex-acp': '@agentclientprotocol/codex-acp',
}
LABELS = {
    'up_to_date': '已是最新稳定版',
    'update_available': '有更新',
    'preview': '当前为预发布版本，需单独判断',
    'ahead_of_latest': '本地版本高于官方 latest，需核实渠道',
    'migration_required': '旧包需要迁移',
    'unknown': '无法验证',
}


def read_profiles(database):
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)) as db:
        row = db.execute('SELECT value FROM settings WHERE key=?', ('acp_agent_profiles',)).fetchone()
    if row and not isinstance(row[0], str):
        raise ValueError('Unsupported ACP profile settings value')
    profiles = json.loads(row[0]) if row else []
    if not isinstance(profiles, list):
        raise ValueError('Unsupported ACP profile schema')
    return profiles


def package_for_entry(entry):
    """Accept only an entrypoint declared by a recognized package's bin field."""
    entry = entry.resolve()
    for parent in list(entry.parents)[:7]:
        manifest = parent / 'package.json'
        if not manifest.is_file():
            continue
        data = json.loads(manifest.read_text(encoding='utf-8-sig'))
        if not isinstance(data, dict):
            raise ValueError('Unsupported package manifest schema')
        if data.get('name') not in PACKAGES:
            continue
        bins = data.get('bin', {})
        if not isinstance(bins, (str, dict)):
            raise ValueError('Unsupported package bin schema')
        values = [bins] if isinstance(bins, str) else list(bins.values())
        if not all(isinstance(value, str) for value in values):
            raise ValueError('Unsupported package entrypoint schema')
        if any((parent / value).resolve() == entry for value in values) and entry.is_file():
            return data['name'], data.get('version'), str(manifest)
    return None


def locate_package(profile):
    command = profile.get('command', '')
    args = profile.get('args', [])
    if not isinstance(command, str) or not isinstance(args, list):
        raise ValueError('Unsupported command schema')
    path = Path(os.path.expandvars(command))
    if not path.is_absolute():
        # This process's PATH need not equal the PATH inherited by running Wisp.
        hint = shutil.which(command)
        raise ValueError('Wisp uses a PATH-relative command; confirm its absolute path in Settings -> Models -> ACP Agents' + (' (candidate found)' if hint else ''))
    if not path.is_file():
        raise ValueError('Configured executable is missing')
    if path.stem.lower() in ('npx', 'npm', 'bun', 'uvx'):
        raise ValueError('Dynamic package launcher: installed version cannot be established without executing/resolving it')
    if path.stem.lower() == 'node':
        if not args or not isinstance(args[0], str) or not Path(args[0]).is_absolute():
            raise ValueError('Node entrypoint is not an absolute path')
        found = package_for_entry(Path(args[0]))
    elif path.suffix.lower() == '.cmd':
        wrapper = path.read_text(encoding='utf-8-sig')
        # Standard Windows npm shim: inspect its literal %dp0% entrypoint, never run it.
        entries = re.findall(r'"%dp0%[\\/]([^"\r\n]+)"', wrapper, flags=re.I)
        found_set = set()
        for relative in entries:
            if relative.lower().startswith('node_modules\\') or relative.lower().startswith('node_modules/'):
                found = package_for_entry(path.parent / relative.replace('\\', '/'))
                if found:
                    found_set.add(found)
        if len(found_set) != 1:
            raise ValueError('Wrapper has no unique recognized ACP package entrypoint')
        found = found_set.pop()
    else:
        found = package_for_entry(path)
    if not found:
        raise ValueError('No supported ACP package manifest matches the configured executable')
    return found


def latest_version(package):
    url = 'https://registry.npmjs.org/' + urllib.parse.quote(package, safe='') + '/latest'
    request = urllib.request.Request(url, headers={'User-Agent': 'wisp-acp-weekly-check/1', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)
    if not isinstance(data, dict) or data.get('name') != package or not isinstance(data.get('version'), str):
        raise ValueError('Official registry returned unexpected package metadata')
    return data['version'], url


def parse_semver(value):
    match = re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?', value or '')
    if not match:
        raise ValueError('Unsupported version format')
    return tuple(int(match[i]) for i in (1, 2, 3)), match[4]


def compare_versions(installed, latest):
    current_numbers, current_preview = parse_semver(installed)
    latest_numbers, latest_preview = parse_semver(latest)
    if latest_preview:
        raise ValueError('Official latest tag points to a prerelease; stable status unverified')
    if current_preview:
        return 'preview'
    if current_numbers == latest_numbers:
        return 'up_to_date'
    return 'update_available' if current_numbers < latest_numbers else 'ahead_of_latest'


def check_profile(profile, fetch=latest_version):
    result = {'label': profile.get('label', 'Unnamed ACP'), 'command': profile.get('command'), 'status': 'unknown'}
    try:
        package, version, manifest = locate_package(profile)
        result.update(package=package, installed_version=version, manifest=manifest)
        target = PACKAGES[package] or package
        result['official_source'] = 'https://registry.npmjs.org/' + urllib.parse.quote(target, safe='') + '/latest'
        if PACKAGES[package]:
            result.update(status='migration_required', replacement_package=target)
        latest, source = fetch(target)
        result.update(latest_version=latest, official_source=source)
        if not PACKAGES[package]:
            result['status'] = compare_versions(version, latest)
    except urllib.error.HTTPError as exc:
        result['error'] = 'Official registry HTTP ' + str(exc.code)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, KeyError) as exc:
        # Do not print configuration values, credentials, or proxy URLs from exception messages.
        result['error'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__ + ': version could not be verified'
    return result


def build_report(database, fetch=latest_version):
    report = {'checked_at': dt.datetime.now().astimezone().isoformat(timespec='seconds'), 'database': str(database), 'profiles': []}
    try:
        profiles = read_profiles(database)
        if not profiles:
            report['error'] = 'No ACP profiles configured; nothing could be verified'
        cache = {}
        def cached_fetch(package):
            if package not in cache:
                try:
                    cache[package] = fetch(package)
                except Exception as exc:
                    cache[package] = exc
            if isinstance(cache[package], Exception):
                raise cache[package]
            return cache[package]
        for profile in profiles:
            if isinstance(profile, dict):
                report['profiles'].append(check_profile(profile, cached_fetch))
            else:
                report['profiles'].append({'label': 'Invalid profile', 'status': 'unknown', 'error': 'Unsupported profile schema'})
    except (OSError, sqlite3.Error, ValueError) as exc:
        report['error'] = type(exc).__name__ + ': Wisp ACP settings could not be read'
    report['all_up_to_date'] = bool(report['profiles']) and all(p['status'] == 'up_to_date' and not p.get('error') for p in report['profiles'])
    return report


def markdown(report):
    def cell(value):
        return str(value if value is not None else '未知').replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    lines = ['# Wisp ACP 每周版本检查', '', '检查时间：' + report['checked_at'], '',
             '结论：' + ('所有已配置适配器均为最新稳定版。' if report['all_up_to_date'] else '存在更新、渠道差异或无法验证的项目，请查看下表。'), '',
             '| ACP | 包 | 已安装 | 官方 latest | 状态 |', '|---|---|---|---|---|']
    for item in report['profiles']:
        lines.append('| ' + ' | '.join(cell(v) for v in (item['label'], item.get('package'), item.get('installed_version'), item.get('latest_version'), LABELS[item['status']])) + ' |')
    if report.get('error'):
        lines += ['', '检查失败：' + report['error']]
    for item in report['profiles']:
        lines += ['', '## ' + cell(item['label'])]
        for key, label in [('command', '启动程序'), ('manifest', '本机版本来源'), ('official_source', '官方来源'), ('replacement_package', '迁移目标'), ('error', '说明')]:
            if item.get(key):
                lines.append('- ' + label + '：' + cell(item[key]))
    lines += ['', '仅检查已配置 ACP 适配器的磁盘安装版本；未启动适配器、未升级软件。正在运行的会话可能仍使用启动时加载的版本。',
              'Wisp 应用、ACP 协议、适配器与底层 Codex/Claude 的版本分别管理。本报告不代表底层模型或 CLI 已更新。', '']
    return '\n'.join(lines)


def save_report(report, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    contents = {'json': json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'md': markdown(report)}
    for extension, content in contents.items():
        (output_dir / (stamp + '.' + extension)).write_text(content, encoding='utf-8')
        temporary = output_dir / ('latest.' + extension + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(output_dir / ('latest.' + extension))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_db = Path(os.environ.get('APPDATA', str(Path.home()))) / 'science.wisp-science/wisp-science/wisp.sqlite'
    parser.add_argument('--database', type=Path, default=default_db)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.database)
    save_report(report, args.output_dir)
    if sys.stdout is not None:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    # Updates are a successful check; unverified results are a failed check.
    return 2 if report.get('error') or any(p['status'] == 'unknown' or p.get('error') for p in report['profiles']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
