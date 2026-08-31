#!/usr/bin/env python3
"""
Obsidian 知识图谱同步工具 - obsidian_sync.py

将 _graph.json 中的实体关系同步为 Obsidian 可识别的 [[wiki links]]，
配合 Obsidian 的图谱视图和 Graph Link Types 插件实现关系可视化。

功能:
1. 初始化 vault: python obsidian_sync.py setup <vault_path>
2. 同步关系数据: python obsidian_sync.py sync [--dry-run]
3. 生成仪表盘:   python obsidian_sync.py dashboard <vault_path>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


def find_project_root() -> Path:
    """从 CWD 向上查找包含 memory/_graph.json 的项目根目录。"""
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / "memory" / "_graph.json").exists():
            return p
    return cwd


PROJECT_ROOT = find_project_root()
MEMORY_DIR = PROJECT_ROOT / "memory"
ENTITIES_DIR = MEMORY_DIR / "entities"
GRAPH_FILE = MEMORY_DIR / "_graph.json"

SYNC_START = "<!-- OBSIDIAN-SYNC-START -->"
SYNC_END = "<!-- OBSIDIAN-SYNC-END -->"


def load_graph() -> Dict[str, Any]:
    if GRAPH_FILE.exists():
        with open(GRAPH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "1.0", "entities": {}, "relations": []}


def get_relations_for_entity(entity_id: str, graph: Dict) -> Tuple[List[Dict], List[Dict]]:
    outgoing = [r for r in graph.get("relations", []) if r.get("from") == entity_id]
    incoming = [r for r in graph.get("relations", []) if r.get("to") == entity_id]
    return outgoing, incoming


def build_sync_section(entity_id: str, outgoing: List[Dict], incoming: List[Dict], graph: Dict) -> str:
    lines = [SYNC_START, "## 关系图谱", ""]

    if outgoing:
        lines.append("### 出向关系")
        for rel in sorted(outgoing, key=lambda r: (r.get("type", ""), r.get("to", ""))):
            target = rel.get("to", "")
            rel_type = rel.get("type", "")
            note = rel.get("note", "")
            note_str = f" ({note})" if note else ""
            lines.append(f"- **{rel_type}** → [[{target}]]{note_str}")
        lines.append("")

    if incoming:
        lines.append("### 入向关系")
        for rel in sorted(incoming, key=lambda r: (r.get("type", ""), r.get("from", ""))):
            source = rel.get("from", "")
            rel_type = rel.get("type", "")
            note = rel.get("note", "")
            note_str = f" ({note})" if note else ""
            lines.append(f"- **{rel_type}** ← [[{source}]]{note_str}")
        lines.append("")

    if not outgoing and not incoming:
        lines.append("*暂无关系记录*")
        lines.append("")

    lines.append(SYNC_END)
    return "\n".join(lines)


def inject_sync_section(content: str, section: str) -> str:
    if SYNC_START in content:
        pattern = re.escape(SYNC_START) + r".*?" + re.escape(SYNC_END)
        new_content = re.sub(pattern, section, content, flags=re.DOTALL)
        return new_content
    else:
        return content.rstrip() + "\n\n" + section + "\n"


def sync_entity(entity_id: str, graph: Dict, dry_run: bool = False) -> Dict[str, Any]:
    entity_info = graph.get("entities", {}).get(entity_id)
    if not entity_info:
        return {"entity": entity_id, "status": "skipped", "reason": "not in graph"}

    filepath = PROJECT_ROOT / entity_info.get("file", "")
    if not filepath.exists():
        return {"entity": entity_id, "status": "skipped", "reason": "file not found"}

    content = filepath.read_text(encoding="utf-8")

    if not content.startswith("---"):
        return {"entity": entity_id, "status": "skipped", "reason": "no frontmatter"}

    outgoing, incoming = get_relations_for_entity(entity_id, graph)
    section = build_sync_section(entity_id, outgoing, incoming, graph)

    if dry_run:
        return {
            "entity": entity_id,
            "status": "dry_run",
            "outgoing": len(outgoing),
            "incoming": len(incoming),
            "section_preview": section[:500]
        }

    new_content = inject_sync_section(content, section)
    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")
        return {"entity": entity_id, "status": "updated", "outgoing": len(outgoing), "incoming": len(incoming)}
    else:
        return {"entity": entity_id, "status": "unchanged", "outgoing": len(outgoing), "incoming": len(incoming)}


def cmd_sync(dry_run: bool = False) -> None:
    graph = load_graph()
    entities = graph.get("entities", {})
    if not entities:
        print("知识图谱为空，请先运行 knowledge_graph.py rebuild")
        return

    results = {"updated": 0, "unchanged": 0, "skipped": 0, "dry_run": 0}
    skipped_entities = []

    for entity_id in sorted(entities.keys()):
        result = sync_entity(entity_id, graph, dry_run=dry_run)
        status = result["status"]
        results[status] = results.get(status, 0) + 1

        if status == "skipped":
            skipped_entities.append(f"  {entity_id}: {result['reason']}")
        elif dry_run:
            print(f"[预览] {entity_id}: {result['outgoing']} 出向, {result['incoming']} 入向")
        elif status == "updated":
            print(f"[更新] {entity_id}: {result['outgoing']} 出向, {result['incoming']} 入向")

    print(f"\n同步完成: {results.get('updated', 0)} 更新 / {results.get('unchanged', 0)} 无变化 / {results.get('skipped', 0)} 跳过")
    if skipped_entities:
        print("跳过的实体:")
        for s in skipped_entities:
            print(s)


def cmd_setup(vault_path: str) -> None:
    vault = Path(vault_path).resolve()
    entities_link = vault / "entities"
    entities_target = ENTITIES_DIR.resolve()

    vault.mkdir(parents=True, exist_ok=True)

    if entities_link.exists() or entities_link.is_symlink():
        if entities_link.resolve() == entities_target:
            print(f"符号链接已存在: {entities_link} -> {entities_target}")
        else:
            print(f"警告: {entities_link} 已存在但指向不同目标")
            return
    else:
        entities_link.symlink_to(entities_target, target_is_directory=True)
        print(f"已创建符号链接: {entities_link} -> {entities_target}")

    dashboard_path = vault / "知识图谱总览.md"
    _generate_dashboard(dashboard_path)

    print(f"\nvault 已创建: {vault}")
    print("\n请在 Obsidian 中:")
    print(f"  1. Open folder as vault -> {vault}")
    print("  2. 安装社区插件: Dataview, Graph Link Types")
    print("  3. 打开图谱视图查看关系网络")


def _generate_dashboard(output_path: Path) -> None:
    content = """# 修真界知识图谱

> 由 `novel-obsidian` 自动生成，请勿手动编辑。

## 角色索引

```dataview
LIST
FROM "entities/characters"
SORT file.name
```

## 势力索引

```dataview
LIST
FROM "entities/factions"
SORT file.name
```

## 地点索引

```dataview
LIST
FROM "entities/locations"
SORT file.name
```

## 物品索引

```dataview
LIST
FROM "entities/items"
SORT file.name
```

## 概念索引

```dataview
LIST
FROM "entities/concepts"
SORT file.name
```
"""
    output_path.write_text(content, encoding="utf-8")
    print(f"已生成仪表盘: {output_path}")


def cmd_dashboard(vault_path: str) -> None:
    vault = Path(vault_path).resolve()
    if not vault.exists():
        print(f"vault 不存在: {vault}")
        print("请先运行 setup 命令")
        return
    _generate_dashboard(vault / "知识图谱总览.md")


def main():
    parser = argparse.ArgumentParser(
        description="Obsidian 知识图谱同步工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python obsidian_sync.py setup /path/to/vault
  python obsidian_sync.py sync
  python obsidian_sync.py sync --dry-run
  python obsidian_sync.py dashboard /path/to/vault
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    setup_parser = subparsers.add_parser("setup", help="初始化 Obsidian vault")
    setup_parser.add_argument("vault_path", help="vault 目录路径")

    sync_parser = subparsers.add_parser("sync", help="同步关系数据到实体文件")
    sync_parser.add_argument("--dry-run", action="store_true", help="预览变更，不写入文件")

    dashboard_parser = subparsers.add_parser("dashboard", help="生成/更新仪表盘笔记")
    dashboard_parser.add_argument("vault_path", help="vault 目录路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "setup":
        cmd_setup(args.vault_path)
    elif args.command == "sync":
        cmd_sync(dry_run=args.dry_run)
    elif args.command == "dashboard":
        cmd_dashboard(args.vault_path)


if __name__ == "__main__":
    main()
