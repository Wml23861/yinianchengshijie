# -*- coding: utf-8 -*-
"""
硬规则自检脚本（机器强制，不靠 AI 自觉）
用法：
  python 硬规则自检.py                 # 扫第一时代目录下全部章节
  python 硬规则自检.py 01_第一章_深夜两点.md   # 指定文件
输出：每章硬规则数据 + 通过/不通过。任一硬规则失败 → 退出码 1。
字数口径（2026-08-15 定；2026-09-02 修订）：字数=汉字+标点（不含数字/英文），<3000 硬失败（旧 2800 已作废），>3300 软警告。
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
    r['方头括号'] = body.count('「') + body.count('」')
    r['忽然类'] = len(re.findall(r'忽然|这一刻|仿佛|真正的|原来', body))
    r['缓缓类'] = len(re.findall(r'缓缓|轻轻|静静|慢慢', body))
    r['越越'] = len(re.findall(r'越.{0,3}越', body))
    r['不是X是Y'] = len(re.findall(r'不是[^。]{0,12}是', body))
    # 2026-09-03 新加：心界场景软提示（不是硬关，参考下限）
    # 收紧：只用真正的心界标记词（避免"城里/街上"等误中）
    r['心界标记'] = len(re.findall(r'心界|王城|心国|五蕴|心内|梦境|梦里|进了城|进王城|进了王城|进宫|进殿|守卒|城门|城墙|将军|问天童|受纳侯|识海侯|行愿侯|想象侯|色相侯|赤炎|金算盘|高台侯|无厌侯|守门官|记账先生|和事官|缩影童子|白玉相|天衡子|疑川|急行人|回首翁|青灯|慈舟|借舟客|万花使|镇国公|雾先生|夜行客|货郎|撑伞|卖秤|称心|号序|盐官|搬空|守山|补漏|账目|等归|五味', body))
    r['字数'] = len(re.findall(r'[^\s0-9０-９A-Za-z]', body))  # 字数=汉字+标点，不含数字/英文
    fails = []
    warns = []
    if r['字数'] < 3000: fails.append(f"字数不足 {r['字数']}<3000（2026-09-02 修订：硬下限 3000，旧 2800 已作废）")
    if r['字数'] > 3300: warns.append(f"字数超3300 {r['字数']}>3300（软上限，见CLAUDE.md第七十四条，由审核者判断）")
    if r['破折号'] > 0: fails.append(f"破折号 {r['破折号']}>0")
    if r['英文'] > 0: fails.append(f"英文 {r['英文']}>0")
    if r['半角引号'] > 0: fails.append(f"半角引号 {r['半角引号']}>0")
    if r['全角左'] != r['全角右']: fails.append(f"全角引号不成对 {r['全角左']}≠{r['全角右']}")
    if r['半角标点'] > 0: fails.append(f"半角标点 {r['半角标点']}>0")
    if r['方头括号'] > 0: fails.append(f"方头括号「」{r['方头括号']}>0（禁用做引号，见52手册§3）")
    # 连续句号铁律（最高优先级，见 CLAUDE.md 第五十一条附）：
    # ① 一个自然段句末符（。？！…）最多 3 个（含对话引号内，与段落自检.sh 一致）；
    # ② 单句逗号（，）最多 3 个（含对话引号内）；
    # ③ 叙述中禁止「短句。+ 后句」的碎片化断句（对话引号内不参与③）。
    for ln, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        # 52 手册格式检测（2026-09-01 硬关化）
        # A. 段首是句号
        if line.startswith('。'):
            fails.append(f"段首是句号（第{ln}行，见52手册§2.1）")
        # B. 对话未独立成段：一行 ≥3 对全角""（6 个引号 = 3 句对话挤一行）
        n_quotes = line.count('“') + line.count('”')
        if n_quotes >= 6:
            fails.append(f"对话未独立成段（第{ln}行，{n_quotes//2}对引号挤一行，见52手册§1.1）")
        n_sent = len(re.findall(r'[。？！…]', line))
        if n_sent > 3:
            fails.append(f"段落句号超3（第{ln}行 {n_sent}个）")
        for sent in re.split(r'[。？！…]', line):
            if sent.count('，') > 3:
                fails.append(f"单句逗号超3（第{ln}行 {sent.count('，')}个）")
        narr = re.sub(r'“[^”]*”', '', line)
        sents = [s for s in re.split(r'[。？！…]', narr) if s.strip()]
        for s in sents[:-1]:
            ss = s.strip()
            if not re.search(r'[，、：]', ss) and len(ss) <= 10:
                fails.append(f"碎片化断句（第{ln}行「{ss[:12]}」后接句号）")
        # 对话形式检测：禁止"X说……X说……X说"连用 3+ 次
        # 一段内"说"动词出现 ≥3 次且无任何"问/答/嗯/停/没接/想了一下/抬头/低头/笑/摇头"等打断 → 警告
        if '说' in line:
            says = len(re.findall(r'(?:明心|老人|女人|老头|母亲|父亲|明心她妈|她妈|小刘|小吴|他|她|小伙子|老头儿)[^，。、；：？！]*?说', line))
            if says >= 4:
                warns.append(f"对话「说」动词过密（第{ln}行 {says}次，建议加动作/停顿/非'说'动词，见CLAUDE.md卷五·七）")
            if says >= 3:
                breakers = ['问', '答', '嗯', '停', '没接', '想了一下', '抬头', '低头', '笑', '摇头', '喊', '催', '嘀咕', '重复', '插嘴', '岔开', '追问']
                if not any(b in line for b in breakers):
                    warns.append(f"对话「说」连用无打断（第{ln}行 {says}次，需加动作/停顿/非'说'动词，见CLAUDE.md卷五·七）")
    # 上下文一致性检测：父母住址（CLAUDE.md卷五·八）
    # 已确立：明心父母住在老家，不在城里
    if re.search(r'我妈在城南|我妈在城西|我妈在城北|我妈在城东|他父母在城南|他父母在城西|他父母在城北|他父母在城东', body):
        fails.append("父母住址与设定矛盾（父母在老家，不在城里，见CLAUDE.md卷五·八）")
    # 2026-09-03 新加：心界场景软提示（不强制——纯日常章/纯现实章合法，但 10 章内 ≥ 8 章必有心界）
    if r['心界标记'] == 0:
        warns.append(f"本章未检到心界场景标记（心界标记={r['心界标记']}，参考下限：最近 10 章 ≥ 8 章有心界；纯日常章/纯现实章可登记 0+理由，但不可连续 5+ 章为 0，见CLAUDE.md卷十·七）")
    return r, fails, warns

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
        r, fails, warns = check(f)
        name = os.path.basename(f)
        print(f"{name}")
        print(f"  字数={r['字数']} 汉字={r['汉字']} 破折号={r['破折号']} 英文={r['英文']} "
              f"半角引号={r['半角引号']} 全角“{r['全角左']}/”{r['全角右']} 半角标点={r['半角标点']} "
              f"方头括号={r['方头括号']}")
        print(f"  忽然类={r['忽然类']} 缓缓类={r['缓缓类']} 越越={r['越越']} 不是X是Y={r['不是X是Y']} 心界标记={r['心界标记']}")
        for w in warns: print(f"  [警告] {w}")
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
