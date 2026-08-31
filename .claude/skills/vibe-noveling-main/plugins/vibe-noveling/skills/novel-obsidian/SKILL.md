---
name: novel-obsidian
description: 同步实体关系到 Obsidian vault，通过图谱视图 + Graph Link Types 可视化知识图谱。
when_to_use: |
  用户想可视化知识图谱，或在 rebuild 知识图谱后同步 Obsidian wiki links。
user-invocable: true
invokes: {SKILL_DIR}/scripts/obsidian_sync.py
---
# Obsidian 知识图谱可视化

将实体关系数据同步到 Obsidian vault，利用 Obsidian 图谱视图 + Graph Link Types 插件可视化知识图谱。

## 前提

- 已安装 Obsidian（https://obsidian.md）
- vault 中安装了以下插件：
  1. **Dataview**（Graph Link Types 的依赖）
  2. **Graph Link Types**（在图谱边上显示关系类型）

## 命令

```bash
python {SKILL_DIR}/scripts/obsidian_sync.py <command> [args]
```

### setup — 初始化 Obsidian vault

```bash
python {SKILL_DIR}/scripts/obsidian_sync.py setup <vault_path>
```

创建 vault 目录，建立 `entities/` 符号链接指向项目的 `memory/entities/`，生成仪表盘笔记。

示例：
```bash
python {SKILL_DIR}/scripts/obsidian_sync.py setup /Users/you/Documents/修真界知识图谱
```

然后在 Obsidian 中 "Open folder as vault" 打开该目录。

### sync — 同步关系数据

```bash
python {SKILL_DIR}/scripts/obsidian_sync.py sync [--dry-run]
```

读取 `_graph.json`，为每个实体文件注入 `[[wiki links]]` 关系区块。

- `--dry-run`：预览变更，不写入文件
- 在 `rebuild` 后自动调用，也可手动执行

### dashboard — 生成仪表盘

```bash
python {SKILL_DIR}/scripts/obsidian_sync.py dashboard
```

在 vault 根目录生成 `知识图谱总览.md`，包含 Dataview 查询。

## 同步机制

脚本在实体文件正文末尾注入受管理的区块：

```markdown
<!-- OBSIDIAN-SYNC-START -->
## 关系图谱

### 出向关系
- **located_in** → [[九天大陆]] (九天大陆北方冰原)

### 入向关系
- **capital_of** ← [[北境三族]] (北境三族的都城)
<!-- OBSIDIAN-SYNC-END -->
```

- 只替换 `OBSIDIAN-SYNC-START/END` 标记之间的内容
- 不修改 frontmatter，不影响 `knowledge_graph.py` 的解析
- 幂等：多次运行结果一致

## 自动调用时机

以下场景会自动调用 `sync`：

1. **novel-sync 完成后**：rebuild 知识图谱后自动同步
2. **novel-discuss 落盘后**：创建/修改实体后自动同步

## 工作流

```
novel-discuss / novel-sync
    → knowledge_graph.py rebuild
    → obsidian_sync.py sync
    → Obsidian 图谱视图实时更新
```

## Vault 结构

```
<vault_path>/
├── .obsidian/           # Obsidian 配置（自动生成）
├── entities/ → <project>/memory/entities/   # 符号链接
└── 知识图谱总览.md      # Dataview 仪表盘（自动生成）
```
