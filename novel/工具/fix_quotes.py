# 自动修复半角引号
import re, sys

path = r'E:/心界/yinianchengshijie/novel/正文/01_第一卷_入道/01_第一时代_尘中少年/17_第十七章_糖葫芦.md'
with open(path, encoding='utf-8') as f:
    text = f.read()

# 替换半角引号为全角引号（交替左/右）
result = []
in_quote = False
for ch in text:
    if ch == chr(34):
        if not in_quote:
            result.append(chr(0x201c))
        else:
            result.append(chr(0x201d))
        in_quote = not in_quote
    else:
        result.append(ch)
text = ''.join(result)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("半角引号替换完成")
lq = text.count(chr(0x201c))
rq = text.count(chr(0x201d))
print("全角左:", lq, "全角右:", rq)
