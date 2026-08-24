# AI Video Workflow

一个面向 Codex 的、平台无关的视频复刻与生成规划 skill。

它把参考图、参考视频、广告、短视频或完整脚本，整理成可审计、可替换执行器的工作流：先核验素材，再建立镜头/台词/叙事账本，明确替换范围，生成完整的逐镜 Prompt，按连续场景拆分片段，并在每段验收后用真实尾帧衔接下一段。

这个仓库提供的是 Codex skill 和配套校验脚本，不是视频生成模型，也不绑定某个网站、模型、API 或供应商。实际生成前，仍然需要用户选择并核验可用的执行器。

## 适用场景

- 参考视频、广告、短视频的结构化复刻和改写
- 保留剧情节奏，替换人物、服装、场景、产品、道具、品牌或 CTA
- 从完整脚本生成镜头表、台词表、场景参考图方案和视频 Prompt
- 长脚本分段生成，以及 `A -> 尾帧 -> B -> 尾帧 -> C` 的连续性管理
- 在冻结核心脚本的前提下制作可归因的场景、服装或摄影变体
- 有对白、旁白、唇形同步、环境音、音效或字幕要求的视频方案
- 仅做拉片分析、提示词打包，或在用户明确授权后执行实际生成

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 原片账本 | 建立镜头、台词和叙事三份稳定账本；看不清或听不清的内容标为 `待确认` |
| 替换矩阵 | 将人物、场景、服装、产品、品牌、台词、声音和 CTA 标记为保留、替换、删除或待确认 |
| 完整 Prompt | 每个镜头和每个片段都输出可独立复制的完整 Prompt，不用“同上”或差异补丁 |
| 对白交付 | 只要有说话，就交付完整可朗读台词、语言变体、表演、时间、声音路径、唇形同步和字幕计划 |
| 变体隔离 | 从同一份冻结 `core_script` 独立生成变体，避免上一个变体的改动污染下一个变体 |
| 场景锁定 | 用实际全景参考图固定人物、服装、道具、空间布局、光线和行动路线 |
| 尾帧接力 | 前段验收通过后提取真实尾帧，作为同场景下一段的首帧输入 |
| 能力核验 | 在生成前核验执行器是否支持参考图、首帧、多参考、时长、画幅、声音和结果回传 |
| 状态证据 | 区分“Prompt 已写”“任务已提交”“结果可查看”“片段验收通过”等状态，不夸大完成度 |

## 默认创作基线

以下默认值只作用于用户没有另行指定的新生成或改写内容。用户明确要求、已确认的 `core_script` 和可验证的原片事实优先级更高。

- **地域**：欧美地区，默认采用北美或西欧的真人选角、建筑、街道、服装、道具和社会语境。
- **Prompt 语言**：无论输入是参考图、参考视频、广告链接、脚本还是文字描述，最终生成 Prompt 的可读正文统一使用简体中文。
- **对白语言**：最终口播统一使用英语；需要口音时明确写 `en-US`、`en-GB` 等语言变体。英文只保留在实际口播台词和与其逐字一致的字幕文本中。
- **字幕**：只要有口播、对白、旁白或画外音，强制显示字幕；字幕位于画面下方安全区，白色文字内填充、黑色描边。
- **公众人物/IP**：参考中出现公众人物、虚构角色、系列、品牌或 Logo 时，只能转译为去标识化的原创角色；生成 Prompt 不写姓名、角色名、品牌标识或直接模仿要求。
- **色彩**：丰富、鲜艳、层次清楚，中高饱和但不过曝、不溢色，肤色自然并保留阴影细节。
- **真人摄影**：参考奥斯卡级和成熟好莱坞叙事摄影的通用方法，将其落到焦段、景别、机位、调度、运镜、布光、曝光、色彩和质感参数。
- **导演参考边界**：可以抽取深焦调度、主观手持、精确正反打、广角近距离、长焦压缩、负空间或实景动机光等可执行特征；不直接复制在世导演的签名风格，也不只写“电影感”或导演姓名。

## 工作模式

在开始时先明确模式，不擅自扩大执行范围：

| 模式 | 适用情况 | 默认交付 |
| --- | --- | --- |
| `analysis_only` | 只拉片、提炼结构或诊断 | 原片账本、问题清单和待确认项；不生成新台词 |
| `prompt_package` | 需要完整提示词但不提交生成 | 参数摘要、逐镜 Prompt、分段 Prompt、参考图方案和尾帧依赖 |
| `variant_package` | 在冻结核心脚本后制作多个变体 | 核心脚本、允许/禁止变化轴、变体矩阵和每个变体的完整 Prompt |
| `execute` | 用户已确认方案并授权实际生成 | 能力核验、参考图、串行片段生成、尾帧交接和验收记录 |

### Prompt 语言分层

“参考内容是什么语言”与“最终 Prompt 用什么语言”是两件事。原片账本可以保留原始语言的可验证转录，方便审计；但交给图像/视频生成器的参考图 Prompt、视频 Prompt、分段 Prompt、镜头描述、摄影参数、声音说明和负面约束都必须用简体中文。唯一的自然语言英文是人物实际说出的英文口播，以及与口播逐字一致的英文字幕。

只要有口播，完整 Prompt 必须同时出现以下内容：

```text
口播台词："<English spoken line>"
字幕：开启；字幕文本："<与口播逐字一致的英文台词>"；位置：画面下方安全区；样式：白色文字内填充，黑色描边。
```

参考 Prompt 中较早的“不要字幕”不能覆盖这条规则。没有口播的镜头才可以关闭字幕，除非用户另有明确要求。

### 公众人物和 IP 去标识化

本 skill 不把参考素材中的身份直接复制进生成提示词。原片账本可以记录可验证的来源身份用于审计，但所有交给图像/视频生成器的 Prompt、负面约束、场景参考图 Prompt、变体 Prompt 和分段 Prompt，都必须使用原创、去标识化的角色描述。

禁止在生成 Prompt 中出现：公众人物或演员姓名、虚构角色名、系列/IP 名称、品牌名、商标、Logo、专属口号、招牌服装标志、可识别面孔、声音模仿或“像某人/某人风格/inspired by 某人”等表述。

允许保留可迁移的高层特征，例如年龄段、发型轮廓、脸部几何、体型、服装色彩与廓形、姿态、表情、角色能量、环境氛围和通用摄影参数，并补充明确的安全边界：

```text
原创成年女性角色，短发、清晰的面部几何、鲜艳的服装配色和自信但亲切的表演；不使用可识别公众人物面孔、声音、Logo、商标或专属台词。
```

如果身份边界不清，先停在确认门补齐原创角色设定，不得把来源身份直接传给生成器。

## 安装

### 方式一：直接告诉 Codex

在 Codex 中发送：

```text
请从 https://github.com/Nikoce/AI-video-workflow 安装一个 skill，安装名为 ai-video-workflow。
安装完成后告诉我实际安装路径，并验证 SKILL.md 是否存在。
```

### 方式二：使用 skill-installer 脚本

Windows PowerShell 示例：

```powershell
$installer = Join-Path $env:USERPROFILE '.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py'
py $installer --repo Nikoce/AI-video-workflow --path . --name ai-video-workflow
```

如果系统没有 `py` 命令，可以将 `py` 换成 `python`。安装后，skill 通常位于：

```text
%USERPROFILE%\.codex\skills\ai-video-workflow
```

安装完成后重新开启一个 Codex 对话，或在下一轮对话中使用它。

### 已安装旧版本时

旧版安装目录通常没有 `.skill-install.json`，安装器无法可靠推断它原来的 GitHub 来源。因此，要让旧版本纳入新版本登记和后台更新，通常需要：

1. 先备份 `ai-video-workflow` 目录中有价值的本地修改。
2. 移除旧目录 `C:\Users\<用户名>\.codex\skills\ai-video-workflow`。
3. 按上面的方式重新安装。
4. 检查新目录中是否生成 `.skill-install.json`。

不要在没有备份的情况下删除包含本地定制内容的目录。

仅删除这个 skill 的精确目录时，可以使用：

```powershell
$skillDir = Join-Path $env:USERPROFILE '.codex\skills\ai-video-workflow'
if (Test-Path -LiteralPath $skillDir) {
    Remove-Item -LiteralPath $skillDir -Recurse -Force
}
```

## 更新机制

仓库推送新提交不会自动覆盖其他人的本地 skill。自动更新需要两部分同时满足：

1. 本地安装器支持更新登记和后台检查。
2. 该 skill 已经通过支持元数据的安装器重新安装过。

后台更新能力属于每台电脑上的 Codex `skill-installer`，不会因为拉取本仓库就自动出现在其他人的系统安装器中。如果安装器不认识 `--update-all` 或 `--enable-background`，它仍然可以安装当前仓库版本，但不会自动登记或后台更新；需要先更新本地的 system skill-installer。

支持后台更新的安装器会在每次成功安装后记录：

- GitHub `owner/repo/ref/path`
- 安装时的提交版本
- 安装内容哈希
- 最后检查、最后更新时间和错误信息

常用命令：

```powershell
$installer = Join-Path $env:USERPROFILE '.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py'

# 更新指定 skill
py $installer --update ai-video-workflow

# 更新所有已登记 skill
py $installer --update-all

# 只检查是否有更新，不修改本地文件
py $installer --check-updates

# 启用 Windows 后台检查，默认建议每 6 小时一次
py $installer --enable-background --interval-hours 6

# 关闭后台检查
py $installer --disable-background
```

新安装默认尝试创建 Windows Task Scheduler 任务；使用 `--no-background` 可以在安装时跳过。后台任务只检查已登记的 skill，不会为没有来源元数据的旧目录猜测仓库地址。

更新时如果发现本地文件已经被手动修改，更新器会跳过该 skill，不直接覆盖用户内容。替换失败时会恢复旧目录，并在 `$CODEX_HOME/skill-installer/backups/` 保留时间戳备份。后台日志位于：

```text
$CODEX_HOME\skill-installer\background-update.log
```

## 推荐使用方式

### 1. 只做拉片分析

```text
请使用 ai-video-workflow 对这个本地参考视频做 analysis_only：
- 只分析，不上传、不生成；
- 输出镜头账本、台词账本、叙事账本和待确认项；
- 不确定的画面或对白必须标记为“待确认”。
```

### 2. 输出完整提示词包

```text
请使用 ai-video-workflow 做 prompt_package：
- 保留原片剧情节奏和 CTA；
- 将人物和场景替换为我指定的版本；
- 未指定时使用欧美地区、英文对白、丰富鲜艳但不溢色的色彩；
- 真人镜头把好莱坞成熟摄影方法展开成具体焦段、机位、运镜、布光和构图参数；
- 只输出完整方案，不提交外部生成。
```

### 3. 制作多个变体

```text
请使用 ai-video-workflow 做 variant_package：
- 先冻结 core_script；
- 剧情顺序、台词、产品主张和 CTA 不变；
- 只允许改变 setting、wardrobe、camera_style；
- 每个变体独立输出完整、可复制的视频 Prompt；
- 不要只给差异表，不要使用“同上”。
```

### 4. 实际执行生成

```text
请使用 ai-video-workflow 做 execute。
先完成执行器能力核验和完整方案确认，确认前不要上传素材、提交任务或消耗额度。
确认后按场景参考图 -> A -> 验收 -> A 尾帧 -> B 的顺序串行执行。
```

## 标准工作流

流程状态如下：

```text
INTAKE
  -> PREFLIGHT
  -> ANALYZE
  -> REWRITE
  -> VARIANT（如需要）
  -> SEGMENT
  -> CAPABILITY
  -> REVIEW
  -> REFERENCE
  -> GENERATE_SEGMENT
  -> HANDOFF
  -> GENERATE_SEGMENT ...
  -> ACCEPT
```

### INTAKE：固定需求

记录用户原话、参考素材、目标时长、画幅、分辨率、地域、对白语言、色彩、真人摄影基线、必须保留项、允许替换项、禁止改动项、声音要求和交付模式。

分段只改变生成单位。没有明确授权时，不压缩剧情、不删台词、不改变原始节拍。

### PREFLIGHT：核验素材和执行器

确认本地文件、URL 或素材节点可访问。实际生成前，还要确认执行器是否支持：

- 场景参考图输入
- 指定视频首帧
- 场景参考图和首帧的多参考输入，或可靠的两阶段替代方案
- 目标时长、画幅和分辨率
- 逐句对白、语言/口音、声音表演、唇形同步、环境音、音效和静音控制
- 可查看、可下载或可继续处理的结果

执行器不支持指定首帧时，不承诺尾帧接力；应改为 `prompt_package` 或更换执行路径。

### ANALYZE：建立三份账本

- **镜头账本**：镜头 ID、时间范围、时长、动作、景别、机位、运镜、光线、声音和屏幕元素。
- **台词账本**：台词 ID、镜头 ID、说话人、原文和顺序。
- **叙事账本**：钩子、冲突、升级、反转、产品露出、证明点和 CTA。

### REWRITE：建立替换矩阵

对人物、场景、服装、道具、产品、品牌、台词、声音和 CTA 分别标记：

```text
保留 / 替换 / 删除 / 待确认
```

每轮修改都从账本和已确认替换矩阵重建完整方案，而不是在旧 Prompt 上累积局部补丁。

### SEGMENT：划分连续片段

按场景、人物、时间、动作和情绪连续性合并镜头。默认每段不超过 15 秒，实际取流程上限、执行器上限和用户上限中的较低值。遇到地点/时间跳转、情绪断点或超时，在自然叙事节点拆分。

### REFERENCE：锁定场景参考图

每个连续场景建立一张实际全景参考图，至少锁定：

- 人物脸型、发型、年龄感、体型、身高关系和完整服装
- 固定道具、随身物品和产品外观
- 建筑、道路、门窗、家具、出入口和空间布局
- 人物初始方位、行动路线、时间、天气、主光方向和色温

只有文字 Prompt、路径占位符或“准备生成”状态，不算参考图已就绪。

### HANDOFF：真实尾帧交接

同一连续场景严格执行：

```text
场景参考图 -> A -> 验收 A -> A_tail
场景参考图 + A_tail -> B -> 验收 B -> B_tail
场景参考图 + B_tail -> C
```

后段第一帧必须继承前段尾帧的构图、姿态、视线、手部、道具位置、人物方位、机位、光线和运动方向。前段没有验收通过或尾帧没有真实文件时，不生成后段。

明确的空间或时间切换使用 `hard_cut`，建立新场景 ID 和新参考图，不把硬切当作逃避连续性检查的标记。

## 台词、声音和字幕

只要镜头存在对白、旁白、画外音或可听见的说话，必须同时交付 `dialogue_delivery_sheet`。每句至少包含：

| 字段 | 内容 |
| --- | --- |
| `source_id` / `shot_id` | 台词和所属镜头的稳定 ID |
| `speaker` | 说话人 |
| `text` | 最终完整台词，不能写“自然对话”或省略号 |
| `language` | 默认 `English`，必要时写 `English/en-US` 或 `English/en-GB` |
| `timing` | 起止时间或可用时长 |
| `delivery` | 情绪、重音、停顿、音量和说话速度 |
| `voice_path` | 原生生成、后期配音或待确认 |
| `lip_sync` | 是否需要唇形同步 |
| `subtitles` | 有口播时固定为 `on` |
| `subtitle_text` | 必须与最终英文台词逐字一致 |
| `subtitle_position` / `subtitle_style` | 固定为画面下方安全区、白色文字内填充和黑色描边 |

字幕规则：

- 只要有对白、旁白、画外音或其他口播，必须写 `subtitles: on`，并逐句提供与英文台词一致的英文字幕、下方安全区位置、白色文字内填充和黑色描边。
- 用户明确要求显示字幕时，覆盖更早 Prompt 中的“不要字幕/不得出现字幕”；本 skill 对口播默认开启字幕。
- “画面下方保留干净留白”默认解释为字幕安全区，不能默默解释成关闭字幕。
- 用户没有口播且没有明确字幕要求时，才可以关闭字幕；出现冲突时列为待确认。
- 台词、逐镜 Prompt、分段 Prompt、交付表和字幕文本必须逐字一致。
- 自然对白可先按约 `2.0-2.8 words/s` 估算口播容量；超出镜头时长时，缩短台词、增加时长或标记待确认。

没有对白的镜头明确写 `无对白`，并同步环境音、音效、BGM 和字幕策略。

## 真人镜头和色彩写法

“电影感”“奥斯卡风格”“某导演风格”都不是足够的生成参数。真人或写实人物镜头至少要展开：

1. **主体调度**：人物起始方位、行动路线、视线、前后景关系和 180 度轴线。
2. **景别与焦段**：建立镜头、全景、中景、中近景、近景或特写，以及广角/标准/长焦感。
3. **机位与运动**：机位高度、俯仰、横滚、相对人物位置、路径、方向、速度和稳定度。
4. **对焦与构图**：对焦对象、景深、焦点转移、头顶空间、运动留白和屏幕方向。
5. **光线与曝光**：主光来源、辅光/负补光、轮廓光、阴影方向、高光保护和曝光控制。
6. **色彩与质感**：主色、辅色、背景色、冷暖关系、饱和度、肤色保护、颗粒和运动模糊。

单个镜头只设一个主要运镜，最多增加一个不冲突的次要动作。不要同时写“静止锁定”和“跟拍”，也不要同时要求“完全稳定”和“明显手持抖动”。

## 核心脚本与变体

当用户说“核心脚本不变”时，先冻结 `core_script`，再生成变体：

```yaml
core_script:
  frozen: true
  beat_ids: [B01, B02, B03]
  dialogue_ids: [D01, D02]
  invariants: [plot_order, dialogue_order, product, cta]
variant_policy:
  allowed_axes: [setting, wardrobe, camera_style]
  forbidden_axes: [plot_order, dialogue_order, product, cta]
  max_changed_axes_per_variant: 1
```

每个变体必须列出 `changed_axes`、`delta` 和完整 `preserved_core_ids`，并独立输出可复制 Prompt。默认一次只改变一个主要变量簇，保证测试结果可归因。改变剧情因果、台词顺序、产品主张或 CTA，不属于普通变体，必须重新确认。

## JSON 计划和校验

复杂任务可以从 [`assets/remake-plan.template.json`](assets/remake-plan.template.json) 复制计划文件。当前计划格式为 `schema_version: 3`，常用顶层字段包括：

```text
schema_version
workflow_mode
settings
execution
source
core_script
variant_policy
variants
source_dialogue
dialogue_delivery_sheet
shots
scene_references
segments
omissions
```

校验器会检查模式、片段时长、执行器能力、对白映射、字幕文本、变体隔离、场景参考图、片段顺序和尾帧依赖。

```powershell
# 方案阶段：检查结构和字段
py scripts/validate_remake_plan.py path\to\remake-plan.json --phase plan

# execute 模式下，生成某个片段前检查参考图和上一段尾帧
py scripts/validate_remake_plan.py path\to\remake-plan.json --phase pre-generate --segment-id B

# 最终阶段：检查所有参考图和输出片段是否已验收
py scripts/validate_remake_plan.py path\to\remake-plan.json --phase final
```

`pre-generate` 和 `final` 只适用于 `workflow_mode: execute`，并要求执行器能力已经有具体证据。

## 配套脚本

### `inspect_reference.py`

在本地读取参考视频的媒体信息，不上传素材：时长、尺寸、比例、方向、帧率、编码、像素格式、音频存在性、音频编码和文件 SHA-256。

```powershell
py scripts/inspect_reference.py input\reference.mp4 --output reports\reference.json
```

需要 `ffprobe`。如果它不在 `PATH`，可以显式指定：

```powershell
py scripts/inspect_reference.py input\reference.mp4 --ffprobe C:\tools\ffprobe.exe
```

读取不到的字段会保持未知，并写入 `warnings`，不会被脚本猜测。

### `extract_tail_frame.py`

从已经验收通过的视频片段末尾提取真实尾帧，并输出来源视频哈希、尾帧时间点、文件路径、文件大小和尾帧哈希。输出后仍需要人工视觉确认。

```powershell
py scripts/extract_tail_frame.py `
  outputs\A.mp4 `
  handoff\A_tail.png `
  --offset 0.1
```

需要 `ffmpeg`；脚本会优先寻找同目录的 `ffprobe`。如果输出文件已经存在，需要加 `--force` 才会覆盖。

### `validate_remake_plan.py`

验证平台无关的 JSON 复刻计划。返回格式化 JSON；存在错误时返回非零退出码，适合接入本地脚本或 CI。

## 质量门槛

方案和执行按以下门槛检查：

| 门槛 | 核心问题 |
| --- | --- |
| Gate 1 | 输入素材是否真实存在且可访问 |
| Gate 2 | 执行器是否真的支持参考图、首帧、参数和声音要求 |
| Gate 3 | 镜头、台词和叙事账本是否完整 |
| Gate 4 | 每项改写是否可追溯，是否误删剧情或台词 |
| Gate 4B | 公众人物和 IP 是否已去标识化为原创角色 |
| Gate 5 | 镜头是否正确分段，时长和声音是否一致 |
| Gate 5A | 核心脚本是否冻结，变体是否隔离 |
| Gate 6 | 每个连续场景是否有实际参考图 |
| Gate 7 | 尾帧是否来自已验收视频并可访问 |
| Gate 8 | 接缝处人物、道具、方位、光线和运动是否连续 |
| Gate 9 | 台词、BGM、环境音、唇形同步和字幕是否一致 |
| Gate 9B | Prompt 正文是否中文，口播字幕是否为白色填充黑色描边 |
| Gate 9A | 默认地域、英文对白、鲜艳色彩和真人摄影是否正确落地 |
| Gate 10 | 是否真的获得了外部生成确认 |
| Gate 11 | 报告的每个状态是否有对应证据 |

“Prompt 已写”“任务已提交”“页面出现进度”都不等于“视频已生成”。只有结果可查看、片段验收通过并且尾帧真实存在，才可以进入下一步。

## 授权边界

- 本地参考素材默认只在本地分析。
- 分析授权不等于上传授权，也不等于生成授权。
- 用户没有明确确认前，不上传本地文件、不提交外部任务、不消耗额度或调用付费服务。
- 生成前如果执行器能力、台词、字幕、声音路径、画幅、时长或关键替换项仍待确认，应停在确认门。
- 不报告没有证据的上传、提交、生成、下载、尾帧提取或验收状态。

## 仓库结构

```text
ai-video-workflow/
├── SKILL.md                         # Codex skill 入口和硬性规则
├── README.md                        # 安装、使用和工作流说明
├── agents/
│   └── openai.yaml                  # Codex 界面元数据
├── assets/
│   └── remake-plan.template.json    # schema_version 3 计划模板
├── references/
│   ├── workflow.md                  # 状态机、账本和分段流程
│   ├── quality-gates.md             # Gate 1-11 质量门槛
│   ├── execution-adapter.md         # 执行器能力契约和字段映射
│   └── camera-prompt-language.md    # 平台无关的镜头提示词语言
└── scripts/
    ├── inspect_reference.py         # 本地参考视频媒体信息检查
    ├── extract_tail_frame.py        # 验收片段尾帧提取
    └── validate_remake_plan.py      # JSON 计划校验
```

## 进一步阅读

- [SKILL.md](SKILL.md)：完整的 Codex 行为规则和输出契约
- [references/workflow.md](references/workflow.md)：状态机、账本、分段和尾帧流程
- [references/quality-gates.md](references/quality-gates.md)：各阶段质量门槛
- [references/execution-adapter.md](references/execution-adapter.md)：执行器能力检查和字段映射
- [references/camera-prompt-language.md](references/camera-prompt-language.md)：镜头、构图、运镜和连续性写法
- [assets/remake-plan.template.json](assets/remake-plan.template.json)：复杂任务的 JSON 计划模板

## 许可证和贡献

提交修改时，请保持以下边界：

- 保持平台无关，不把某个网站或模型写成默认执行器。
- 新增规则必须能改变实际决策或提升可验证性，避免堆积泛化口号。
- 修改台词、字幕、默认基线或确认门时，同时检查 `SKILL.md`、相关 reference 和 JSON 校验器是否一致。
- 脚本改动后运行对应的 `--help`、编译检查和最小行为测试。
- 不把 Prompt、任务 ID、预填路径或模拟结果报告成真实生成资产。
