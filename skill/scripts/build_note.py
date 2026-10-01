#!/usr/bin/env python3
"""把字幕词条 JSON 编译成 A4 预习笔记：自包含 HTML + Markdown 摘要。仅用标准库。"""
import argparse
import html
import json
import re
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'assets' / 'note.html'
BANDS = ('超纲实词', '短语搭配', '俚语口语', '派生词')
ENTRY_REQUIRED = ('term', 'ipa', 'pos', 'meaning', 'sentence', 'translation')


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} 必须是非空字符串')
    return value.strip()


def strlist(value, field):
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f'{field} 必须是非空字符串数组')
    return list(dict.fromkeys(v.strip() for v in value))


def spans(sentence, targets, where):
    """在原句里定位目标词形；不改写原句来迁就词条。"""
    found = []
    for target in targets:
        pattern = r'(?<!\w)' + re.escape(target) + r'(?!\w)'
        matches = list(re.finditer(pattern, sentence, re.IGNORECASE))
        if not matches:
            raise ValueError(f'{where}：目标 {target!r} 未出现在原句中，请填写原句里的实际词形')
        found.extend((m.start(), m.end()) for m in matches)
    found = sorted(set(found))
    if any(a[1] > b[0] for a, b in zip(found, found[1:])):
        raise ValueError(f'{where}：targets 在原句中重叠')
    return found


def render(sentence, positions, blank=False):
    out, offset = [], 0
    for start, end in positions:
        out.append(html.escape(sentence[offset:start]))
        out.append('<u>&#160;</u>' if blank else f'<b>{html.escape(sentence[start:end])}</b>')
        offset = end
    out.append(html.escape(sentence[offset:]))
    return ''.join(out)


def clean_entry(raw, index, kind):
    where = f'{kind} 第 {index} 条'
    if not isinstance(raw, dict):
        raise ValueError(f'{where} 不是对象')
    row = {f: text(raw.get(f), f'{where} 的 {f}') for f in ENTRY_REQUIRED}
    targets = strlist(raw.get('targets'), f'{where} 的 targets') or [row['term']]
    row['spans'] = spans(row['sentence'], targets, where)
    for optional in ('speaker', 'timecode', 'context', 'mnemonic'):
        value = raw.get(optional)
        row[optional] = value.strip() if isinstance(value, str) and value.strip() else ''
    row['collocations'] = strlist(raw.get('collocations'), f'{where} 的 collocations')
    row['derivatives'] = strlist(raw.get('derivatives'), f'{where} 的 derivatives')
    row['synonyms'] = strlist(raw.get('synonyms'), f'{where} 的 synonyms')
    band = raw.get('band', '短语搭配' if kind == '短语与习语' else '超纲实词')
    if band not in BANDS:
        raise ValueError(f'{where} 的 band 必须是 {"/".join(BANDS)} 之一')
    row['band'] = band
    freq = raw.get('freq', 1)
    if not isinstance(freq, int) or isinstance(freq, bool) or freq < 1:
        raise ValueError(f'{where} 的 freq 必须是不小于 1 的整数')
    row['freq'] = freq
    return row


def clean_grammar(raw, index):
    where = f'口语语法点 第 {index} 条'
    if not isinstance(raw, dict):
        raise ValueError(f'{where} 不是对象')
    row = {'point': text(raw.get('point'), f'{where} 的 point'),
           'rule': text(raw.get('rule'), f'{where} 的 rule')}
    for optional in ('sentence', 'translation', 'speaker', 'timecode', 'bad', 'good'):
        value = raw.get(optional)
        row[optional] = value.strip() if isinstance(value, str) and value.strip() else ''
    if bool(row['bad']) != bool(row['good']):
        raise ValueError(f'{where}：bad 与 good 必须成对出现')
    highlight = strlist(raw.get('highlight'), f'{where} 的 highlight')
    row['sentence_spans'] = spans(row['sentence'], highlight, where) if row['sentence'] and highlight else []
    row['good_spans'] = spans(row['good'], highlight, where) if row['good'] and highlight else []
    return row


def clean_culture(raw, index):
    where = f'文化背景注 第 {index} 条'
    if not isinstance(raw, dict):
        raise ValueError(f'{where} 不是对象')
    row = {'term': text(raw.get('term'), f'{where} 的 term'),
           'note': text(raw.get('note'), f'{where} 的 note')}
    for optional in ('sentence', 'speaker', 'timecode'):
        value = raw.get(optional)
        row[optional] = value.strip() if isinstance(value, str) and value.strip() else ''
    return row


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('输入必须是 JSON 对象')
    out = {k: text(data.get(k), k) for k in ('show', 'episode', 'subtitle_source', 'lead')}
    out['level'] = text(data.get('level', '高中（词汇量约 3500）'), 'level')
    out['flag'] = data['flag'].strip() if isinstance(data.get('flag'), str) and data['flag'].strip() else ''
    out['vocab'] = [clean_entry(c, i, '重点词汇') for i, c in enumerate(data.get('vocab') or [], 1)]
    out['phrases'] = [clean_entry(c, i, '短语与习语') for i, c in enumerate(data.get('phrases') or [], 1)]
    out['grammar'] = [clean_grammar(g, i) for i, g in enumerate(data.get('grammar') or [], 1)]
    out['culture'] = [clean_culture(c, i) for i, c in enumerate(data.get('culture') or [], 1)]
    if not out['vocab'] and not out['phrases']:
        raise ValueError('vocab 与 phrases 不能同时为空')
    seen = set()
    for row in out['vocab'] + out['phrases']:
        key = row['term'].casefold()
        if key in seen:
            raise ValueError(f'词条 {row["term"]!r} 重复收录')
        seen.add(key)
    return out


# ---------- HTML ----------

def entry_html(row, number):
    e = html.escape
    parts = [f'<div class="entry"><div class="l1"><span class="eno">{number:02d}</span>'
             f'<span class="head">{e(row["term"])}</span>'
             f'<span class="pron">{e(row["ipa"])}</span>'
             f'<span class="pos">{e(row["pos"])}</span> '
             f'<span class="def">{e(row["meaning"])}</span></div>']
    attribution = ' · '.join(x for x in (row['speaker'], row['timecode']) if x)
    who = f'<span class="who">— {e(attribution)}</span>' if attribution else ''
    parts.append(f'<div class="ex"><span class="en">{render(row["sentence"], row["spans"])}</span>{who}</div>')
    parts.append(f'<div class="zh">{e(row["translation"])}</div>')
    if row['context']:
        parts.append(f'<div class="ctx">{e(row["context"])}</div>')
    if row['mnemonic']:
        parts.append(f'<div class="mn"><span class="lab">记忆点</span>{e(row["mnemonic"])}</div>')
    tags = ([f'<span class="tag t-phrase">{e(t)}</span>' for t in row['collocations']]
            + [f'<span class="tag t-grammar">{e(t)}</span>' for t in row['derivatives']]
            + [f'<span class="tag">{e(t)}</span>' for t in row['synonyms']])
    if row['freq'] > 1:
        tags.append(f'<span class="tag">本集出现 {row["freq"]} 次</span>')
    if tags:
        parts.append('<div class="tags">' + ''.join(tags) + '</div>')
    return ''.join(parts) + '</div>'


def section(index, title, count, body):
    return (f'<section class="sec"><div class="sec-head"><span class="idx">{index}</span>'
            f'<span class="tt">{title}</span><span class="cnt">{count}</span></div>{body}</section>')


def map_html(data):
    e = html.escape
    entries = data['vocab'] + data['phrases']
    rows = []
    for band in BANDS:
        group = [row for row in entries if row['band'] == band]
        if not group:
            continue
        sample = '、'.join(row['term'] for row in group[:3])
        rows.append(f'<tr><td class="tname">{e(band)}</td><td class="tnum">{len(group)}</td>'
                    f'<td>{e(sample)}</td></tr>')
    summary = (f'<p>收录 <span class="tnum">{len(entries)}</span> 条表达：重点词汇 '
               f'<span class="tnum">{len(data["vocab"])}</span> 条、短语与习语 '
               f'<span class="tnum">{len(data["phrases"])}</span> 条；'
               f'口语语法点 <span class="tnum">{len(data["grammar"])}</span> 个、'
               f'文化背景注 <span class="tnum">{len(data["culture"])}</span> 条。'
               f'目标水平：{e(data["level"])}。</p>')
    table = ('<table class="t3"><caption>表 1 · 难度分布</caption><thead><tr>'
             '<th style="width:26%">类别</th><th style="width:14%">词数</th><th>本集示例</th>'
             f'</tr></thead><tbody>{"".join(rows)}</tbody></table>')
    return summary + table


def grammar_html(row, number):
    e = html.escape
    parts = [f'<div class="gram"><div class="gt"><span class="eno">{number:02d}</span>{e(row["point"])}</div>']
    if row['sentence']:
        attribution = ' · '.join(x for x in (row['speaker'], row['timecode']) if x)
        who = f'<span class="who">— {e(attribution)}</span>' if attribution else ''
        parts.append(f'<div class="ex"><span class="en">'
                     f'{render(row["sentence"], row["sentence_spans"])}</span>{who}</div>')
        if row['translation']:
            parts.append(f'<div class="zh">{e(row["translation"])}</div>')
    if row['bad']:
        parts.append('<div class="pair">'
                     f'<div class="line bad"><span class="lab">✗</span>'
                     f'<span class="txt">{e(row["bad"])}</span></div>'
                     f'<div class="line good"><span class="lab">✓</span>'
                     f'<span class="txt">{render(row["good"], row["good_spans"])}</span></div></div>')
    parts.append(f'<div class="rule"><span class="lab">规则</span>{e(row["rule"])}</div>')
    return ''.join(parts) + '</div>'


def culture_html(row, number):
    e = html.escape
    parts = [f'<div class="cul"><div class="l1"><span class="eno">{number:02d}</span>'
             f'<span class="term">{e(row["term"])}</span></div>']
    if row['sentence']:
        attribution = ' · '.join(x for x in (row['speaker'], row['timecode']) if x)
        who = f'<span class="who">— {e(attribution)}</span>' if attribution else ''
        parts.append(f'<div class="ex"><span class="en">{e(row["sentence"])}</span>{who}</div>')
    return ''.join(parts) + f'<div class="note">{e(row["note"])}</div></div>'


def selftest_html(entries):
    e = html.escape
    recall = ''.join(f'<tr><td class="tname">{e(row["term"])}</td>'
                     f'<td class="tform">{e(row["ipa"])}</td><td class="blank">&#160;</td></tr>'
                     for row in entries)
    table = ('<table class="t3"><caption>表 2 · 遮住右栏，回想中文释义</caption><thead><tr>'
             '<th style="width:32%">词头</th><th style="width:24%">音标</th><th>释义</th>'
             f'</tr></thead><tbody>{recall}</tbody></table>')
    items = ''.join(f'<li>{render(row["sentence"], row["spans"], blank=True)}'
                    f'<span class="zh">{e(row["translation"])}</span></li>' for row in entries)
    key = '　'.join(f'{i:02d} {e(row["term"])}' for i, row in enumerate(entries, 1))
    return (table + f'<ol class="cloze">{items}</ol>'
            + f'<div class="key"><span class="lab">挖空答案</span>{key}</div>')


def build_html(data):
    e = html.escape
    entries = data['vocab'] + data['phrases']
    head = (f'<h1 class="note-title">{e(data["show"])} {e(data["episode"])} 预习笔记</h1>'
            f'<p class="note-lead">{e(data["lead"])}</p>')
    if data['flag']:
        head += f'<p class="note-flag">{e(data["flag"])}</p>'
    body, index = [head], 1
    body.append(section(f'{index}', '本集词汇地图', f'{len(entries)} 条', map_html(data)))
    index += 1
    if data['vocab']:
        rows = ''.join(entry_html(row, i) for i, row in enumerate(data['vocab'], 1))
        body.append(section(f'{index}', '重点词汇', f'{len(data["vocab"])} 条', rows))
        index += 1
    if data['phrases']:
        start = len(data['vocab'])
        rows = ''.join(entry_html(row, start + i) for i, row in enumerate(data['phrases'], 1))
        body.append(section(f'{index}', '短语与习语', f'{len(data["phrases"])} 条', rows))
        index += 1
    if data['grammar']:
        rows = ''.join(grammar_html(row, i) for i, row in enumerate(data['grammar'], 1))
        body.append(section(f'{index}', '口语语法点', f'{len(data["grammar"])} 个', rows))
        index += 1
    if data['culture']:
        rows = ''.join(culture_html(row, i) for i, row in enumerate(data['culture'], 1))
        body.append(section(f'{index}', '文化背景注', f'{len(data["culture"])} 条', rows))
        index += 1
    body.append(section(f'{index}', '自测清单', '回想 + 挖空', selftest_html(entries)))

    title = f'{data["show"]} {data["episode"]} 预习笔记'
    return (TEMPLATE.read_text(encoding='utf-8')
            .replace('__TITLE__', e(title))
            .replace('__RUNHEAD_L__', e(f'{data["show"]} · {data["episode"]}'))
            .replace('__RUNHEAD_R__', e(f'字幕来源：{data["subtitle_source"]}'))
            .replace('__FOOT_L__', e(f'{title} · 目标水平 {data["level"]}'))
            .replace('__FOOT_R__', e(f'共 {len(entries)} 条表达'))
            .replace('__BODY__', ''.join(body)))


# ---------- Markdown ----------

def entry_md(row, number):
    attribution = ' · '.join(x for x in (row['speaker'], row['timecode']) if x)
    lines = [f'{number:02d}. **{row["term"]}** `{row["ipa"]}` *{row["pos"]}* — {row["meaning"]}',
             f'    - {row["sentence"]}' + (f'  — {attribution}' if attribution else ''),
             f'    - {row["translation"]}']
    if row['context']:
        lines.append(f'    - 情境：{row["context"]}')
    extras = row['collocations'] + row['derivatives'] + row['synonyms']
    if extras:
        lines.append('    - 搭配 / 派生：' + '；'.join(extras))
    if row['mnemonic']:
        lines.append(f'    - 记忆点：{row["mnemonic"]}')
    return '\n'.join(lines)


def build_md(data):
    entries = data['vocab'] + data['phrases']
    out = [f'# {data["show"]} {data["episode"]} 预习笔记', '',
           f'- 字幕来源：{data["subtitle_source"]}',
           f'- 目标水平：{data["level"]}',
           f'- 收录：重点词汇 {len(data["vocab"])} 条、短语与习语 {len(data["phrases"])} 条、'
           f'语法点 {len(data["grammar"])} 个、文化注 {len(data["culture"])} 条', '',
           data['lead'], '']
    if data['flag']:
        out += [f'> {data["flag"]}', '']
    if data['vocab']:
        out += ['## 重点词汇', '']
        out += [entry_md(row, i) for i, row in enumerate(data['vocab'], 1)] + ['']
    if data['phrases']:
        start = len(data['vocab'])
        out += ['## 短语与习语', '']
        out += [entry_md(row, start + i) for i, row in enumerate(data['phrases'], 1)] + ['']
    if data['grammar']:
        out += ['## 口语语法点', '']
        for i, row in enumerate(data['grammar'], 1):
            out.append(f'{i:02d}. **{row["point"]}**')
            if row['sentence']:
                out.append(f'    - {row["sentence"]}')
            if row['bad']:
                out += [f'    - ✗ {row["bad"]}', f'    - ✓ {row["good"]}']
            out.append(f'    - 规则：{row["rule"]}')
        out.append('')
    if data['culture']:
        out += ['## 文化背景注', '']
        out += [f'{i:02d}. **{row["term"]}** — {row["note"]}'
                for i, row in enumerate(data['culture'], 1)] + ['']
    out += ['## 自测清单', '', '遮住释义回想：' + '、'.join(row['term'] for row in entries), '']
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='词条 JSON')
    parser.add_argument('output', type=Path, help='输出 HTML 路径')
    parser.add_argument('--markdown', type=Path, default=None,
                        help='Markdown 摘要路径，默认与 HTML 同名同目录')
    args = parser.parse_args()
    try:
        data = validate(json.loads(args.input.read_text(encoding='utf-8')))
        page = build_html(data)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f'生成失败：{error}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding='utf-8')
    markdown = args.markdown or args.output.with_suffix('.md')
    markdown.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text(build_md(data), encoding='utf-8')
    total = len(data['vocab']) + len(data['phrases'])
    print(f'已生成 {args.output}（{total} 条表达）\n已生成 {markdown}')
    if not 15 <= total <= 25:
        print(f'提示：共 {total} 条，规范建议 15–25 条。'
              f'{"材料不足请在 flag 字段说明" if total < 15 else "建议再精简"}')


if __name__ == '__main__':
    main()
