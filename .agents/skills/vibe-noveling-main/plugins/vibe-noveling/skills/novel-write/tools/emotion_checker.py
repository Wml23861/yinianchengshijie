#!/usr/bin/env python3
"""
情感展示检测工具

检测中文小说中的"告知而非展示"(tell don't show)情感写法，计算展示/告知比率。

使用方式：
    python3 tools/emotion_checker.py <正文文件路径> [--json] [--fix] [--threshold 2.0]

    --json       输出 JSON 格式结果
    --fix        输出修复建议
    --threshold  展示/告知比率的最低阈值（默认 2.0）

退出码：
    0 — 全部通过
    1 — 存在违规
    2 — 文件错误
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 模式定义
# ---------------------------------------------------------------------------

# 直接情感标签 (tell)
DIRECT_EMOTION_RE = re.compile(
    r'(他|她|它|这人)'
    r'(?:很|非常|极其|特别|格外|异常|十分)?'
    r'(愤怒|悲伤|高兴|开心|害怕|恐惧|焦虑|紧张|兴奋|感动|失望|绝望'
    r'|痛苦|难过|心痛|不安|震惊|恼怒|烦躁|委屈|尴尬|愧疚|后悔'
    r'|无奈|疲惫|心寒|心酸)'
)

# 情感涌上模式 (tell)
SURGE_EMOTION_RE = re.compile(
    r'(?:一阵|一股|一种|一丝)'
    r'(愤怒|悲伤|恐惧|绝望|痛苦|焦虑|不安|寒意|暖意|酸楚|委屈)'
    r'(涌上|袭来|蔓延|升起|涌来|填满|笼罩|划过|掠过|漫上)'
)

# 内心觉醒标签 (tell)
REALIZATION_RE = re.compile(
    r'(他|她)'
    r'(?:突然|忽然|猛然)?'
    r'(意识到|明白|发现|感觉到|感到|意识到)'
    r'(?:，|了)'
)

# 动作传情模式 (show)
ACTION_EMOTIONS = [
    # Hand/arm tension
    re.compile(r'攥紧|握紧|咬住|攥住|攥着|捏紧|攥出了汗'),
    # Movement avoidance
    re.compile(r'退后|后退|闪开|缩回|蜷缩'),
    # Body freeze/speed
    re.compile(r'加快|放慢|停住|僵住|顿住|愣住'),
    # Breathing
    re.compile(r'深吸|屏住|吐出一口气|抿紧'),
    # Face/head
    re.compile(r'别过|移开|低下|扬起|绷紧|咬着牙|绷着脸|沉着脸|黑着脸'),
    # Specific body parts
    re.compile(
        r'(?:后背|脊背|手心|指甲|膝盖|喉咙|胃|肩|脚底|太阳穴)'
        r'(?:发紧|发麻|发凉|发热|发疼|发软|发沉|发木)'
    ),
]

# 比喻词
METAPHOR_WORDS = re.compile(r'好像|似的|如同|仿佛|宛如|犹如')

# 先描写后比喻模式
DESCRIBE_THEN_SIMILE_RE = re.compile(
    r'[^，。！？]{5,}，(?:像|如|仿佛|似)[^，。！？]{3,}'
)


# ---------------------------------------------------------------------------
# 核心检测逻辑
# ---------------------------------------------------------------------------

def strip_dialogue(text: str) -> str:
    """移除对话内容，只保留叙述文本。"""
    return re.sub(r'[""「」][^""「」]*[""「」]', '', text)


def _find_emotion_labels(narrative: str) -> list[dict]:
    """查找所有情感标签 (tell) 匹配。"""
    hits = []
    for m in DIRECT_EMOTION_RE.finditer(narrative):
        hits.append({
            'type': 'direct',
            'text': m.group(),
            'pos': m.start(),
        })
    for m in SURGE_EMOTION_RE.finditer(narrative):
        hits.append({
            'type': 'surge',
            'text': m.group(),
            'pos': m.start(),
        })
    for m in REALIZATION_RE.finditer(narrative):
        hits.append({
            'type': 'realization',
            'text': m.group(),
            'pos': m.start(),
        })
    return hits


def _find_action_emotions(narrative: str) -> list[str]:
    """查找所有动作传情 (show) 匹配，返回去重后的匹配文本列表。"""
    seen = set()
    results = []
    for pattern in ACTION_EMOTIONS:
        for m in pattern.finditer(narrative):
            matched = m.group()
            if matched not in seen:
                seen.add(matched)
                results.append(matched)
    return results


def _check_metaphor_density(text: str) -> list[dict]:
    """检查每段的比喻密度。"""
    paragraphs = re.split(r'\n\n+', text)
    violations = []
    for idx, para in enumerate(paragraphs, 1):
        para = para.strip()
        if not para:
            continue
        # 计算比喻词出现次数
        metaphor_matches = METAPHOR_WORDS.findall(para)
        count = len(metaphor_matches)
        if count > 1:
            violations.append({
                'type': 'density',
                'paragraph': idx,
                'count': count,
                'words': metaphor_matches,
            })
        # 检查先描写后比喻
        for m in DESCRIBE_THEN_SIMILE_RE.finditer(para):
            violations.append({
                'type': 'describe_then_simile',
                'paragraph': idx,
                'text': m.group()[:40],
                'pos': m.start(),
            })
    return violations


def _check_info_dumps(text: str, limit: int = 400) -> list[dict]:
    """检测连续非对话段落（信息倾销）。"""
    # 将文本按段落分割
    paragraphs = re.split(r'\n\n+', text)
    # 判断段落是否包含对话
    dialogue_re = re.compile(r'[""「」]')
    violations = []
    run_start = None
    run_chars = 0

    for idx, para in enumerate(paragraphs, 1):
        para = para.strip()
        if not para:
            if run_start is not None and run_chars > limit:
                violations.append({
                    'start_paragraph': run_start,
                    'end_paragraph': idx - 1,
                    'chars': run_chars,
                })
            run_start = None
            run_chars = 0
            continue

        has_dialogue = bool(dialogue_re.search(para))
        if has_dialogue:
            if run_start is not None and run_chars > limit:
                violations.append({
                    'start_paragraph': run_start,
                    'end_paragraph': idx - 1,
                    'chars': run_chars,
                })
            run_start = None
            run_chars = 0
        else:
            if run_start is None:
                run_start = idx
            run_chars += len(para)

    # 结尾检查
    if run_start is not None and run_chars > limit:
        violations.append({
            'start_paragraph': run_start,
            'end_paragraph': len(paragraphs),
            'chars': run_chars,
        })

    return violations


def check(text: str, ratio_threshold: float = 2.0) -> dict:
    """
    检测情感展示质量。

    返回：
    {
        "passed": bool,
        "show_tell_ratio": float,
        "emotion_labels": int,
        "action_emotions": int,
        "action_details": [...],       # 去重后的动作传情文本
        "label_details": [...],        # 情感标签详情
        "metaphor_violations": [...],
        "info_dumps": [...]
    }
    """
    narrative = strip_dialogue(text)

    # 情感标签 (tell)
    label_details = _find_emotion_labels(narrative)
    emotion_label_count = len(label_details)

    # 动作传情 (show)
    action_details = _find_action_emotions(narrative)
    action_count = len(action_details)

    # 展示/告知比率
    show_tell_ratio = action_count / (emotion_label_count + 1)

    # 比喻密度
    metaphor_violations = _check_metaphor_density(text)

    # 信息倾销
    info_dumps = _check_info_dumps(text)

    passed = (
        show_tell_ratio >= ratio_threshold
        and len(metaphor_violations) == 0
        and len(info_dumps) == 0
    )

    return {
        'passed': passed,
        'show_tell_ratio': round(show_tell_ratio, 2),
        'emotion_labels': emotion_label_count,
        'action_emotions': action_count,
        'action_details': action_details,
        'label_details': label_details,
        'metaphor_violations': metaphor_violations,
        'info_dumps': info_dumps,
    }


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------

def _print_human(result: dict, threshold: float, show_fix: bool) -> None:
    """人类可读的输出格式。"""
    if result['passed']:
        print(f'✓ 情感展示检测通过')
        print(f'  展示/告知比率: {result["show_tell_ratio"]} (阈值: {threshold})')
        print(f'  动作传情: {result["action_emotions"]} 处')
        print(f'  情感标签: {result["emotion_labels"]} 处')
        return

    ratio = result['show_tell_ratio']
    print(f'✗ 情感展示检测未通过:')

    # 展示/告知比率
    ratio_pass = ratio >= threshold
    marker = '  ' if ratio_pass else '  '
    print(f'{marker}展示/告知比率: {ratio} (阈值: {threshold})')

    action_str = ', '.join(result['action_details']) if result['action_details'] else '无'
    print(f'    动作传情: {result["action_emotions"]} 处 ({action_str})')
    print(f'    情感标签: {result["emotion_labels"]} 处')

    for label in result['label_details']:
        pos = label['pos']
        snippet = label['text']
        print(f'      [pos {pos}] "{snippet}"')

    # 比喻密度
    for v in result['metaphor_violations']:
        if v['type'] == 'density':
            words_str = ', '.join(v['words'])
            print(f'  比喻密度: 第{v["paragraph"]}段有{v["count"]}个比喻词 ({words_str})')
        elif v['type'] == 'describe_then_simile':
            print(f'  比喻模式: 第{v["paragraph"]}段先描写后比喻 "{v["text"]}"')

    # 信息倾销
    for d in result['info_dumps']:
        if d['start_paragraph'] == d['end_paragraph']:
            print(f'  信息倾销: 第{d["start_paragraph"]}段连续{d["chars"]}字无对话')
        else:
            print(f'  信息倾销: 第{d["start_paragraph"]}-{d["end_paragraph"]}段连续{d["chars"]}字无对话')

    if show_fix:
        print()
        print('修复建议: 用动作和感官替代情感标签，删除重复比喻，在长段叙事中插入对话或动作节拍。')


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='情感展示检测工具')
    parser.add_argument('file', help='正文文件路径')
    parser.add_argument('--json', action='store_true', dest='json_output',
                        help='输出 JSON 格式结果')
    parser.add_argument('--fix', action='store_true',
                        help='输出修复建议')
    parser.add_argument('--threshold', type=float, default=2.0,
                        help='展示/告知比率的最低阈值（默认 2.0）')
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

    result = check(text, args.threshold)

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_human(result, args.threshold, args.fix)

    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
