---
name: phd-supervisor-outreach
description: 为博士/硕士申请批量生成个性化导师套磁信（supervision inquiry / cold email），并可选通过 IMAP 存入邮箱草稿箱。适用场景：用户提供导师名单 + 个人 CV/背景 + 模板，要求为每位导师撰写邮件、排除指定导师、中英双语、差异化措辞、存草稿箱。触发词：套磁信、陶瓷信、导师意向信、PhD supervision、supervisor outreach、cold email、博士申请邮件、导师邮件。
---

# phd-supervisor-outreach · 导师套磁信生成

为科研申请者（PhD/MSc）批量生成**个性化**导师套磁信，每位导师一个独立文件，并（可选）通过 IMAP 存入邮箱草稿箱。

## 输入清单

动笔前向用户确认并收集：

1. **申请人背景**：全名、学校、专业、学位、成绩（GPA 或综测，如 84.8/100）、入学时间（如 autumn 2027）
2. **导师名单**：姓名 + 研究方向资料（用户上传文件，或需检索）
3. **排除名单**：明确不生成哪些导师（如已另有安排者）
4. **模板**（可选）：用户提供的邮件模板结构
5. **偏好**：语言（英/中/双语）、是否存草稿箱、导师称谓（Professor/Dr）、每封信差异化程度

## 工作流程

1. 读取全部输入文件（导师资料、CV）。找不到时用 `shell` 在 `.wisp/artifacts` 下定位并读取。
2. 确认关键参数：入学学期、课题切入点、称谓、输出格式、语言、是否投递草稿箱。**不确定就问，不要猜。**
3. 排除名单中的导师。
4. 为每位导师确定真实研究方向：以用户文件为准；缺漏时检索 PubMed / 机构官网补充。**严禁编造 PMID、论文或研究内容。**
5. 逐位撰写，每位导师一个独立 `.md` 文件（命名如 `01-导师姓.md`）。
6. （可选）运行 `scripts/save_drafts_with_recipients.py` 存草稿箱（支持写入收件人、单封重写、去审阅高亮）。
7. **存草稿箱前先与用户确认**；每次只重写用户指定需要更新的那一封（`--only`），避免重复生成整批草稿。
8. 完成后**列出全部生成/修改文件及路径**（本项目要求）。

## 写作结构

完整模板与最佳实践见 `references/email-writing-guide.md`。核心三段式：

- **开头**：身份 + 成绩 + 来意 + 与导师研究方向的匹配
- **正文**：解读导师研究的可行性 + 提出从申请人已有工作**自然延伸**的研究计划
- **结尾**：个人优势 + 询问招生 + 附 CV

## 存草稿箱

两个脚本，按需选择：

- `scripts/save_drafts_imap.py`：原始脚本，仅存草稿、不写收件人。
- `scripts/save_drafts_with_recipients.py`：**推荐**，支持写收件人（To）、单封重写、去审阅高亮。

```powershell
# 授权码通过环境变量传入，避免明文写入脚本或对话日志
$env:EMAIL_APP_PASSWORD = "你的邮箱授权码"
python .wisp/skills/phd-supervisor-outreach/scripts/save_drafts_with_recipients.py `
  --dir 套磁信 `
  --email applicant@example.com `
  --imap-host imap.163.com `
  --recipients-file recipients.json `
  --english-only
```

- `--recipients-file recipients.json`：`{"01": "professor@example.edu", ...}`，键为 `.md` 文件名前两位前缀，值为收件人邮箱；提供则把邮箱写入 `To`（仅邮箱、不带姓名）。
- `--only 03`：只重写文件名以 `03` 开头的那一封，避免每次全量重写、重复生成草稿。
- 脚本自动剥掉正文/主题中的 `==` 审阅高亮标记。
- 自动检测草稿箱文件夹（163 / QQ / Gmail 等均支持），也可用 `--drafts-folder` 显式指定。

**163 已知限制**：163 允许 `APPEND`（写草稿）但会拒绝 `SELECT`（读草稿），返回 `SELECT Unsafe Login...`。因此**无法用 IMAP 回读草稿核对**；要核对时用「与存草稿脚本完全一致的解析逻辑」在本地解析 `.md` 打印最终主题/正文，或让用户在网页/客户端肉眼确认。

## 关键约束

- 每位导师**单独文件**，词汇与句式彼此差异化，避免模板化痕迹
- 不堆砌 PMID（除非用户要求）；自然提及研究内容即可
- 研究计划必须从申请人已有工作延伸，不能凭空另起炉灶
- 诚实处理背景短板（如临床/生信背景想转实验——承认既往侧重 + 表达转化/实验意愿）
- 简洁直接，少空话套话
- **英文正文避免 em dash（`—`）插入语**：纯文本邮件会在空格处断行，`— A —` 会显得像分行。优先改圆括号 `(A)`；单边 `—` 改逗号或句号。详见 `references/email-writing-guide.md`
- **改动先高亮再确认**：给用户 review 时用 `==...==` 包住改动处，存草稿脚本会自动剥掉 `==`，不会混入正文
- **存草稿箱前先经用户确认**，不擅自写入

## Scripts

- `scripts/save_drafts_imap.py` — 存草稿（不写收件人）
- `scripts/save_drafts_with_recipients.py` — 存草稿 + 收件人 + 单封重写 + 去高亮

## References

- `references/email-writing-guide.md` — 完整模板、最佳实践、常见偏好开关
