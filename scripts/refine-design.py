"""Idempotent presentation pass. Preserves approved text, assets and backgrounds."""
from pathlib import Path
import json
import re
import copy
from bs4 import BeautifulSoup, Tag

ROOT=Path(__file__).resolve().parents[1]
files=list(ROOT.glob('*.html'))+list((ROOT/'practice-areas').glob('*.html'))+list((ROOT/'es').rglob('*.html'))
report=[]
def key(text):return ' '.join(text.split())
for path in files:
    soup=BeautifulSoup(path.read_text(),'html.parser')
    if not soup.body or not set(soup.body.get('class',[]))&{'client-home','client-site'}:continue
    before={key(n.get_text(' ',strip=True)) for n in soup.select('main p, main li, main h1, main h2, main h3')}
    soup.body['class']=list(dict.fromkeys(soup.body.get('class',[])+['design-refined']))
    prefix='../'*len(path.relative_to(ROOT).parts[:-1])
    link=soup.select_one('link[href*="design-refinement.css"]')
    if not link:
        link=soup.new_tag('link',rel='stylesheet');soup.head.append(link)
    link['href']=prefix+'css/design-refinement.css?v=20260927-6'
    # One compact, native-text wordmark shared by navigation and footer.
    header_logo=soup.select_one('.client-header .client-logo')
    footer_brand=soup.select_one('.client-footer__brand')
    if header_logo and footer_brand:
        header_logo.clear()
        wordmark=soup.new_tag('span',attrs={'class':'brand-wordmark','aria-hidden':'true'})
        name=soup.new_tag('span',attrs={'class':'brand-wordmark__name'});name.string='SHAPIRO'
        line=soup.new_tag('span',attrs={'class':'brand-wordmark__line'})
        offices=soup.new_tag('span',attrs={'class':'brand-wordmark__offices'})
        for letter in 'LAW OFFICES':
            glyph=soup.new_tag('span');glyph.string=letter if letter!=' ' else '\u00a0';offices.append(glyph)
        suffix=soup.new_tag('small');suffix.string='PLLC'
        line.append(offices);line.append(suffix);wordmark.append(name);wordmark.append(line);header_logo.append(wordmark)
        footer_brand.find_parent('footer')['id']='site-footer'
        footer_logo=copy.deepcopy(header_logo)
        footer_logo['class']=['client-footer__logo']
        current=footer_brand.find('a',recursive=False)
        if current:current.replace_with(footer_logo)
        else:footer_brand.insert(0,footer_logo)
    for script in soup.select('script[src]'):
        if script['src'].split('?')[0].endswith('js/main.js'):script['src']=prefix+'js/main.js?v=20260927-design'
    # Replaced source headings had lost their original accessibility IDs.
    for section in soup.select('[aria-labelledby]'):
        ids=section['aria-labelledby'].split()
        if any(not soup.find(id=i) for i in ids):
            heading=section.find(re.compile('^h[1-6]$'))
            if heading and not heading.get('id'):heading['id']=ids[0]
            else:del section['aria-labelledby']
    for content in soup.select('.client-september-content'):
        shell=content.select_one('.client-shell')
        if shell.select_one('.editorial-article'):continue
        relative=str(path.relative_to(ROOT))
        is_detail=relative.startswith('practice-areas/')
        is_overview=relative=='practice-areas.html'
        is_results=relative=='results.html'
        content['class']+=['editorial-content']
        if is_overview:content['class']+=['editorial-overview']
        if is_results:content['class']+=['editorial-results']
        # Keep one copy of the shared consultation content, in its dedicated band.
        cta=soup.select_one('.client-cta')
        duplicate_texts={key(n.get_text(' ',strip=True)) for n in cta.select('h2,p,a')} if cta else set()
        for n in list(shell.find_all(recursive=False)):
            if n.name in ['h2','p','a'] and key(n.get_text(' ',strip=True)) in duplicate_texts:n.decompose()
        media=shell.select_one('.client-september-media')
        if media:media.extract()
        children=list(shell.find_all(recursive=False))
        article=soup.new_tag('div',attrs={'class':'editorial-article'})
        lead=soup.new_tag('div',attrs={'class':'editorial-lead'})
        article.append(lead);current=lead;faq=None;question=None
        for n in children:
            text=n.get_text(' ',strip=True)
            if n.name=='h2':
                if faq is not None and text.endswith('?'):
                    question=soup.new_tag('details',attrs={'class':'editorial-question'})
                    summary=soup.new_tag('summary');summary.string=text;question.append(summary);n.decompose();faq.append(question);continue
                faq=None;question=None
                current=soup.new_tag('section',attrs={'class':'editorial-section'})
                n['id']='section-'+str(len(article.select('.editorial-section'))+1)
                current.append(n.extract());article.append(current)
                if text=='Frequently Asked Questions':faq=current
            elif question is not None:question.append(n.extract())
            else:current.append(n.extract())
        if media:
            lead['class']+=['editorial-lead--media'];copy=soup.new_tag('div')
            for n in list(lead.contents):copy.append(n.extract())
            lead.append(copy);lead.append(media)
        if not lead.get_text(strip=True) and not lead.find('img'):lead.decompose()
        # Legal copy is a distinct note, not another loose paragraph.
        for p in article.select('p'):
            if p.get_text().startswith('Attorney Advertising.'):
                p['class']=list(dict.fromkeys(p.get('class',[])+['editorial-legal']))
        if is_detail:
            layout=soup.new_tag('div',attrs={'class':'editorial-layout'})
            nav=soup.new_tag('nav',attrs={'class':'editorial-toc','aria-label':'On this page'})
            label=soup.new_tag('p');label.string='On this page';nav.append(label)
            for h in article.select('.editorial-section > h2'):
                a=soup.new_tag('a',href='#'+h['id']);a.string=h.get_text();nav.append(a)
            layout.append(nav);layout.append(article);shell.append(layout)
        else:shell.append(article)
        for h in article.select('.client-practice-index-card h2, .client-case-result h2'):h.name='h3'
    # Give the contact guidance a real container and hierarchy.
    for shell in soup.select('.client-section > .client-shell'):
        shell['class']=[c for c in shell.get('class',[]) if c!='editorial-contact-guidance']
        if shell.find('h2',string='What Happens After You Contact Us',recursive=False):
            shell['class']+=['editorial-contact-guidance']
    for p in soup.select('.editorial-question .editorial-legal'):
        article=p.find_parent(class_='editorial-article')
        article.append(p.extract())
    # Keep the office details and next steps together, beside the intake form.
    guidance=soup.select_one('.editorial-contact-guidance')
    grid=soup.select_one('.client-contact__grid')
    if guidance and grid and not grid.select_one('.editorial-contact-column'):
        old_section=guidance.parent
        column=soup.new_tag('div',attrs={'class':'editorial-contact-column'})
        location=grid.select_one('.client-contact-card');location.insert_before(column);column.append(location.extract())
        guidance.name='section';guidance['class']=['editorial-contact-guidance']
        column.append(guidance.extract());old_section.decompose()
    for field in soup.select('.client-contact__field'):
        if field.select_one('textarea, #f-matter'):
            field['class']=list(dict.fromkeys(field.get('class',[])+['client-contact__field--full']))
    # A direct maps link remains usable when third-party embeds are blocked.
    for frame in soup.select('.client-contact__map iframe'):
        url=frame.get('src','').replace('&output=embed','')
        a=soup.new_tag('a',href=url,target='_blank',rel='noopener')
        a.string='Cómo llegar ↗' if soup.html.get('lang')=='es' else 'Get directions ↗'
        frame.replace_with(a)
    # Correct the role styling on profile blocks without changing the text.
    for profile in soup.select('.client-attorney-profile__content'):
        role=profile.select_one('h2 + p')
        if role:role['class']=list(dict.fromkeys(role.get('class',[])+['client-attorney-role']))
    # Recognition belongs in one concise list, not four mostly empty cards.
    for grid in soup.select('.client-recognition__grid'):
        grid.name='ul';grid['class']=['client-recognition-list'];grid['role']='list'
        for card in grid.find_all(recursive=False):
            card.name='li';card.attrs={}
    for img in soup.select('#jason-shapiro .client-attorney-profile__media img'):
        img['src']=prefix+'images/jason-top-lawyers-2026.jpg'
        img['width']='600';img['height']='800'
        img['alt']='Jason Shapiro at the 2026 Top Lawyers of Long Island event' if soup.html.get('lang')!='es' else 'Jason Shapiro en el evento Top Lawyers de Long Island de 2026'
        figure=img.find_parent('figure')
        if figure:figure['class']=list(dict.fromkeys(figure.get('class',[])+['client-attorney-profile__media--event']))
    # Integrate introductory passages with their page title, above breadcrumbs.
    hero=soup.select_one('.client-inner-hero__content')
    if hero and not hero.select_one('.client-inner-hero__intro'):
        intro=soup.new_tag('div',attrs={'class':'client-inner-hero__intro'})
        summary=hero.select_one('.client-inner-hero__summary')
        if summary:intro.append(summary.extract())
        lead=soup.select_one('.editorial-lead')
        if lead:
            source=lead.find('div',recursive=False) if 'editorial-lead--media' in lead.get('class',[]) else lead
            for p in list(source.find_all('p',recursive=False)):intro.append(p.extract())
            if source!=lead and not source.get_text(strip=True):source.decompose()
            if not lead.get_text(strip=True) and not lead.find('img'):lead.decompose()
        else:
            firm=soup.select_one('.client-inner-intro')
            if firm:
                shell=firm.select_one('.client-shell')
                for n in list(shell.find_all(recursive=False)):
                    if n.name in ['h2','p']:intro.append(n.extract())
                if not shell.get_text(strip=True):firm.decompose()
            for p in list(soup.select('.client-contact .client-september-intro > p, .client-practice-index > .client-shell > .client-intro, .client-results-page__content > .client-shell > .client-intro')):
                parent=p.parent;intro.append(p.extract())
                if 'client-september-intro' in parent.get('class',[]) and not parent.get_text(strip=True):parent.decompose()
            # Existing Spanish practice pages use the older detail template.
            detail=soup.select_one('.client-practice-detail__content')
            if detail:
                for n in list(detail.find_all(recursive=False)):
                    if n.name not in ['h2','p']:break
                    intro.append(n.extract())
        if intro.get_text(strip=True):hero.h1.insert_after(intro)
        # Removing a lead should not leave a redundant gap above the cards.
        for lead in soup.select('.editorial-lead'):
            if lead.select_one('.client-practice-index__grid'):lead['class']=list(dict.fromkeys(lead.get('class',[])+['editorial-lead--cards']))
    after={key(n.get_text(' ',strip=True)) for n in soup.select('main p, main li, main h1, main h2, main h3, main summary')}
    missing=sorted(before-after)
    if missing:raise ValueError((str(path),missing))
    path.write_text(str(soup).rstrip()+'\n')
    report.append({'file':str(path.relative_to(ROOT)),'approved_text_preserved':True})
(ROOT/'docs/design-review').mkdir(parents=True,exist_ok=True)
(ROOT/'docs/design-review/content-preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Refined {len(report)} pages; approved text preserved.')
