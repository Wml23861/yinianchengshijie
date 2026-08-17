#!/usr/bin/env bash
export LANG=C.UTF-8
file="${1:?用法: $0 <章节文件路径>}"

line_no=0
para_no=0
max_period=0
max_comma=0
fail_period=0
fail_comma=0

while IFS= read -r line || [[ -n "$line" ]]; do
  (( line_no++ ))
  [[ -z "$line" ]] && continue
  # skip title line
  if (( line_no == 1 )); then continue; fi
  (( para_no++ ))
  pe=0
  len=${#line}
  for (( i=0; i<len; i++ )); do
    ch="${line:$i:1}"
    case "$ch" in
      '。'|'？'|'！'|'…') (( pe++ )) ;;
    esac
  done
  if (( pe > 3 )); then
    echo "段落句号超3 第$line_no行 ${pe}个句末符"
    (( fail_period++ ))
  fi
  if (( pe > max_period )); then max_period=$pe; fi
  # count commas per sentence, split by 。 ？ ！ …
  # replace endings with newline and iterate
  sent_str="${line//。/$'\n'}"
  sent_str="${sent_str//？/$'\n'}"
  sent_str="${sent_str//！/$'\n'}"
  sent_str="${sent_str//…/$'\n'}"
  while IFS= read -r sent; do
    [[ -z "$sent" ]] && continue
    cc=0
    slen=${#sent}
    for (( j=0; j<len; j++ )); do
      cch="${sent:$j:1}"
      if [[ "$cch" == "，" ]]; then (( cc++ )); fi
    done
    if (( cc > 3 )); then
      echo "单句逗号超3 第$line_no行 ${cc}个逗号"
      (( fail_comma++ ))
    fi
    if (( cc > max_comma )); then max_comma=$cc; fi
  done <<< "$sent_str"
done < "$file"

echo "段落数=$para_no 最大句末符=$max_period 最大单句逗号=$max_comma"
if (( fail_period == 0 && fail_comma == 0 )); then
  echo "[OK] 段落句号/单句逗号检查通过"
else
  echo "[X] 段落句号超标${fail_period}处，单句逗号超标${fail_comma}处"
fi
