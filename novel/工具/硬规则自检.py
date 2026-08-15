# -*- coding: utf-8 -*-
"""
硬规则自检脚本（机器强制，不靠 AI 自觉）
用法：
  python 硬规则自检.py                 # 扫第一时代目录下全部章节
  python 硬规则自检.py 01_第一章_深夜两点.md   # 指定文件
输出：每章硬规则数据 + 通过/不通过。任一硬规则失败 → 退出码 1。
审核者 B 审任何章，必须先跑本脚本并把输出贴进审核记录；没有输出 = 没跑 = 打回。
"""
import re, glob, sys, os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', '正文', '01_第一卷_入道', '01_第一时代_尘中少年')

def check(path):
    t = open(path, encoding='utf-8').read()
    lines = t.split('\n')
    body = '\n'.join(lines[1:]) if len(lines) > 1 else ''
    r = {}
    r['汉字'] = len(re.findall(r'[\u4e00-\u9fff]', body))
    r['破折号'] = len(re.findall(r'[——–—－]', t))
    r['英文'] = len(re.findall(r'[A-Za-z]', t))
    r['半角引号'] = body.count(chr(34))
    r['全角左'] = body.count('\u201c')
    r['全角右'] = body.count('\u201d')
    r['半角标点'] = len(re.findall(r'[,.;:!?]', body))
    r['忽然类'] = len(re.findall(r'忽然|这一刻|仿佛|真正的|原来', body))
    r['缓缓类'] = len(re.findall(r'缓缓|轻轻|静静|慢慢', body))
    r['越越'] = len(re.findall(r'越.{0,3}越', body))
    r['不是X是Y'] = len(re.findall(r'不是[^。]{0,12}是', body))
    fails = []
    if r['汉字'] < 2800: fails.append(f"字数不足 {r['汉字']}<2800")
    if r['破折号'] > 0: fails.append(f"破折号 {r['破折号']}>0")
    if r['英文'] > 0: fails.append(f"英文 {r['英文']}>0")
    if r['半角引号'] > 0: fails.append(f"半角引号 {r['半角引号']}>0")
    if r['全角左'] != r['全角右']: fails.append(f"全角引号不成对 {r['全角左']}≠{r['全角右']}")
    if r['半角标点'] > 0: fails.append(f"半角标点 {r['半角标点']}>0")
    return r, fails

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) > 1:
        files = [sys.argv[1]]
        if not os.path.exists(files[0]):
            files = [os.path.join(BASE, sys.argv[1])]
    else:
        files = sorted(glob.glob(os.path.join(BASE, '*.md')))
    if not files:
        print('未找到章节文件'); sys.exit(2)
    any_fail = False
    for f in files:
        r, fails = check(f)
        name = os.path.basename(f)
        print(f"{name}")
        print(f"  汉字={r['汉字']} 破折号={r['破折号']} 英文={r['英文']} "
              f"半角引号={r['半角引号']} 全角“{r['全角左']}/”{r['全角右']} 半角标点={r['半角标点']}")
        print(f"  忽然类={r['忽然类']} 缓缓类={r['缓缓类']} 越越={r['越越']} 不是X是Y={r['不是X是Y']}")
        if fails:
            any_fail = True
            for x in fails: print(f"  [X] {x}")
        else:
            print("  [OK] 硬规则全过")
    print("=" * 40)
    print("不通过" if any_fail else "全部通过")
    sys.exit(1 if any_fail else 0)

if __name__ == '__main__':
    main()
