#!/usr/bin/env python3
"""
短句碎片检测工具

检测非对话叙述文本中的连续短句碎片。短句碎片指 ≤15 字的句子连续出现超过阈值。

使用方式：
    python tools/fragment_checker.py <正文文件路径> [--threshold 3] [--fix]

    --threshold  连续短句的最大允许数量（默认 3）
    --fix        输出修复建议（哪些段落需要合并）

退出码：
    0 — 全部通过
    1 — 存在短句碎片
"""

import argparse
import re
import sys
from pathlib import Path


def strip_dialogue(text: str) -> str:
    """移除对话内容，只保留叙述文本。"""
    # 移除引号内的对话
    result = re.sub(r'[""「][^""」]+[""」]', '', text)
    return result


def find_sentences(text: str) -> list[tuple[str, int, int]]:
    """提取句子及其位置。返回 (句子文本, 起始位置, 结束位置) 的列表。"""
    sentences = []
    for m in re.finditer(r'([^。！？\n]+[。！？])', text):
        s = m.group(1).strip()
        if s:
            sentences.append((s, m.start(), m.end()))
    return sentences


def check_fragments(text: str, threshold: int = 3) -> list[dict]:
    """检查短句碎片，返回违规段落列表。"""
    non_dialogue = strip_dialogue(text)
    sentences = find_sentences(non_dialogue)

    if not sentences:
        return []

    violations = []
    consecutive_short = []

    for sent, start, end in sentences:
        char_count = len(re.sub(r'[^一-鿿 a-zA-Z0-9]', '', sent))
        if char_count <= 15:
            consecutive_short.append({
                'text': sent,
                'chars': char_count,
                'start': start,
                'end': end,
            })
        else:
            if len(consecutive_short) > threshold:
                violations.append({
                    'fragments': consecutive_short,
                    'count': len(consecutive_short),
                    'preview': ' → '.join(f['text'][:20] for f in consecutive_short),
                    'position': consecutive_short[0]['start'],
                })
            consecutive_short = []

    # Check last group
    if len(consecutive_short) > threshold:
        violations.append({
            'fragments': consecutive_short,
            'count': len(consecutive_short),
            'preview': ' → '.join(f['text'][:20] for f in consecutive_short),
            'position': consecutive_short[0]['start'],
        })

    return violations


def main():
    parser = argparse.ArgumentParser(description='短句碎片检测工具')
    parser.add_argument('file', help='正文文件路径')
    parser.add_argument('--threshold', '-t', type=int, default=3,
                        help='连续短句的最大允许数量（默认 3）')
    parser.add_argument('--fix', action='store_true',
                        help='输出修复建议')
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f'文件不存在: {path}', file=sys.stderr)
        sys.exit(2)

    text = path.read_text(encoding='utf-8')
    violations = check_fragments(text, args.threshold)

    if not violations:
        print(f'✓ 短句碎片检测通过（阈值: {args.threshold}）')
        sys.exit(0)

    print(f'✗ 发现 {len(violations)} 处短句碎片（阈值: {args.threshold}）:')
    for i, v in enumerate(violations, 1):
        print(f'\n  [{i}] 连续 {v["count"]} 个短句:')
        for frag in v['fragments']:
            print(f'      "{frag["text"]}" ({frag["chars"]}字)')

    if args.fix:
        print(f'\n修复建议:')
        print(f'  将上述连续短句用逗号或分号合并为长句，整合因果关系。')
        print(f'  保持核心表意不变，不增加字数。')

    sys.exit(1)


if __name__ == '__main__':
    main()
