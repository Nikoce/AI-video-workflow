# 生成执行器能力契约

把网站、模型、API、CLI 或人工操作界面视为可替换执行器。流程不能依赖某个执行器的品牌或字段名。

## 选择前检查

记录以下能力及证据：

| 能力 | 必需条件 | 不满足时 |
| --- | --- | --- |
| 场景参考图输入 | 能锁定人物和环境，或可通过独立图像阶段生成后输入 | 改用两阶段执行器或只交付 Prompt |
| 指定视频首帧 | 能把实际尾帧作为下一段首帧 | 不承诺尾帧接力，改用其他执行器 |
| 多参考输入 | 能同时使用场景参考图和首帧，或有可靠顺序上传方法 | 先锁场景图，再将尾帧作为强制首帧 |
| 时长 | 支持当前片段长度 | 降低分段上限 |
| 画幅与分辨率 | 支持用户目标 | 重新确认可接受参数 |
| 声音 | 支持对白、音效、环境音或静音要求 | 拆成视频与后期音频两阶段 |
| 结果证据 | 返回可查看文件、URL 或素材节点 | 不报告生成完成 |

## 能力记录

```json
{
  "name": "<executor-name>",
  "capabilities_verified": true,
  "verification_evidence": "<docs-live-probe-or-visible-ui>",
  "supports_scene_reference": true,
  "supports_start_frame": true,
  "supports_multiple_references": true,
  "max_duration_seconds": 10,
  "supported_ratios": ["9:16"],
  "supported_resolutions": ["720p"],
  "audio_mode": "native-or-post"
}
```

不要只根据营销文案认定能力。优先使用当前文档、可见控件、最小安全探测或已验证成功记录。能力可能变化，真正生成前重新核验。

## 字段映射

把通用输入映射到执行器字段：

| 通用输入 | 执行器字段 |
| --- | --- |
| `scene_reference.image_path` | 参考图、角色图、风格图或资产节点 |
| `continuity.start_frame_path` | 首帧、起始图、image-to-video 输入 |
| `generation_prompt` | 正向视频提示词 |
| `negative_constraints` | 负向提示词或禁止项 |
| `duration_seconds` | 时长参数 |
| `ratio` / `resolution` | 输出规格 |
| `audio` | 原生声音参数或后期音频计划 |

若执行器只能上传一张图，不能静默丢弃其中一个参考输入。停止并明确说明能力缺口。

## 提交与状态

- 上传后验证附件名称、缩略图、资产 ID 或其他可见证据。
- 提交后记录任务 ID、节点 ID 或结果位置。
- “已提交”不等于“生成完成”。
- 只有结果文件、URL 或素材节点可访问时，才进入验收。
- 用户没有授权时，不上传本地文件、不调用付费生成、不消耗额度。
