"""Restore client copy verbatim from the August 24 DOCX and verify every record.

Run with the source DOCX path. Layout labels and instructions are never published.
The explicit request for verbatim copy takes precedence over earlier copy edits.
"""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'Paragraph', 'Button', 'Section heading', 'Small heading', 'Heading',
          'List item', 'Page title (browser tab)', 'Search-results description',
          'Image description', 'Main headline', 'Form label', 'Form field'}
META = {'Page title (browser tab)', 'Search-results description'}
EDITORIAL = set(range(139, 147)) | set(range(268, 275)) | set(range(190, 201)) | set(range(682, 690)) | set(range(810, 818)) | set(range(733, 744))
AMAZON = 'https://www.amazon.com/Lawyers-Guide-Personal-Injury-Law/dp/1595941991/'


def esc(text):
    return html.escape(text, quote=True)


def records(paragraphs, start, end):
    found = []
    group = ''
    i = start
    while i < end:
        text = paragraphs[i]
        if text in LABELS and i + 1 < end:
            found.append({'id': i + 1, 'role': text, 'text': paragraphs[i + 1], 'group': group})
            i += 2
        else:
            if text and text.isupper():
                group = text
            i += 1
    return found


def marker(record):
    return f'data-copy-id="{record["id"]}"'


def block(record, tag, attrs=''):
    return f'<{tag} {marker(record)} {attrs}>{esc(record["text"])}</{tag}>'


def link_for(text, lang, prefix):
    lower = text.lower()
    if 'purchase' in lower or 'comprar' in lower:
        return AMAZON
    if 'call 718' in lower or 'llame 718' in lower:
        return 'tel:7182957000'
    if 'result' in lower:
        return prefix + 'results.html'
    if 'profile' in lower or 'perfil' in lower or 'author' in lower or 'autor' in lower:
        return prefix + 'about.html'
    for terms, slug in [(['scaffold', 'andamios'], 'construction-scaffold'), (['motor vehicle', 'vehículos'], 'motor-vehicle'), (['premises', 'propiedades'], 'premises'), (['medical', 'médica'], 'medical-malpractice')]:
        if any(term in lower for term in terms):
            return prefix + 'practice-areas/' + slug + '.html'
    return prefix + 'contact.html#contact-form'


def render_sequence(items, lang, prefix, asset_prefix, home=False):
    output = []
    form_open = False
    in_list = False
    for index, record in enumerate(items):
        role, text = record['role'], record['text']
        if role == 'List item':
            if not in_list:
                output.append('<ul class="document-list">')
                in_list = True
            output.append(block(record, 'li'))
            continue
        if in_list:
            output.append('</ul>')
            in_list = False
        if role == 'Image description':
            book = 'Guide' in text or 'Guía' in text
            src = 'lawyers-guide-book.webp' if book else 'jason-shapiro.jpg'
            output.append(f'<img class="document-image {"document-image--book" if book else ""}" {marker(record)} src="{asset_prefix}images/{src}" alt="{esc(text)}" loading="lazy">')
        elif role == 'Form label':
            if not form_open:
                output.append('<form id="contact-form" class="document-form">')
                form_open = True
            ident = 'field-' + str(record['id'])
            if 'Disclaimer' in text or 'Aviso Legal' in text:
                output.append(f'<label class="document-consent"><input type="checkbox" required name="disclaimer-accepted"><span {marker(record)}>{esc(text)}</span></label>')
                continue
            next_record = items[index + 1] if index + 1 < len(items) else None
            lower = text.lower()
            kind = 'email' if 'email' in lower or 'correo' in lower else 'tel' if 'phone' in lower or 'teléfono' in lower else 'text'
            required = ' required' if '*' in text else ''
            field_marker = marker(next_record) if next_record and next_record['role'] == 'Form field' else ''
            placeholder = esc(next_record['text']) if next_record and next_record['role'] == 'Form field' else ''
            output.append(f'<label for="{ident}" {marker(record)}>{esc(text)}</label>')
            if 'description' in lower or 'descripción' in lower:
                output.append(f'<textarea id="{ident}" name="description" {field_marker} placeholder="{placeholder}" rows="6"{required}></textarea>')
            else:
                output.append(f'<input id="{ident}" name="{ident}" type="{kind}" {field_marker} placeholder="{placeholder}"{required}>')
        elif role == 'Form field':
            continue
        elif role == 'Button':
            if form_open:
                output.append(block(record, 'button', 'type="submit" class="client-btn"'))
            else:
                href = link_for(text, lang, prefix)
                extra = ' target="_blank" rel="noopener"' if href.startswith('https:') else ''
                output.append(block(record, 'a', f'class="client-btn" href="{href}"{extra}'))
        else:
            tag = {'Main headline': 'h1', 'Section heading': 'h2', 'Heading': 'h3', 'Small heading': 'h3'}.get(role, 'p')
            output.append(block(record, tag))
    if in_list:
        output.append('</ul>')
    if form_open:
        output.append('</form>')
    return '\n'.join(output)


def groups_for(items):
    groups = []
    current = []
    for record in items:
        boundary = current and (record['group'] != current[-1]['group'] or (record['role'] == 'Section heading' and any(r['role'] == 'Section heading' for r in current)))
        if boundary:
            groups.append(current)
            current = []
        current.append(record)
    if current:
        groups.append(current)
    # Image descriptions precede the book label in the source, but belong with it.
    for i in range(len(groups) - 1):
        if groups[i] and groups[i][-1]['role'] == 'Image description' and groups[i + 1][0]['group'] == 'THE BOOK':
            groups[i + 1].insert(0, groups[i].pop())
    return groups


def layout_body(body, group):
    fragment = BeautifulSoup(body, 'html.parser')
    group_name = group[0]['group']
    if group_name in {'CASE RESULTS', 'PRACTICE AREAS', 'WHY CHOOSE US'}:
        grid = fragment.new_tag('div', attrs={'class': 'document-card-grid'})
        card = None
        for node in list(fragment.contents):
            if getattr(node, 'name', None) == 'h3':
                card = fragment.new_tag('article', attrs={'class': 'document-card'})
                grid.append(card)
            if card is not None:
                card.append(node.extract())
        fragment.append(grid)
    return str(fragment)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--baseline', type=Path, default=ROOT)
    args = parser.parse_args()
    paragraphs = [p.text for p in Document(args.source).paragraphs]
    starts = [(i, p) for i, p in enumerate(paragraphs) if re.fullmatch(r'(?:es/)?(?:practice-areas/)?[a-z-]+\.html', p)]
    shared = {'en': records(paragraphs, 13, 37), 'es': records(paragraphs, 552, 580)}
    manifest = {'source': args.source.name, 'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(), 'pages': {}, 'editorial_omissions': []}
    before_after = []
    for n, (start, relative) in enumerate(starts):
        end = starts[n + 1][0] - 1 if n + 1 < len(starts) else 1091
        if relative == 'contact.html':
            end = 550
        page_records = records(paragraphs, start + 1, end)
        lang = 'es' if relative.startswith('es/') else 'en'
        prefix = '../' if 'practice-areas/' in relative else ''
        asset_prefix = '../' * (len(Path(relative).parts) - 1)
        home = relative in ('index.html', 'es/index.html')
        path = ROOT / relative
        soup = BeautifulSoup((args.baseline / relative).read_text(), 'html.parser')
        old_text = soup.main.get_text(' ', strip=True)
        body_records = []
        for record in page_records:
            if record['id'] in EDITORIAL:
                manifest['editorial_omissions'].append({'page': relative, **record})
                continue
            if record['role'] == 'Page title (browser tab)':
                soup.title.string = record['text']
                soup.title['data-copy-id'] = record['id']
            elif record['role'] == 'Search-results description':
                meta = soup.find('meta', attrs={'name': 'description'})
                meta['content'] = record['text']
                meta['data-copy-id'] = record['id']
            else:
                body_records.append(record)

        # Keep the established header, navigation and photography; replace its copy.
        header_line = soup.select_one('.client-header__contact > span')
        header_line.string = shared[lang][0]['text']
        header_line['data-copy-id'] = shared[lang][0]['id']
        header_button = next(r for r in shared[lang] if r['role'] == 'Button')
        header_actions = soup.select_one('.client-header__actions')
        header_actions.append(BeautifulSoup(block(header_button, 'a', f'class="document-header-cta" href="{prefix}contact.html#contact-form"'), 'html.parser'))
        if lang == 'es':
            follow = next(r for r in shared[lang] if r['text'] == 'Síganos :')
            header_actions.insert(0, BeautifulSoup(block(follow, 'span', 'class="document-follow"'), 'html.parser'))
            contact_nav = next(a for a in soup.select('#main-navigation a') if a.get('href', '').endswith('contact.html'))
            contact_rec = next(r for r in shared[lang] if r['role'] == 'List item')
            contact_nav.string = contact_rec['text']
            contact_nav['data-copy-id'] = contact_rec['id']

        sections = []
        groups = groups_for(body_records)
        if home:
            hero_items = groups.pop(0)
            if groups and any(r['role'] == 'Main headline' for r in groups[0]):
                hero_items += groups.pop(0)
            # The source image description is the portrait's accessible text.
            portrait = next(r for r in hero_items if r['role'] == 'Image description')
            copy = render_sequence([r for r in hero_items if r != portrait], lang, prefix, asset_prefix)
            sections.append(f'<section class="client-hero document-hero"><div class="client-hero__shade"></div><div class="client-shell client-hero__inner"><div class="client-hero__portrait"><img {marker(portrait)} src="{asset_prefix}images/jason-shapiro-hero.webp" alt="{esc(portrait["text"])}"></div><div class="client-hero__copy">{copy}</div><a class="client-hero__book" href="{AMAZON}"><img src="{asset_prefix}images/lawyers-guide-book.webp" alt=""></a></div></section>')
        else:
            headline = next((r for r in body_records if r['role'] == 'Main headline'), None)
            if headline:
                title_html = block(headline, 'h1')
                groups = [[r for r in group if r != headline] for group in groups]
            else:
                title = paragraphs[start - 1].split(' (')[0]
                title_html = '<h1>' + esc(title) + '</h1>'
            sections.append(f'<section class="client-inner-hero"><div class="client-inner-hero__shade"></div><div class="client-shell client-inner-hero__content">{title_html}</div></section>')
        for index, group in enumerate(groups):
            if not group:
                continue
            body = layout_body(render_sequence(group, lang, prefix, asset_prefix, home), group)
            kind = 'document-section'
            if any(r['text'].startswith('$') for r in group):
                kind += ' document-results'
            if any(r['role'] == 'Form label' for r in group):
                kind += ' document-contact'
            if any(r['role'] == 'Image description' and ('Guide' in r['text'] or 'Guía' in r['text']) for r in group):
                kind += ' document-book'
            if group[0]['group'] == 'MOVING PRACTICE-AREA STRIP':
                kind += ' document-strip'
            if home and group[0]['group'] == 'OFFICE LOCATION AND CONTACT FORM' and len(group) == 1:
                body += '<iframe class="document-map" title="' + ('Ubicación' if lang == 'es' else 'Location') + '" src="https://www.google.com/maps?q=3205+Grand+Concourse+Suite+1+Bronx+NY+10468&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'
            sections.append(f'<section class="{kind}"><div class="client-shell document-flow">{body}</div></section>')
        main_html = '<main id="main-content">' + '\n'.join(sections) + '</main>'
        soup.main.replace_with(BeautifulSoup(main_html, 'html.parser'))
        # The document specifies the same consultation and footer text on every page.
        commons = shared[lang]
        cta_start = next(i for i, r in enumerate(commons) if r['role'] == 'Section heading')
        location_start = next(i for i, r in enumerate(commons) if r['role'] == 'Heading')
        cta = render_sequence(commons[cta_start:location_start], lang, prefix, asset_prefix)
        footer = render_sequence(commons[location_start:], lang, prefix, asset_prefix)
        soup.footer.replace_with(BeautifulSoup(f'<footer class="document-footer"><section class="client-cta"><div class="client-shell document-flow">{cta}</div></section><div class="client-shell document-flow document-footer__body">{footer}</div></footer>', 'html.parser'))
        soup.body['class'] = soup.body.get('class', []) + ['document-copy']
        css = soup.new_tag('link', rel='stylesheet', href=asset_prefix + 'css/document-copy.css?v=20260918-1')
        soup.head.append(css)
        # Fix pre-existing relative language links on detail pages.
        target_lang = ('../../' if lang == 'es' else '../') + ('practice-areas/' if lang == 'es' else 'es/practice-areas/') + Path(relative).name
        if 'practice-areas/' in relative:
            for anchor in soup.select('.client-lang, .lang-pill-mobile'):
                anchor['href'] = target_lang
        path.write_text(str(soup).rstrip() + '\n')
        expected = [r for r in page_records if r['id'] not in EDITORIAL] + commons
        manifest['pages'][relative] = expected
        before_after.append({'page': relative, 'before': old_text, 'after': soup.main.get_text(' ', strip=True)})
    output = ROOT / 'docs/verbatim-copy'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (output / 'before-after-text.json').write_text(json.dumps(before_after, ensure_ascii=False, indent=2) + '\n')
    print(f'Restored {len(manifest["pages"])} pages from {args.source.name}')


if __name__ == '__main__':
    main()
