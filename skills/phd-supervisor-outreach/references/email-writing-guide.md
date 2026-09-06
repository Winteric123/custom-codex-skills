# 套磁信写作指南

## 邮件结构模板

以下为通用结构（源于一次真实 PhD 申请流程的提炼）。方括号为需替换的占位符。

```
Subject: Enquiry about PhD Supervision – [Full Name]

Dear Professor [Last Name],

[开头段] I am [Full Name], currently pursuing my [MSc/MD] at [University],
majoring in [field] with a [GPA / comprehensive score of __/100]. I am reaching
out to explore the possibility of joining your team as a PhD candidate in the
[spring/autumn] term of [year]. [一句与导师研究方向的真实匹配点。]

[正文段1 — 导师研究方向解读] 简述导师研究脉络（1–3 个真实方向），点出其中
一个你感兴趣、且与你能力/背景能衔接的缺口或机会。

[正文段2 — 研究计划] I would like to / I propose to / The question I want to
tackle is ... 提出一个从申请人已有工作自然延伸的具体研究设想（方法 + 预期产出）。

[结尾段] 个人优势（擅长什么，而非逐一列举论文）+ 实验/转化意愿（如适用）
+ 询问招生情况 + 附 CV。

Best regards,
[Full Name]

Postscript: Enclosed is my CV for your reference.
```

## 最佳实践（从真实流程提炼）

### 差异化
- 每位导师**单独一个文件**，命名 `01-导师姓.md` 便于排序。
- 开篇句式、提案动词（"I propose" / "I would like to build" / "The question I want to tackle"）、技能表述、结尾措辞彼此不同，避免让收件人察觉是模板批量发送。
- 差异化对照表可写在回复里，帮助用户审阅。

### 真实性
- **引用导师研究必须真实**。以用户提供的文件为准；缺漏时检索 PubMed/官网补充。绝不编造 PMID、论文标题或研究项目。
- 研究计划从申请人**已有工作自然延伸**（例如做过 STK11/LKB1 多组学 → 延伸到 osimertinib 耐药解析），而非凭空另起一个与履历无关的课题。

### 简洁
- 少空话套话，去掉 "It would be a great honor" 之类的堆砌。
- 默认**不提 PMID**；自然表述为 "your recent work on liquid biopsy" 即可。除非用户明确要求引用编号。

### 自我描述
- 精简为"擅长什么"（"I am proficient in R/Python for multi-omics analysis"），不要逐篇罗列论文。
- 诚实处理背景短板：如临床/生信背景想转实验，写法是「承认既往侧重 + 表达转化/实验意愿 + 已有基础实验室经历」，而非回避或夸大。

### 中英双语
- 用户要求双语时，英文在前，以 `---` 分隔，后接 `## 中文参考`。
- 中文忠实于英文原文，专业术语准确（oligoprogression=寡进展、fragmentomics=片段组学、super-enhancer=超级增强子、PDX=患者来源异种移植模型）。

### 标点与折行（纯文本邮件易踩坑）
- **英文正文避免 em dash（`—`）插入语**：纯文本邮件客户端会在空格处断行，`genes — A — shape` 会在破折号附近断开、看起来像分了几行。
  - 成对插入语 `— A —` → 圆括号 `(A)`；
  - 单边 `—` → 逗号或句号（如 `SBRT — and it is…` → `SBRT, and it is…`）。
  - 词内无空格的连字符（`end-to-end`、`FDG-PET/CT`、`machine-learning`）不会触发断行，可保留。
- 主题行中的 `—` 若会折行也一并处理；无空格、单行显示的主题行通常可保留。

### 审阅高亮
- 改动处用 `==...==` 包起来给用户 review，方便定位。
- 存草稿脚本会自动剥掉 `==`（`body.replace("==", "")`），不会混入邮件正文。

## 常见偏好开关（写作前确认）

| 维度 | 选项 |
|---|---|
| 入学时间 | spring / autumn + 年份 |
| 导师称谓 | Professor / Dr |
| 语言 | 纯英文 / 纯中文 / 中英双语 |
| 研究描述详细度 | 精简（只提擅长）/ 详细（列举论文） |
| 是否提 PMID | 否（默认）/ 是 |
| 差异化程度 | 高（默认）/ 统一模板 |
| 是否存草稿箱 | 否 / 是（需邮箱授权码） |

## 存草稿箱要点

- 通过 IMAP 将 `.md` 邮件追加到草稿箱（`\Draft`），**不直接发送**——用户补充收件人后手动发送更安全。
- 163 邮箱：`imap.163.com:993`，草稿箱文件夹显示名为 `&g0l6P3ux-`（UTF-7 编码），脚本会自动检测。
- **授权码 ≠ 登录密码**：需在邮箱设置里单独生成（163：设置 → POP3/SMTP/IMAP → 开启并生成授权码）。
- 授权码通过环境变量传入脚本，避免明文出现在命令行历史或对话日志中。
- 邮件 `From` 可预设为申请人姓名 + 邮箱；`X-Unsent: 1` 标记为草稿。
- 收件人 `To` 可只写邮箱、不带姓名（用户常要求如此）；`save_drafts_with_recipients.py` 支持 `--recipients-file`。
- **163 已知限制**：允许 `APPEND`（写）但拒绝 `SELECT`（读），返回 `SELECT Unsafe Login. Please contact kefu@188.com for help`。因此无法 IMAP 回读草稿核对；改用「与存草稿脚本一致」的本地解析打印，或让用户在网页/客户端肉眼确认。
- **存草稿箱前先经用户确认**；单封重写用 `--only <前缀>`，避免重复生成整批草稿。
- 从 markdown 提取：主题 = 首行 `**Subject:** ...`；正文 = 首个空行之后；双语时按 `---` 分隔剥离中文部分。

## 已知边界

- 目前通过 IMAP 只能"存草稿"，不能批量设置收件人（收件人字段需用户在网页/客户端补齐）。
- 如需"直接发送"，需改用 SMTP 且明确用户已授权发送行为——默认不做，避免误发。
