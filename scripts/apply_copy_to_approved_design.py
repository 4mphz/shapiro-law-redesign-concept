"""Place document passages in the approved components, preserving their structure.

The approved design is d4615c5. Newer approved case figures explicitly override
the older document results. Source markers allow literal copy verification.
"""
import copy
import json
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/verbatim-copy'
manifest = json.loads((OUT / 'source-manifest.json').read_text())
R = {r['id']: r for rows in manifest['pages'].values() for r in rows}


def baseline(relative):
    return BeautifulSoup(subprocess.check_output(['git', 'show', 'd4615c5:' + relative], cwd=ROOT).decode(), 'html.parser')


def put(node, record):
    if node is None:
        raise ValueError('Missing component for ' + str(record['id']))
    node['data-copy-id'] = str(record['id'])
    if record['role'] == 'Image description':
        node['alt'] = record['text']
    elif record['role'] == 'Search-results description':
        node['content'] = record['text']
    elif record['role'] == 'Form field':
        node['placeholder'] = record['text']
    else:
        node.clear()
        node.append(record['text'])
    return node


def new(soup, name, record=None, cls=None, **attrs):
    if cls:
        attrs['class'] = cls
    node = soup.new_tag(name, attrs=attrs)
    if record:
        put(node, record)
    return node


def contact_component(soup, relative, records, home=False):
    lang = 'es' if relative.startswith('es/') else 'en'
    source = baseline(('es/' if lang == 'es' else '') + 'contact.html')
    section = copy.deepcopy(source.select_one('.client-contact'))
    for node in section.select('.client-shell > .client-eyebrow, .client-shell > h2, .client-shell > .client-intro, .client-contact-card > .client-eyebrow'):
        node.decompose()
    section.attrs.pop('aria-labelledby', None)
    headings = [r for r in records if r['role'] == 'Section heading']
    put(section.select_one('#office-location-title'), headings[0])
    put(section.select_one('#contact-form-title'), headings[1])
    first_form = next(i for i, r in enumerate(records) if r['role'] == 'Form label')
    before_form = records[:first_form]
    paragraph = [r for r in before_form if r['role'] == 'Paragraph']
    put(section.select_one('#required-fields'), paragraph[-1])
    if not home:
        details = section.select_one('.client-contact__details')
        details.clear()
        details.append(new(soup, 'p', paragraph[0]))
    labels = [r for r in records if r['role'] == 'Form label']
    fields = [r for r in records if r['role'] == 'Form field']
    for target, record in zip(section.select('.client-contact__field label'), labels):
        put(target, record)
    for target, record in zip(section.select('.client-contact__field input, .client-contact__field textarea'), fields):
        put(target, record)
    put(section.select_one('.client-contact__consent > span'), labels[-1])
    put(section.select_one('#contact-disclaimer'), [r for r in records if r['role'] == 'Paragraph'][-1])
    put(section.select_one('button[type=submit]'), [r for r in records if r['role'] == 'Button'][-1])
    return section


approved_overrides = []
for relative, page_records in manifest['pages'].items():
    soup = baseline(relative)
    es = relative.startswith('es/')
    prefix = '../' if 'practice-areas/' in relative else ''
    asset = '../' * (len(Path(relative).parts) - 1)
    is_home = relative in ('index.html', 'es/index.html')
    kind = Path(relative).name

    def r(english_id):
        offset = 543 if es else 0
        if kind == 'contact.html' and english_id >= 512 and es:
            offset = 541
        return R[english_id + offset]

    def set_text(selector, english_id):
        return put(soup.select_one(selector), r(english_id))

    def discard(selector):
        for node in soup.select(selector):
            node.decompose()

    for record in page_records:
        if record['role'] == 'Page title (browser tab)':
            put(soup.title, record)
        elif record['role'] == 'Search-results description':
            put(soup.select_one('meta[name=description]'), record)

    if is_home:
        set_text('.client-hero__copy h1', 51)
        set_text('.client-hero__copy h2', 130)
        set_text('.client-hero__credential', 55)
        set_text('.client-hero__author', 57)
        portrait = set_text('.client-hero__portrait img', 48)
        portrait.parent.attrs.pop('aria-hidden', None)
        promises = soup.select('.client-hero__promises li')
        for node, source_id in zip(promises, [53, 172, 63]):
            put(node, r(source_id))
        set_text('.client-proof__item--logo span', 59)
        proof = soup.select('.client-proof__item')[3]
        put(proof.select_one('span'), r(61))
        set_text('.client-results h2', 77)
        set_text('.client-results__heading > a', 79)
        # Newer approved case results remain in their editorial cards.
        for record in page_records:
            if record['group'] == 'CASE RESULTS' and record['role'] in ('Heading', 'Paragraph'):
                approved_overrides.append({'page': relative, **record, 'reason': 'User explicitly retained newer approved case results.'})
        set_text('.client-practice h2', 105)
        discard('.client-practice > .client-shell > .client-intro')
        for card, ids in zip(soup.select('.client-practice-card'), [[107, 109], [111, 113, 115], [117], [119, 121]]):
            for node in card.select('h3, p'):
                node.decompose()
            for source_id in ids:
                card.append(new(soup, 'h3', r(source_id)))
        set_text('.client-firm h2', 96)
        set_text('.client-firm > .client-shell > .client-intro', 100)
        intro = soup.select_one('.client-firm > .client-shell > .client-intro')
        intro.insert_before(new(soup, 'h3', r(98), 'client-copy-subhead'))
        intro.insert_after(new(soup, 'h3', r(102), 'client-copy-subhead'))
        panel = soup.select_one('.client-firm__panel')
        panel.clear()
        panel.append(new(soup, 'h3', r(162)))
        grid = new(soup, 'div', cls='client-copy-benefits')
        for heading, paragraph in [(164, 166), (168, 170), (172, 174), (176, 178), (180, 182), (184, 186)]:
            card = new(soup, 'article')
            card.append(new(soup, 'h4', r(heading)))
            card.append(new(soup, 'p', r(paragraph)))
            grid.append(card)
        panel.append(grid)
        set_text('.client-attorneys h2', 124)
        set_text('.client-attorneys .client-intro', 126)
        card = soup.select_one('.client-attorney-card')
        put(card.select_one('h3'), r(130))
        put(card.select_one('strong'), r(132))
        put(card.select_one('p'), r(134))
        card.append(new(soup, 'p', r(136)))
        card.append(new(soup, 'a', r(138), 'client-text-link', href='about.html'))
        card.insert(0, new(soup, 'img', r(128), 'client-copy-portrait', src=asset + 'images/jason-shapiro.jpg', loading='lazy', width='939', height='975'))
        set_text('.client-book__art img', 148)
        set_text('.client-book__copy .client-eyebrow', 151)
        set_text('.client-book__copy h2', 153)
        set_text('.client-book__copy > p:not(.client-eyebrow)', 155)
        set_text('.client-book__actions .client-btn', 159)
        set_text('.client-book__actions .client-text-link', 157)
        # Source practice strip remains a compact list, without a new page template.
        strip = new(soup, 'div', cls='client-source-strip')
        listing = new(soup, 'ul', cls='client-shell')
        for source_id in [66, 68, 70, 72, 74]:
            listing.append(new(soup, 'li', r(source_id)))
        strip.append(listing)
        soup.select_one('.client-proof').insert_after(strip)
        form_records = [record for record in page_records if record['group'] == 'OFFICE LOCATION AND CONTACT FORM']
        contact = contact_component(soup, relative, form_records, home=True)
        source_line = new(soup, 'p', r(189), 'client-source-contact-line')
        contact.select_one('.client-shell').insert(0, source_line)
        soup.select_one('.client-cta').insert_before(contact)
        soup.select_one('.client-cta').attrs.pop('id', None)
    elif kind == 'about.html':
        set_text('#firm-heading', 246)
        for node, source_id in zip(soup.select('.client-inner-intro .client-shell > p:not(.client-eyebrow)'), [248, 250]):
            put(node, r(source_id))
        set_text('#jason-heading', 252)
        set_text('#jason-shapiro .client-attorney-role', 254)
        set_text('#jason-shapiro .client-attorney-profile__content > p:not(.client-attorney-role)', 256)
        for node, source_id in zip(soup.select('#jason-shapiro .client-attorney-facts li'), [258, 260, 262, 264]):
            put(node, r(source_id))
        set_text('#jason-shapiro img', 266)
        set_text('#recognition-heading', 276)
        cards = soup.select('.client-recognition-card p')
        for node, source_id in zip([cards[0], cards[2], cards[3]], [278, 280, 282]):
            put(node, r(source_id))
        set_text('.client-book-feature__art img', 284)
        set_text('#book-heading', 286)
        set_text('.client-book-feature__copy > p:not(.client-eyebrow)', 288)
        set_text('.client-book-feature__copy .client-btn', 290)
    elif kind == 'practice-areas.html':
        set_text('.client-practice-index h2', 299)
        set_text('.client-practice-index .client-intro', 301)
        content = [record for record in page_records if record['id'] >= (303 + (543 if es else 0)) and record['id'] <= (365 + (543 if es else 0))]
        groups = []
        for record in content:
            if record['role'] == 'Heading':
                groups.append([])
            groups[-1].append(record)
        for card, group in zip(soup.select('.client-practice-index-card'), groups):
            put(card.h3, group[0])
            for node, record in zip(card.select('li'), [rec for rec in group if rec['role'] == 'List item']):
                put(node, record)
            put(card.select_one('.client-btn'), group[-1])
    elif 'practice-areas/' in relative:
        content = [record for record in page_records if record['id'] >= 370 + (543 if es else 0)]
        content = [rec for rec in content if rec['id'] not in range(552, 580)]
        headline = next(rec for rec in content if rec['role'] == 'Main headline')
        heading = next(rec for rec in content if rec['role'] == 'Section heading')
        paragraphs = [rec for rec in content if rec['role'] == 'Paragraph']
        # Shared footer records are at the end of the manifest; limit to this page.
        upper = 550 if not es else 1091
        content = [rec for rec in content if rec['id'] < upper]
        paragraphs = [rec for rec in content if rec['role'] == 'Paragraph']
        put(soup.h1, headline)
        put(soup.select_one('.client-practice-detail__content h2'), heading)
        put(soup.select_one('.client-practice-detail__content > p'), paragraphs[0])
        put(soup.select_one('.client-detail-callout p'), paragraphs[1])
        for node, record in zip(soup.select('.client-practice-detail__content li'), [rec for rec in content if rec['role'] == 'List item']):
            put(node, record)
    elif kind == 'results.html':
        set_text('h1', 482)
        set_text('#published-results-title', 484)
        set_text('.client-legal-note', 500)
        # Keep factual descriptions and amounts together, as approved by the user.
        for record in page_records:
            if (486 + (543 if es else 0)) <= record['id'] <= (498 + (543 if es else 0)):
                approved_overrides.append({'page': relative, **record, 'reason': 'User explicitly retained newer approved case results.'})
    elif kind == 'contact.html':
        if not es:
            set_text('h1', 509)
        else:
            soup.h1.string = 'Contáctenos'
        records = [rec for rec in page_records if rec['group'] == 'OFFICE LOCATION AND CONTACT FORM']
        soup.select_one('.client-contact').replace_with(contact_component(soup, relative, records))

    common = {14:553,16:559,18:561,20:563,22:565,24:567,26:569,28:571,30:573,32:575,34:577,36:579}
    def shared(english_id):
        return R[common[english_id] if es else english_id]
    put(soup.select_one('.client-header__contact > span'), shared(14))
    cta = soup.select_one('.client-cta')
    shell = cta.select_one('.client-shell')
    shell.clear()
    cta.attrs.pop('aria-labelledby', None)
    shell.append(new(soup, 'h2', shared(18)))
    shell.append(new(soup, 'h5', shared(20)))
    shell.append(new(soup, 'p', shared(22)))
    actions = new(soup, 'div', cls='client-cta__actions')
    actions.append(new(soup, 'a', shared(16), 'client-btn client-btn--light', href=prefix + 'contact.html#contact-form'))
    actions.append(new(soup, 'a', shared(24), 'client-btn client-btn--outline-light', href='tel:7182957000'))
    shell.append(actions)
    if is_home:
        put(soup.select_one('.client-hero__copy .client-btn'), shared(16))
    # Restore the approved full footer instead of the replacement single column.
    footer = copy.deepcopy(baseline(('es/' if es else '') + 'index.html').footer)
    if prefix:
        for anchor in footer.select('a[href]'):
            if ':' not in anchor['href'] and not anchor['href'].startswith('#'):
                anchor['href'] = prefix + anchor['href']
    for anchor in footer.select('[aria-current]'):
        anchor.attrs.pop('aria-current', None)
    put(footer.select_one('.client-footer__serving'), shared(30))
    put(footer.select_one('.client-footer__contact h2'), shared(26))
    put(footer.select_one('.client-footer__contact p'), shared(28))
    put(footer.select_one('.client-footer__contact a'), shared(32))
    for node, source_id in zip(footer.select('.client-footer__legal > p'), [34,36]):
        put(node, shared(source_id))
    if es:
        footer.select_one('.client-footer__social').insert(0,new(soup,'span',R[555]))
        contact_link = next(a for a in soup.select('#main-navigation a') if a['href'].endswith('contact.html'))
        put(contact_link,R[557])
    soup.footer.replace_with(footer)
    if 'practice-areas/' in relative:
        language_target = ('../../practice-areas/' if es else '../es/practice-areas/') + kind
        for anchor in soup.select('.client-lang, .lang-pill-mobile'):
            anchor['href'] = language_target
    soup.body['class'] = soup.body.get('class', []) + ['client-document-copy']
    soup.head.append(soup.new_tag('link', rel='stylesheet', href=asset+'css/approved-copy.css?v=20260918-2'))
    (ROOT / relative).write_text(str(soup).rstrip()+'\n')

manifest['approved_overrides'] = approved_overrides
manifest['design_baseline'] = 'd4615c5'
manifest['policy'] = 'Document passages in approved components; newer approved results and credentials retained per user confirmation.'
(OUT/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Restored approved components on 18 pages; retained newer approved results.')
