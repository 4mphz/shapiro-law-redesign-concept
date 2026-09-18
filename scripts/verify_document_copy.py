"""Validate exact text, metadata, image descriptions and form fields for 18 pages."""
import json
from pathlib import Path
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'docs/verbatim-copy/source-manifest.json').read_text())
failures = []
total = 0
results = []
for relative, records in manifest['pages'].items():
    soup = BeautifulSoup((root / relative).read_text(), 'html.parser')
    for record in records:
        element = soup.select_one(f'[data-copy-id="{record["id"]}"]')
        if element is None:
            failures.append(f'{relative}: missing paragraph {record["id"]}: {record["text"]}')
            continue
        if record['role'] == 'Search-results description':
            actual = element.get('content')
        elif record['role'] == 'Image description':
            actual = element.get('alt')
        elif record['role'] == 'Form field':
            actual = element.get('placeholder')
        else:
            actual = element.get_text()
        total += 1
        if actual != record['text']:
            failures.append(f'{relative} paragraph {record["id"]}: {actual!r} != {record["text"]!r}')
    ids = [e['id'] for e in soup.select('[id]')]
    if len(ids) != len(set(ids)):
        failures.append(f'{relative}: duplicate element IDs')
    if len(soup.select('h1')) != 1:
        failures.append(f'{relative}: expected one H1')
    for element in soup.select('[src], a[href], link[rel="stylesheet"]'):
        target = element.get('src', element.get('href', '')).split('?')[0].split('#')[0]
        if not target or ':' in target or target.startswith('//'):
            continue
        if not ((root / relative).parent / target).exists():
            failures.append(f'{relative}: missing local target {target}')
    results.append({'page': relative, 'source_records': len(records)})
report = {'pages_checked': len(results), 'exact_records_checked': total, 'failures': failures, 'pages': results,
          'editorial_records_excluded': len(manifest['editorial_omissions'])}
(root / 'docs/verbatim-copy/verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(bool(failures))
