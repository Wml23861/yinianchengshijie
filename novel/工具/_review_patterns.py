import re
import os

chapters = {
    '51': '51_第五十一章_南门桥',
    '52': '52_第五十二章_早市',
    '53': '53_第五十三章_候诊',
    '54': '54_第五十四章_超市',
    '55': '55_第五十五章_搬家',
    '56': '56_第五十六章_老家',
}

base = 'novel/正文/01_第一卷_入道/01_第一时代_尘中少年/'

for num, name in chapters.items():
    path = base + name + '.md'
    if not os.path.exists(path):
        print(f'!!! {path} not found')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
    print(f'\n========== 51-56 第 {num} 章 ==========')

    # 沙发同构（独立段）
    print('-- 沙发相关行 --')
    for i, l in enumerate(lines, 1):
        if '沙发' in l:
            print(f'L{i}: {l[:80]}')

    # 63岁
    print('-- 63岁/六十三 --')
    for i, l in enumerate(lines, 1):
        if '六十三' in l or '63' in l:
            print(f'L{i}: {l[:80]}')

    # 心儿
    print('-- 心儿 --')
    for i, l in enumerate(lines, 1):
        if '心儿' in l:
            print(f'L{i}: {l[:80]}')

    # 纸袋
    print('-- 纸袋/床底靠墙 --')
    for i, l in enumerate(lines, 1):
        if '纸袋' in l or '床底' in l:
            print(f'L{i}: {l[:80]}')

    # 酱油
    print('-- 酱油 --')
    for i, l in enumerate(lines, 1):
        if '酱油' in l:
            print(f'L{i}: {l[:80]}')

    # 体检
    print('-- 体检 --')
    for i, l in enumerate(lines, 1):
        if '体检' in l:
            print(f'L{i}: {l[:80]}')

    # 脚底软
    print('-- 脚底软 --')
    for i, l in enumerate(lines, 1):
        if '脚底' in l and '软' in l:
            print(f'L{i}: {l[:80]}')

    # 水是凉的
    print('-- 水是凉的 --')
    for i, l in enumerate(lines, 1):
        if '水是凉' in l or '凉的水' in l:
            print(f'L{i}: {l[:80]}')

    # 不知道为了什么
    print('-- 不知道为什么 --')
    for i, l in enumerate(lines, 1):
        if '也不知道是为了什么' in l or '不知道是为了什么' in l:
            print(f'L{i}: {l[:80]}')

    # 缓缓
    print('-- 缓缓 --')
    for i, l in enumerate(lines, 1):
        if '缓缓' in l:
            print(f'L{i}: {l[:80]}')

    # 吊兰
    print('-- 吊兰 --')
    for i, l in enumerate(lines, 1):
        if '吊兰' in l:
            print(f'L{i}: {l[:80]}')

    # 棉袄
    print('-- 棉袄 --')
    for i, l in enumerate(lines, 1):
        if '棉袄' in l:
            print(f'L{i}: {l[:80]}')

    # 鞋柜
    print('-- 鞋柜 --')
    for i, l in enumerate(lines, 1):
        if '鞋柜' in l:
            print(f'L{i}: {l[:80]}')
