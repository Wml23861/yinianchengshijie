# -*- coding: utf-8 -*-
"""补扫：机械三段式、连续同构句、金句密度。"""
import re, glob, os

BASE = r'e:\心界\yinianchengshijie\novel\正文\01_第一卷_入道\01_第一时代_尘中少年'

JINJU = [
    r'真正的[\u4e00-\u9fff]{0,6}',
    r'原来[\u4e00-\u9fff]{0,6}',
    r'人生[\u4e00-\u9fff]{0,4}就是',
    r'所谓[\u4e00-\u9fff]{0,6}',
    r'他终于[\u4e00-\u9fff]{0,8}明白',
    r'他忽然意识到',
    r'这一刻[，,]他终于',
    r'他深吸[了]?一口气',
    r'沉默良久',
    r'嘴角露出一丝笑容',
    r'不由得[\u4e00-\u9fff]{0,4}',
]
JINJU_RE = re.compile('|'.join(JINJU))

def main():
    files = sorted(glob.glob(os.path.join(BASE, '*.md')))
    print(f"{'章号':<6}{'机械三段式':<12}{'连续同构':<12}{'金句总数':<10}")
    print('-'*40)
    for f in files:
        name = os.path.basename(f)
        chap = re.match(r'(\d+)_', name).group(1)
        t = open(f, encoding='utf-8').read()
        lines = t.split('\n')

        # 1. 机械三段式
        san = 0
        san_hits = []
        for ln, line in enumerate(lines, 1):
            if not line.strip():
                continue
            # "X。X。X。" 形式：连续 3+ 个句号，每个片段都 <15 字
            sents = re.split(r'[。？！…]', line)
            for i in range(len(sents)-2):
                s1, s2, s3 = sents[i], sents[i+1], sents[i+2]
                if all(0 < len(s1.strip()) <= 12 and 0 < len(s2.strip()) <= 12 and 0 < len(s3.strip()) <= 12 for _ in [0]):
                    if s1.strip() and s2.strip() and s3.strip():
                        san += 1
                        san_hits.append(f"L{ln}:{s1.strip()[:8]}|{s2.strip()[:8]}|{s3.strip()[:8]}")
                        break
            # "不是X不是X而是X"
            if re.search(r'不是[^。？！…]{0,8}不是[^。？！…]{0,8}而是', line):
                san += 1
                san_hits.append(f"L{ln}:不是X不是X而是X")
            # "过去X现在X未来X"
            if re.search(r'(过去|曾经)[^。？！…]{0,12}(现在|如今)[^。？！…]{0,12}(未来|以后)', line):
                san += 1
                san_hits.append(f"L{ln}:过去现在未来")
            # "没有X没有X只是X"
            if re.search(r'没有[^。？！…]{0,8}没有[^。？！…]{0,8}只[是的有]', line):
                san += 1
                san_hits.append(f"L{ln}:没有X没有X只是X")

        # 2. 连续同构句（"X看着A。X看着B。X看着C。"）同主语+动宾结构 3+
        iso = 0
        iso_hits = []
        for ln, line in enumerate(lines, 1):
            if not line.strip():
                continue
            sents = [s.strip() for s in re.split(r'[。？！…]', line) if s.strip()]
            for i in range(len(sents)-2):
                p1, p2, p3 = sents[i], sents[i+1], sents[i+2]
                # 简单规则：去掉尾巴名词短语，前 4 字相同
                t1 = re.sub(r'[\u4e00-\u9fff]{0,3}$', '', p1)
                t2 = re.sub(r'[\u4e00-\u9fff]{0,3}$', '', p2)
                t3 = re.sub(r'[\u4e00-\u9fff]{0,3}$', '', p3)
                if len(t1) >= 4 and t1 == t2 == t3:
                    iso += 1
                    iso_hits.append(f"L{ln}:{p1[:12]}|{p2[:12]}|{p3[:12]}")
                    break

        # 3. 金句密度
        jin = 0
        jin_hits = []
        for ln, line in enumerate(lines, 1):
            for m in JINJU_RE.finditer(line):
                jin += 1
                jin_hits.append(f"L{ln}:{m.group()[:14]}")

        flag_san = '*' if san else ''
        flag_iso = '*' if iso else ''
        flag_jin = '*' if jin else ''
        print(f"{chap:<6}{str(san)+flag_san:<12}{str(iso)+flag_iso:<12}{str(jin)+flag_jin:<10}")
        if san_hits[:5]:
            for h in san_hits[:5]: print(f"      机械三段式: {h}")
        if iso_hits[:5]:
            for h in iso_hits[:5]: print(f"      连续同构: {h}")
        if jin_hits[:5]:
            for h in jin_hits[:5]: print(f"      金句: {h}")

if __name__ == '__main__':
    main()
