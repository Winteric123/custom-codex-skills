#!/usr/bin/env python3
"""将目录下的套磁信 .md 文件通过 IMAP 追加到邮箱草稿箱（不发送）。

用法示例（163 邮箱）:
    $env:EMAIL_APP_PASSWORD = "授权码"
    python save_drafts_imap.py --dir ceramic-emails --email you@163.com \
        --imap-host imap.163.com --english-only

授权码优先从环境变量 EMAIL_APP_PASSWORD 读取，也可用 --password 传入。
仅追加到草稿箱，不设置收件人、不发送。
"""

import argparse
import imaplib
import os
import ssl
import sys
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate


def parse_email_file(path, english_only=False):
    """解析 .md 文件 -> (subject, body)。

    约定：首行为 `**Subject:** <主题>`；正文从首个空行之后开始。
    english_only 时在 `---` 分隔符或 `## 中文参考` 处截断，只保留英文。
    """
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    if english_only:
        for sep in ("\n---\n", "\n## 中文参考", "\n## 中文"):
            idx = content.find(sep)
            if idx != -1:
                content = content[:idx]
                break

    lines = content.split("\n")
    subject_line = lines[0].strip()
    if subject_line.startswith("**Subject:**"):
        subject = subject_line[len("**Subject:**"):].strip()
    else:
        subject = subject_line.replace("**", "").strip()

    # 正文从首个空行之后开始
    body_start = 2
    while body_start < len(lines) and lines[body_start].strip() == "":
        body_start += 1
    body = "\n".join(lines[body_start:]).strip()

    return subject, body


def detect_drafts_folder(conn):
    """从 IMAP LIST 返回中自动定位草稿箱（含 \\Drafts 标记的文件夹）。"""
    status, folders = conn.list()
    if status != "OK":
        return None
    for line in folders:
        text = line.decode("latin-1", errors="replace")
        if "\\Drafts" in text:
            parts = text.split('"')
            if len(parts) >= 2:
                return parts[-2]
    return None


def list_md_files(directory):
    files = sorted(
        f for f in os.listdir(directory)
        if f.lower().endswith(".md")
    )
    if not files:
        sys.exit(f"错误: 目录 {directory} 下没有 .md 文件")
    return files


def main():
    p = argparse.ArgumentParser(description="将套磁信 .md 存入 IMAP 草稿箱")
    p.add_argument("--dir", required=True, help="存放 .md 邮件的目录")
    p.add_argument("--email", required=True, help="邮箱地址")
    p.add_argument("--imap-host", default="imap.163.com")
    p.add_argument("--imap-port", type=int, default=993)
    p.add_argument("--password", default=None,
                   help="授权码；默认读环境变量 EMAIL_APP_PASSWORD")
    p.add_argument("--drafts-folder", default=None,
                   help="草稿箱文件夹名；默认自动检测")
    p.add_argument("--from-name", default=None,
                   help="From 显示名；默认取邮箱前缀")
    p.add_argument("--english-only", action="store_true",
                   help="只保留英文正文，剥离中文参考部分")
    p.add_argument("--dry-run", action="store_true",
                   help="只解析并打印，不连接邮箱")
    args = p.parse_args()

    files = list_md_files(args.dir)
    parsed = []
    for fname in files:
        subject, body = parse_email_file(
            os.path.join(args.dir, fname), args.english_only)
        parsed.append((fname, subject, body))

    from_name = args.from_name or args.email.split("@")[0]

    if args.dry_run:
        for fname, subject, body in parsed:
            print(f"--- {fname} ---")
            print(f"Subject: {subject}")
            print(f"From: {from_name} <{args.email}>")
            print(f"Body ({len(body)} chars): {body[:80].strip()}...")
            print()
        print(f"dry-run: {len(parsed)} 封邮件已解析，未连接邮箱。")
        return

    password = args.password or os.environ.get("EMAIL_APP_PASSWORD")
    if not password:
        sys.exit("错误: 未提供授权码（--password 或环境变量 EMAIL_APP_PASSWORD）")

    context = ssl.create_default_context()
    conn = imaplib.IMAP4_SSL(args.imap_host, args.imap_port, ssl_context=context)
    conn.login(args.email, password)

    drafts_folder = args.drafts_folder or detect_drafts_folder(conn)
    if not drafts_folder:
        conn.logout()
        sys.exit("错误: 无法自动检测草稿箱文件夹，请用 --drafts-folder 显式指定")

    results = []
    for fname, subject, body in parsed:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = f"{from_name} <{args.email}>"
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["X-Unsent"] = "1"
        raw = msg.as_string()
        status, _ = conn.append(drafts_folder, "\\Draft", None,
                                raw.encode("utf-8"))
        results.append((fname, status == "OK"))

    conn.logout()

    ok = sum(1 for _, s in results if s)
    print(f"\n{ok}/{len(results)} 封已存入草稿箱 ({args.email} -> {drafts_folder})")
    for fname, s in results:
        print(f"  [{'OK' if s else 'FAILED'}] {fname}")
    if ok != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
