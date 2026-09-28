"""Idempotent presentation pass. Preserves approved text, assets and backgrounds."""
from pathlib import Path
import json
import re
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
    link['href']=prefix+'css/design-refinement.css?v=20260927-1'
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
    after={key(n.get_text(' ',strip=True)) for n in soup.select('main p, main li, main h1, main h2, main h3, main summary')}
    missing=sorted(before-after)
    if missing:raise ValueError((str(path),missing))
    path.write_text(str(soup).rstrip()+'\n')
    report.append({'file':str(path.relative_to(ROOT)),'approved_text_preserved':True})
(ROOT/'docs/design-review').mkdir(parents=True,exist_ok=True)
(ROOT/'docs/design-review/content-preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Refined {len(report)} pages; approved text preserved.')
