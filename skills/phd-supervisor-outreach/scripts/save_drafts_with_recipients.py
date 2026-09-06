#!/usr/bin/env python3
"""将套磁信英文部分通过 IMAP 存入邮箱草稿箱（不发送），并可选写入收件人（To）。

相比 save_drafts_imap.py 的增强：
  1. 支持 --recipients-file 写入 To 收件人字段；
  2. 支持 --only <前缀> 只写某一封（避免每次全量重写、重复生成草稿）；
  3. 自动剥掉正文/主题里的 "==" 审阅高亮标记；
  4. 解析逻辑与 save_drafts_imap.py 一致（首行 Subject、首个空行后为正文、
     --english-only 时在 "---" / "## 中文参考" 处截断）。

用法（163 邮箱）：
    $env:EMAIL_APP_PASSWORD = "授权码"
    python save_drafts_with_recipients.py --dir 套磁信 \
        --email applicant@example.com --imap-host imap.example.com \
        --recipients-file recipients.json --english-only

recipients.json 形如（键 = .md 文件名前两位前缀，值 = 收件人邮箱）：
    {"01": "professor1@example.edu", "02": "professor2@example.edu", "03": "professor3@example.edu"}

只写一封：追加 --only 03
"""
import argparse
import imaplib
import json
import os
import ssl
import sys
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate


def parse_email_file(path, english_only=False):
    """解析 .md -> (subject, body)。与 save_drafts_imap.py 约定一致。"""
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    if english_only:
        for sep in ("\n---\n", "\n## 中文参考", "\n## 中文"):
            idx = content.find(sep)
            if idx != -1:
                content = content[:idx]
                break

    lines = content.split("\n")
    subject = lines[0].strip()
    if subject.startswith("**Subject:**"):
        subject = subject[len("**Subject:**"):].strip()
    else:
        subject = subject.replace("**", "").strip()

    body_start = 2
    while body_start < len(lines) and lines[body_start].strip() == "":
        body_start += 1
    body = "\n".join(lines[body_start:]).strip()

    # 剥掉审阅用高亮标记，避免混入邮件正文
    body = body.replace("==", "")
    subject = subject.replace("==", "")
    return subject, body


def detect_drafts_folder(conn):
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
    files = sorted(f for f in os.listdir(directory) if f.lower().endswith(".md"))
    if not files:
        sys.exit(f"错误: 目录 {directory} 下没有 .md 文件")
    return files


def main():
    p = argparse.ArgumentParser(description="将套磁信 .md 存入 IMAP 草稿箱（可含收件人）")
    p.add_argument("--dir", required=True, help="存放 .md 邮件的目录")
    p.add_argument("--email", required=True, help="邮箱地址")
    p.add_argument("--imap-host", default="imap.163.com")
    p.add_argument("--imap-port", type=int, default=993)
    p.add_argument("--password", default=None, help="授权码；默认读环境变量 EMAIL_APP_PASSWORD")
    p.add_argument("--drafts-folder", default=None, help="草稿箱文件夹名；默认自动检测")
    p.add_argument("--from-name", default=None, help="From 显示名；默认取邮箱前缀")
    p.add_argument("--english-only", action="store_true", help="只保留英文正文")
    p.add_argument("--recipients-file", default=None, help="JSON：{前缀: 邮箱}；提供则写入 To")
    p.add_argument("--only", default=None, help="只处理文件名以该前缀开头的 .md")
    p.add_argument("--dry-run", action="store_true", help="只解析打印，不连接邮箱")
    args = p.parse_args()

    recipients = {}
    if args.recipients_file:
        with open(args.recipients_file, "r", encoding="utf-8") as fh:
            recipients = json.load(fh)

    parsed = []
    for fname in list_md_files(args.dir):
        key = fname[:2]
        if args.only and key != args.only:
            continue
        subject, body = parse_email_file(os.path.join(args.dir, fname), args.english_only)
        remail = recipients.get(key)
        parsed.append((fname, remail, subject, body))

    if not parsed:
        sys.exit("错误: 没有可处理的 .md 邮件（检查 --only 前缀）")

    from_name = args.from_name or args.email.split("@")[0]

    if args.dry_run:
        for fname, remail, subject, body in parsed:
            print(f"--- {fname} ---")
            print(f"Subject: {subject}")
            print(f"To: {remail or '(无)'}")
            print(f"From: {from_name} <{args.email}>")
            print(f"Body ({len(body)} chars): {body[:80].strip()}...")
            print()
        print(f"dry-run: {len(parsed)} 封已解析，未连接邮箱。")
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
    for fname, remail, subject, body in parsed:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = formataddr((from_name, args.email))
        if remail:
            msg["To"] = remail  # 仅邮箱地址，不带姓名
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["X-Unsent"] = "1"
        raw = msg.as_string()
        status, _ = conn.append(drafts_folder, "\\Draft", None, raw.encode("utf-8"))
        results.append((fname, remail, status == "OK"))

    conn.logout()

    ok = sum(1 for r in results if r[2])
    print(f"{ok}/{len(results)} 封已存入草稿箱 ({args.email} -> {drafts_folder})")
    for fname, remail, s in results:
        print(f"  [{'OK' if s else 'FAILED'}] {fname} -> {remail or '(无收件人)'}")
    if ok != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
