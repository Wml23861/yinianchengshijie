#!/usr/bin/env bash
# 硬规则自检（bash 版，python 不可用时用；用法: ./硬规则自检.sh <章节文件路径>）
export LANG=C.UTF-8

file="${1:?用法: $0 <章节文件路径>}"

c_total=0
c_dash=0
c_eng=0
c_halfq=0
c_fl=0
c_fr=0
c_halfp=0
c_huran=0
c_huan=0
c_yue=0
c_bushi=0

first=1
while IFS= read -r line || [[ -n "$line" ]]; do
  if (( first )); then
    first=0
    continue
  fi

  len=${#line}
  for (( i=0; i<len; i++ )); do
    ch="${line:$i:1}"
    # count chars that are not whitespace/ascii digit/ascii letter
    case "$ch" in
      [[:space:]]|[0-9]|[A-Za-z]) ;;
      *) (( c_total++ )) ;;
    esac
    case "$ch" in
      '—'|'–'|'—'|'－') (( c_dash++ )) ;;
    esac
    case "$ch" in
      [A-Za-z]) (( c_eng++ )) ;;
    esac
    case "$ch" in
      '\"') (( c_halfq++ )) ;;
    esac
    case "$ch" in
      '“') (( c_fl++ )) ;;
      '”') (( c_fr++ )) ;;
    esac
    case "$ch" in
      ','|'.'|';'|':'|'!'|'?') (( c_halfp++ )) ;;
    esac
  done

  # regex-based counts over the whole line
  tmp="$line"
  while [[ $tmp =~ 忽然|这一刻|仿佛|真正的|原来 ]]; do
    (( c_huran++ ))
    tmp="${tmp#*${BASH_REMATCH[0]}}"
  done
  tmp="$line"
  while [[ $tmp =~ 缓缓|轻轻|静静|慢慢 ]]; do
    (( c_huan++ ))
    tmp="${tmp#*${BASH_REMATCH[0]}}"
  done
  tmp="$line"
  while [[ $tmp =~ 越.{0,3}越 ]]; do
    (( c_yue++ ))
    tmp="${tmp#*${BASH_REMATCH[0]}}"
  done
  tmp="$line"
  while [[ $tmp =~ 不是[^。]{0,12}是 ]]; do
    (( c_bushi++ ))
    tmp="${tmp#*${BASH_REMATCH[0]}}"
  done
done < "$file"

echo "file: $file"
echo "字数=$c_total"
echo "破折号=$c_dash"
echo "英文=$c_eng"
echo "半角引号=$c_halfq"
echo "全角左=$c_fl 全角右=$c_fr"
echo "半角标点=$c_halfp"
echo "忽然类=$c_huran"
echo "缓缓类=$c_huan"
echo "越越=$c_yue"
echo "不是X是Y=$c_bushi"

fail=0
if (( c_total < 2800 )); then echo "[X] 字数不足 $c_total<2800"; fail=1; fi
if (( c_total > 3300 )); then echo "[警告] 字数超3300 $c_total"; fi
if (( c_dash > 0 )); then echo "[X] 破折号 $c_dash>0"; fail=1; fi
if (( c_eng > 0 )); then echo "[X] 英文 $c_eng>0"; fail=1; fi
if (( c_halfq > 0 )); then echo "[X] 半角引号 $c_halfq>0"; fail=1; fi
if (( c_fl != c_fr )); then echo "[X] 全角引号不成对 $c_fl≠$c_fr"; fail=1; fi
if (( c_halfp > 0 )); then echo "[X] 半角标点 $c_halfp>0"; fail=1; fi
if (( fail == 0 )); then echo "[OK] 硬规则全过"; fi
