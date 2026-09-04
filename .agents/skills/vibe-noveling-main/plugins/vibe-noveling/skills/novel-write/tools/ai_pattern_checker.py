#!/usr/bin/env python3
"""
AI 文风痕迹检测工具

检测中文小说叙述文本中的 AI 典型写作痕迹。所有规则仅检查非对话叙述部分。

使用方式：
    python tools/ai_pattern_checker.py <正文文件路径> [--json] [--fix]

    --json    以 JSON 格式输出结果
    --fix     输出修复建议

退出码：
    0 — 全部通过
    1 — 存在 AI 痕迹
    2 — 文件错误
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

# ── 规则定义 ──────────────────────────────────────────────────────────

# 叙述中破折号最大允许次数
EM_DASH_MAX = 1

# 负面排比：3+ 个并列否定短语
NEG_PARALLEL_RE = re.compile(
    r'(?:不|没有|不再|不会|无法)[^，。！？]{1,8}，'
    r'(?:不|没有|不再|不会|无法)[^，。！？]{1,8}，'
    r'(?:不|没有|不再|不会|无法)'
)

# 纠偏句式
CORRECTIVE_PATTERNS = [
    (re.compile(r'不是[^，。]{1,30}而是'), '不是…而是…'),
    (re.compile(r'并非[^，。]{1,30}(?:只是|而是)'), '并非…只是/而是…'),
    (re.compile(r'与其说[^，。]{1,30}不如说'), '与其说…不如说…'),
    (re.compile(r'不在于[^，。]{1,30}而在于'), '不在于…而在于…'),
    (re.compile(r'恰恰相反'), '恰恰相反'),
    (re.compile(r'相反，'), '相反，'),
]

# 虚假升华
FALSE_ELEVATION_KEYWORDS = ['象征着', '昭示着', '映照出', '命运转折', '时代缩影', '格局改写']
FALSE_ELEVATION_PATTERNS = [
    (re.compile(r'这不仅是[^，。]{1,30}更是'), '这不仅是…更是…'),
]

# 交流残留
COMMUNICATION_RESIDUE_KEYWORDS = [
    '让我们看看',
    '下面来看看',
    '这里可以看出',
    '如果你愿意',
    '值得注意的是',
    '需要指出的是',
]

# 形容词+冒号
ADJ_COLON_RE = re.compile(r'(?:的是|之处|之处在于|很简单|很明确|很清晰)：')

# 段首过渡词
PARAGRAPH_START_WORDS = [
    '最终',
    '总之',
    '综上所述',
    '由此可见',
    '显而易见',
]

# 否定词开头的句子（在 。！？ 或行首之后）
NEGATION_SENTENCE_RE = re.compile(r'(?:^|[。！？\n])(\s*(?:没有|不是|不会|不能|不再|并非|从未))')


# ── 核心函数 ──────────────────────────────────────────────────────────

def strip_dialogue(text: str) -> str:
    """移除对话内容，只保留叙述文本。"""
    return re.sub(r'[""「][^""」]+[""」]', '', text)


def _context(text: str, pos: int, width: int = 20) -> str:
    """截取 pos 位置前后各 width 个字符作为上下文。"""
    start = max(0, pos - width)
    end = min(len(text), pos + width)
    snippet = text[start:end]
    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'
    return snippet


def check(text: str, threshold_config: Optional[dict] = None) -> list[dict]:
    """
    运行全部 AI 痕迹检查，返回违规列表。

    每条违规: {"rule": 规则名, "count": 违规次数, "items": [{"position": int, "context": str}]}
    无违规则返回空列表。
    """
    violations = []
    narrative = strip_dialogue(text)

    # 1. 破折号
    em_dashes = list(re.finditer(r'——', narrative))
    if len(em_dashes) > EM_DASH_MAX:
        items = []
        for m in em_dashes:
            items.append({'position': m.start(), 'context': _context(narrative, m.start())})
        violations.append({
            'rule': '破折号',
            'count': len(em_dashes),
            'items': items,
        })

    # 2. 负面排比
    neg_matches = list(NEG_PARALLEL_RE.finditer(narrative))
    if neg_matches:
        items = []
        for m in neg_matches:
            items.append({'position': m.start(), 'context': _context(narrative, m.start())})
        violations.append({
            'rule': '负面排比',
            'count': len(neg_matches),
            'items': items,
        })

    # 3. 纠偏句式
    corrective_items = []
    for pat, label in CORRECTIVE_PATTERNS:
        for m in pat.finditer(narrative):
            corrective_items.append({
                'position': m.start(),
                'context': _context(narrative, m.start()) + f'  [{label}]',
            })
    if corrective_items:
        violations.append({
            'rule': '纠偏句式',
            'count': len(corrective_items),
            'items': corrective_items,
        })

    # 4. 虚假升华
    elevation_items = []
    for kw in FALSE_ELEVATION_KEYWORDS:
        for m in re.finditer(re.escape(kw), narrative):
            elevation_items.append({
                'position': m.start(),
                'context': _context(narrative, m.start()) + f'  [{kw}]',
            })
    for pat, label in FALSE_ELEVATION_PATTERNS:
        for m in pat.finditer(narrative):
            elevation_items.append({
                'position': m.start(),
                'context': _context(narrative, m.start()) + f'  [{label}]',
            })
    if elevation_items:
        violations.append({
            'rule': '虚假升华',
            'count': len(elevation_items),
            'items': elevation_items,
        })

    # 5. 交流残留
    residue_items = []
    for kw in COMMUNICATION_RESIDUE_KEYWORDS:
        for m in re.finditer(re.escape(kw), narrative):
            residue_items.append({
                'position': m.start(),
                'context': _context(narrative, m.start()),
            })
    if residue_items:
        violations.append({
            'rule': '交流残留',
            'count': len(residue_items),
            'items': residue_items,
        })

    # 6. 形容词+冒号
    adj_matches = list(ADJ_COLON_RE.finditer(narrative))
    if adj_matches:
        items = []
        for m in adj_matches:
            items.append({'position': m.start(), 'context': _context(narrative, m.start())})
        violations.append({
            'rule': '形容词+冒号',
            'count': len(adj_matches),
            'items': items,
        })

    # 7. 段首过渡词
    paragraphs = re.split(r'\n\n+', text)
    para_items = []
    for para in paragraphs:
        stripped = para.lstrip()
        if not stripped:
            continue
        for word in PARAGRAPH_START_WORDS:
            if stripped.startswith(word):
                para_items.append({
                    'position': text.find(para),
                    'context': stripped[:40],
                })
                break
    if para_items:
        violations.append({
            'rule': '段首过渡词',
            'count': len(para_items),
            'items': para_items,
        })

    # 8. 否定词开头的句子
    neg_sent_matches = list(NEGATION_SENTENCE_RE.finditer(narrative))
    if neg_sent_matches:
        items = []
        for m in neg_sent_matches:
            items.append({'position': m.start(), 'context': _context(narrative, m.start())})
        violations.append({
            'rule': '否定词开头',
            'count': len(neg_sent_matches),
            'items': items,
        })

    return violations


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='AI 文风痕迹检测工具')
    parser.add_argument('file', help='正文文件路径')
    parser.add_argument('--json', action='store_true', dest='json_output',
                        help='以 JSON 格式输出结果')
    parser.add_argument('--fix', action='store_true',
                        help='输出修复建议')
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f'文件不存在: {path}', file=sys.stderr)
        sys.exit(2)

    try:
        text = path.read_text(encoding='utf-8')
    except Exception as e:
        print(f'读取文件失败: {e}', file=sys.stderr)
        sys.exit(2)

    violations = check(text)

    if args.json_output:
        result = {
            'passed': len(violations) == 0,
            'violations': violations,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not violations:
            print('✓ AI 文风痕迹检测通过')
            sys.exit(0)

        total = sum(v['count'] for v in violations)
        print(f'✗ 发现 {total} 处 AI 文风痕迹（{len(violations)} 条规则）:')
        for v in violations:
            print(f'\n  【{v["rule"]}】 ×{v["count"]}')
            for item in v['items']:
                print(f'      位置 {item["position"]}: {item["context"]}')

    if args.fix:
        print('\n修复建议: 针对每项违规，联系前后句整句重写，不做局部换词。')

    sys.exit(0 if not violations else 1)


if __name__ == '__main__':
    main()
