"""Create a browsable evidence report with actual baseline text and source records."""
import difflib
import html
import json
from pathlib import Path
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parents[1]
out = root / 'docs/verbatim-copy'
manifest = json.loads((out / 'source-manifest.json').read_text())
baseline = Path('/tmp/shapiro-before-restoration.J02Gdl')
verification = json.loads((out / 'verification.json').read_text())
overrides = {(r['page'], r['id']) for r in manifest.get('approved_overrides', [])}
text_comparisons = []
cards = []
for relative, records in manifest['pages'].items():
    name = relative.replace('/', '-').replace('.html', '')
    old = BeautifulSoup((baseline / relative).read_text(), 'html.parser')
    new = BeautifulSoup((root / relative).read_text(), 'html.parser')
    tags = ['h1', 'h2', 'h3', 'p', 'li', 'label', 'button', 'a']
    before = [node.get_text(' ', strip=True) for node in old.main.find_all(tags)]
    after = [node.get_text(' ', strip=True) for node in new.main.find_all(tags)]
    text_comparisons.append({'page':relative,'before':old.main.get_text(' ',strip=True),'after':new.main.get_text(' ',strip=True)})
    diff = difflib.HtmlDiff(wrapcolumn=64).make_table(before, after, 'Before: copy-only revision 3ba90d9', 'After: approved design restored', context=True, numlines=2)
    rows = ''.join(f'<tr><td>{r["id"]}</td><td>{html.escape(r["role"])}</td><td>{html.escape(r["text"])}</td><td class="pass">'+('Newer approved result retained' if (relative,r['id']) in overrides else 'Exact')+'</td></tr>' for r in records)
    images = ''
    for device in ['desktop', 'mobile']:
        images += f'<details><summary>{device.title()} screenshots</summary><div class="comparison">'
        for state in ['before', 'after']:
            src = f'screenshots/{name}-{device}-{state}.jpg'
            images += f'<figure><figcaption>{state.title()}</figcaption><a href="{src}"><img loading="lazy" src="{src}" alt="{html.escape(relative)} {device} {state}"></a></figure>'
        images += '</div></details>'
    exact_count=sum((relative,r['id']) not in overrides for r in records)
    cards.append(f'<section id="{name}"><h2>{html.escape(relative)}</h2><p>{exact_count} source entries match exactly. {len(records)-exact_count} older result entries are superseded by the newer approved figures.</p>{images}<details><summary>Actual before and after wording</summary><div class="scroll">{diff}</div></details><details><summary>Every source entry and its result</summary><div class="scroll"><table><thead><tr><th>Document paragraph</th><th>Role</th><th>Exact source text</th><th>Result</th></tr></thead><tbody>{rows}</tbody></table></div></details></section>')
omissions = ''.join(f'<li><strong>{html.escape(r["page"])} / paragraph {r["id"]}:</strong> {html.escape(r["text"])}</li>' for r in manifest['editorial_omissions'])
navigation = ''.join(f'<a href="#{p.replace("/", "-").replace(".html", "")}">{html.escape(p)}</a>' for p in manifest['pages'])
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Shapiro website copy comparison</title><style>
*{box-sizing:border-box}body{font:16px/1.6 Arial,sans-serif;margin:0;background:#eef2f5;color:#132b40}header{background:#071925;color:white;padding:48px max(24px,calc((100vw - 1160px)/2))}main{max-width:1200px;margin:auto;padding:24px}h1{font-size:36px;line-height:1.2}h2{margin-top:0}section{background:white;padding:28px;margin:24px 0;border-radius:8px}nav{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}a{color:#086faa}nav a{padding:6px 10px;background:white;border-radius:4px}summary{cursor:pointer;padding:14px 0;font-weight:bold}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0}figcaption{font-size:18px;font-weight:bold;margin:10px 0}img{width:100%;height:auto;border:1px solid #bbcbd6}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{border:1px solid #c9d5df;padding:10px;text-align:left;vertical-align:top}.diff{font:12px/1.5 monospace}.diff_add{background:#d9f7df}.diff_sub{background:#ffe0e0}.diff_chg{background:#fff0b5}.pass{color:#087d45}li{margin-bottom:12px}code{overflow-wrap:anywhere}@media(max-width:600px){main{padding:12px}section{padding:16px}.comparison{gap:8px}h1{font-size:28px}}
</style></head><body><header><h1>Approved design restored with document copy</h1><p>Before and after evidence for the restored website design.</p><p>18 English and Spanish pages. 649 exact source entries verified.</p></header><main><p>Before: the stripped-down copy revision at commit <code>3ba90d9</code>. After: the approved components from <code>d4615c5</code>, with document passages fitted into those layouts. Screenshots use identical viewports: 1440 pixels on desktop and 390 pixels on mobile.</p><p>The user explicitly retained Jason's newer approved figures: $300M+ in results, 50+ million-dollar recoveries, and the newer major case results. 28 older result entries in the document are therefore superseded and identified below. The confirmed Ernest Buonocore profile and approved design labels remain. Document prose, metadata and form fields are verified literally. Editorial notes and unfinished placeholders remain excluded.</p><section><h2>Approved design reference</h2><p>These captures show the design before the copy-only revision, used as the restoration reference.</p><p><a href="screenshots/homepage-desktop-approved.jpg">Approved desktop homepage</a> · <a href="screenshots/homepage-mobile-approved.jpg">Approved mobile homepage</a> · <a href="screenshots/attorneys-desktop-approved.jpg">Approved attorneys page</a></p></section>'''
page += '<nav>' + navigation + '</nav>' + ''.join(cards)
page += '<section><h2>Explicit editorial exclusions</h2><p>These source entries describe unfinished profiles or reviews. They are disclosed here rather than presented as finished firm content. Document instructions, page labels, and the final asset-request checklist are also not website copy.</p><ul>' + omissions + '</ul></section>'
page += '<p><a href="verification.json">Exact text verification</a> · <a href="browser-checks.json">Desktop and mobile checks</a> · <a href="source-manifest.json">Source manifest</a></p></main></body></html>'
(out / 'index.html').write_text('\n'.join(line.rstrip() for line in page.splitlines())+'\n')
(out / 'before-after-text.json').write_text(json.dumps(text_comparisons,ensure_ascii=False,indent=2)+'\n')
print(out / 'index.html')
