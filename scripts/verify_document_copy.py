"""Validate exact text, metadata, image descriptions and form fields for 18 pages."""
import json
from pathlib import Path
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'docs/verbatim-copy/source-manifest.json').read_text())
failures = []
overrides = {(r['page'], r['id']) for r in manifest.get('approved_overrides', [])}
total = 0
results = []
component_checks = 0
for relative, records in manifest['pages'].items():
    soup = BeautifulSoup((root / relative).read_text(), 'html.parser')
    layout = ['.client-header', '.client-footer__grid', '.client-footer__nav', '.client-cta__actions']
    if relative in ('index.html', 'es/index.html'):
        layout += ['.client-hero__portrait', '.client-hero__book', '.client-proof__grid', '.client-result-card--featured', '.client-practice__grid', '.client-firm__panel', '.client-attorneys__grid', '.client-book__inner', '.client-contact__grid']
        for required_figure in ['$300M+', '50+']:
            if required_figure not in soup.select_one('.client-proof').get_text():
                failures.append(f'{relative}: missing approved credential {required_figure}')
    elif relative.endswith('about.html'):
        layout += ['.client-inner-hero__content', '.client-attorney-profile__grid', '#ernest-buonocore', '.client-recognition__grid', '.client-book-feature__grid']
    elif relative.endswith('contact.html'):
        layout += ['.client-inner-hero__content', '.client-contact__grid', '.client-contact__form-grid', '.client-contact__map']
    elif '/practice-areas/' in '/' + relative:
        layout += ['.client-inner-hero__content', '.client-practice-detail__grid', '.client-practice-media']
    elif relative.endswith('practice-areas.html'):
        layout += ['.client-inner-hero__content', '.client-practice-index__grid']
    elif relative.endswith('results.html'):
        layout += ['.client-inner-hero__content', '.client-results__grid']
    for selector in layout:
        component_checks += 1
        if not soup.select_one(selector):
            failures.append(f'{relative}: missing approved design component {selector}')
    for record in records:
        if (relative, record['id']) in overrides:
            continue
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
          'approved_component_checks': component_checks,
          'approved_newer_result_overrides': len(overrides),
          'editorial_records_excluded': len(manifest['editorial_omissions'])}
(root / 'docs/verbatim-copy/verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(bool(failures))
