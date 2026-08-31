#!/usr/bin/env python3
"""
翻译腔检测工具

检测中文小说中的翻译腔问题，包括冗长定语链、被动语态滥用、代词复指、
空泛动词、抽象名词主语等典型翻译腔特征。

使用方式：
    python tools/translationese_checker.py <正文文件路径> [--json] [--fix]

    --json    以 JSON 格式输出结果
    --fix     输出修复建议

退出码：
    0 — 全部通过
    1 — 存在翻译腔问题
    2 — 文件错误
"""

import argparse
import json
import re
import sys
from pathlib import Path


def strip_dialogue(text: str) -> str:
    """移除对话内容，只保留叙述文本。"""
    return re.sub(r'[""「][^""」]+[""」]', '', text)


def _context(text: str, pos: int, window: int = 30) -> str:
    """取 pos 前后 window 个字符作为上下文片段。"""
    start = max(0, pos - window)
    end = min(len(text), pos + window)
    return text[start:end]


def _split_sentences(text: str) -> list[tuple[str, int]]:
    """按 。！？ 拆句，返回 (句子文本, 起始位置) 列表。"""
    results = []
    last = 0
    for m in re.finditer(r'[。！？]', text):
        sent = text[last:m.end()].strip()
        if sent:
            results.append((sent, last))
        last = m.end()
    # 末尾无标点的残余
    if last < len(text):
        tail = text[last:].strip()
        if tail:
            results.append((tail, last))
    return results


def check_de_chain(text: str) -> dict:
    """规则1: "的"定语链 —— 3个以上"的"连续修饰。"""
    narrative = strip_dialogue(text)
    pattern = re.compile(r'的[^，。！？\n]{1,15}的[^，。！？\n]{1,15}的')
    items = []
    for m in pattern.finditer(narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start())})
    return {
        'rule': '的定语链',
        'count': len(items),
        'items': items,
    }


def check_passive_voice(text: str) -> dict:
    """规则2: 被动语态密度 —— 每1000字中"被"出现超过3次。"""
    narrative = strip_dialogue(text)
    char_count = len(narrative)
    if char_count == 0:
        return {'rule': '被动语态密度', 'count': 0, 'items': [], 'density': 0.0}
    hits = list(re.finditer(r'被', narrative))
    density = len(hits) / char_count * 1000
    items = [{'position': m.start(), 'context': _context(narrative, m.start())} for m in hits]
    return {
        'rule': '被动语态密度',
        'count': len(hits),
        'items': items,
        'density': round(density, 2),
        'threshold': 3.0,
    }


def check_pronoun_repetition(text: str) -> dict:
    """规则3: 代词复指 —— 3个以上连续句子以相同代词开头。"""
    narrative = strip_dialogue(text)
    sentences = _split_sentences(narrative)
    pronouns = ('他', '她', '它', '他们', '她们')
    items = []
    streak_start = 0
    streak_pronoun = None

    for i, (sent, pos) in enumerate(sentences):
        matched = None
        for p in sorted(pronouns, key=len, reverse=True):
            if sent.startswith(p):
                matched = p
                break
        if matched and matched == streak_pronoun:
            continue
        else:
            # 结束前一段连续
            if streak_pronoun and (i - streak_start) >= 3:
                streak_sents = sentences[streak_start:i]
                preview = ' → '.join(s[:20] for s, _ in streak_sents)
                items.append({
                    'position': streak_sents[0][1],
                    'context': preview,
                    'streak': i - streak_start,
                    'pronoun': streak_pronoun,
                })
            streak_start = i
            streak_pronoun = matched

    # 处理末尾
    if streak_pronoun and (len(sentences) - streak_start) >= 3:
        streak_sents = sentences[streak_start:]
        preview = ' → '.join(s[:20] for s, _ in streak_sents)
        items.append({
            'position': streak_sents[0][1],
            'context': preview,
            'streak': len(sentences) - streak_start,
            'pronoun': streak_pronoun,
        })

    return {
        'rule': '代词复指',
        'count': len(items),
        'items': items,
    }


def check_empty_verbs(text: str) -> dict:
    """规则4: 空泛动词 + 名词结构。"""
    narrative = strip_dialogue(text)
    patterns = [
        (r'进行[^\s，。！？]{1,6}?(研究|调查|分析|讨论|评估)', '进行+名词'),
        (r'作出[^\s，。！？]{1,6}?(贡献|决定|选择|判断)', '作出+名词'),
        (r'加以[^\s，。！？]{1,6}?(解决|改善|利用)', '加以+名词'),
        (r'给予[^\s，。！？]{1,6}?(帮助|支持|关注)', '给予+名词'),
        (r'实施[^\s，。！？]{1,6}?(打击|制裁|控制)', '实施+名词'),
    ]
    items = []
    for pat, label in patterns:
        for m in re.finditer(pat, narrative):
            items.append({
                'position': m.start(),
                'context': _context(narrative, m.start()),
                'label': label,
            })
    return {
        'rule': '空泛动词+名词',
        'count': len(items),
        'items': items,
    }


def check_abstract_noun_subject(text: str) -> dict:
    """规则5: 抽象名词作主语。"""
    narrative = strip_dialogue(text)
    patterns = [
        r'他的(到来|离去|出现|消失|决定|选择|成长|改变|死亡)[^，。]{0,5}?(让|使|令)',
        r'这(个)?(问题|决定|选择|方案|方法|想法|观点)[^，。]{0,5}?(让|使|令|是)',
    ]
    items = []
    for pat in patterns:
        for m in re.finditer(pat, narrative):
            items.append({
                'position': m.start(),
                'context': _context(narrative, m.start()),
            })
    return {
        'rule': '抽象名词主语',
        'count': len(items),
        'items': items,
    }


def check_zhiyi_overuse(text: str) -> dict:
    """规则6: "之一"滥用 —— 全文超过2次。"""
    items = []
    for m in re.finditer(r'之一', text):
        items.append({'position': m.start(), 'context': _context(text, m.start())})
    return {
        'rule': '之一滥用',
        'count': len(items),
        'items': items,
        'threshold': 2,
    }


def check_shi_de_structure(text: str) -> dict:
    """规则7: "是...的"结构。"""
    narrative = strip_dialogue(text)
    pattern = re.compile(r'是[^\s，。！？]{1,10}?(做|写|说|买|卖|完成|做出|进行|创造)的')
    items = []
    for m in pattern.finditer(narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start())})
    return {
        'rule': '是…的结构',
        'count': len(items),
        'items': items,
    }


def check_conjunction_density(text: str) -> dict:
    """规则8: 连词密度 —— 每1000字超过5个。"""
    narrative = strip_dialogue(text)
    char_count = len(narrative)
    if char_count == 0:
        return {'rule': '连词密度', 'count': 0, 'items': [], 'density': 0.0}

    simple_conjunctions = ['虽然', '但是', '因为', '所以', '如果', '那么']
    items = []
    for cj in simple_conjunctions:
        for m in re.finditer(re.escape(cj), narrative):
            items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': cj})

    # 不仅...而且
    for m in re.finditer(r'不仅', narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': '不仅…而且'})
    for m in re.finditer(r'而且', narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': '不仅…而且'})
    # 一方面...另一方面
    for m in re.finditer(r'一方面', narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': '一方面…另一方面'})
    for m in re.finditer(r'另一方面', narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': '一方面…另一方面'})
    # 当...的时候
    for m in re.finditer(r'当[^，。！？\n]{1,20}?(的时候|时)', narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': '当…时(候)'})

    density = len(items) / char_count * 1000
    return {
        'rule': '连词密度',
        'count': len(items),
        'items': items,
        'density': round(density, 2),
        'threshold': 5.0,
    }


def check_adjective_colon(text: str) -> dict:
    """规则9: 形容词+冒号引导读者预判。"""
    pattern = re.compile(r'(?:逻辑|原因|结论|答案|结果|道理|真相)(?:很|非常)?(?:清晰|明确|简单|清楚|明显)：')
    items = []
    for m in pattern.finditer(text):
        items.append({'position': m.start(), 'context': _context(text, m.start())})
    return {
        'rule': '形容词+冒号预判',
        'count': len(items),
        'items': items,
    }


def check_preposition_stacking(text: str) -> dict:
    """规则10: "作为"和"在"介词堆叠 —— 每1000字超过3个。"""
    narrative = strip_dialogue(text)
    char_count = len(narrative)
    if char_count == 0:
        return {'rule': '介词堆叠', 'count': 0, 'items': [], 'density': 0.0}

    items = []
    for m in re.finditer(r'作为[^，。！？\n]{1,15}的[^，。！？\n]{1,10}', narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': '作为…的…'})
    for m in re.finditer(r'在[^，。！？\n]{1,15}?(之后|之前|之中|之际|之时)', narrative):
        items.append({'position': m.start(), 'context': _context(narrative, m.start()), 'word': '在…之后/之前/之中/之际/之时'})

    density = len(items) / char_count * 1000
    return {
        'rule': '介词堆叠',
        'count': len(items),
        'items': items,
        'density': round(density, 2),
        'threshold': 3.0,
    }


def check(text: str) -> list[dict]:
    """运行全部检测，返回违规列表。"""
    results = [
        check_de_chain(text),
        check_passive_voice(text),
        check_pronoun_repetition(text),
        check_empty_verbs(text),
        check_abstract_noun_subject(text),
        check_zhiyi_overuse(text),
        check_shi_de_structure(text),
        check_conjunction_density(text),
        check_adjective_colon(text),
        check_preposition_stacking(text),
    ]

    violations = []
    for r in results:
        rule = r['rule']
        count = r['count']
        if rule == '被动语态密度':
            if r.get('density', 0) > r.get('threshold', 3.0):
                violations.append(r)
        elif rule == '之一滥用':
            if count > r.get('threshold', 2):
                violations.append(r)
        elif rule == '连词密度':
            if r.get('density', 0) > r.get('threshold', 5.0):
                violations.append(r)
        elif rule == '介词堆叠':
            if r.get('density', 0) > r.get('threshold', 3.0):
                violations.append(r)
        elif rule == '代词复指':
            if count > 0:
                violations.append(r)
        else:
            if count > 0:
                violations.append(r)

    return violations


def main():
    parser = argparse.ArgumentParser(description='翻译腔检测工具')
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
    except OSError as e:
        print(f'读取文件失败: {e}', file=sys.stderr)
        sys.exit(2)

    violations = check(text)

    if args.json_output:
        output = {
            'passed': len(violations) == 0,
            'violations': violations,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not violations:
            print('✓ 翻译腔检测通过')
            sys.exit(0)

        print(f'✗ 发现 {len(violations)} 类翻译腔问题:')
        for i, v in enumerate(violations, 1):
            print(f'\n  [{i}] {v["rule"]}（{v["count"]}处）')
            if 'density' in v:
                print(f'      密度: {v["density"]}/1000字（阈值: {v.get("threshold", "N/A")}）')
            if 'streak' in v.get('items', [{}])[0] if v['items'] else {}:
                for item in v['items']:
                    print(f'      连续{item["streak"]}句以"{item["pronoun"]}"开头: {item["context"][:60]}')
            else:
                for item in v['items'][:5]:
                    label = item.get('label', '')
                    word = item.get('word', '')
                    tag = f' [{label}]' if label else (f' [{word}]' if word else '')
                    print(f'      …{item["context"]}…{tag}')
                if len(v['items']) > 5:
                    print(f'      …另有 {len(v["items"]) - 5} 处省略')

    if args.fix:
        print('\n修复建议: 拆句、换主动语态、省略主语、用中文口语习惯重写。')

    sys.exit(1 if violations else 0)


if __name__ == '__main__':
    main()
