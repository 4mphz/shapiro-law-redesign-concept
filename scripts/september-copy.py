"""Map the September client package into the existing design, with an audit manifest.

Run with the client DOCX path. Does not publish, merge, or change backgrounds.
"""
import copy
import hashlib
import json
import re
import sys
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = 'b6ab7c99c64bb3516ecfdfb1d569a6732e58d5b5'
SOURCE = Path(sys.argv[1])
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
body = ET.fromstring(zipfile.ZipFile(SOURCE).read('word/document.xml')).find('w:body', NS)
pages = []
current = None
for el in body:
    if el.tag == W + 'tbl':
        cells = [' '.join(''.join(t.itertext()) for t in c.findall('.//w:t', NS)) for c in el.findall('.//w:tc', NS)]
        if cells and cells[0] == 'URL':
            current = {'url': cells[1], 'title': cells[3], 'description': cells[5], 'blocks': []}
            pages.append(current)
        elif current:
            for paragraph in el.findall('.//w:p', NS):
                text = ''.join(t.text or '' for t in paragraph.findall('.//w:t', NS)).strip()
                if text:
                    current['blocks'].append({'text':text,'style':''})
    elif el.tag == W + 'p' and current:
        text = ''.join(t.text or '' for t in el.findall('.//w:t', NS)).strip()
        style = el.find('w:pPr/w:pStyle', NS)
        style = style.get(W + 'val', '') if style is not None else ''
        if text == 'Implementation and Verification Notes':
            current = None
        elif text in ('CORE PAGE', 'PRIMARY PRACTICE-AREA PAGE', 'DEDICATED SEO PAGE'):
            current = None
        elif text:
            current['blocks'].append({'text': text, 'style': style})
assert len(pages) == 29, len(pages)
exceptions = []

def clean(text):
    original = text
    text = re.sub(r'\[[^\]]*\]', '', text).strip()
    if 'anticipated' in text.lower():
        text = re.split(r'; (?:plus |and )an anticipated', text, maxsplit=1)[0].rstrip('.') + '.'
    if text.startswith('RESULT: Use practice-area-specific'):
        text = 'Every case depends on its own facts. Contact the firm to discuss your circumstances.'
    text = text.replace('—', ', ').replace('–', '-')
    if '$115' in text:
        if text.startswith('The firm’s current selected-results list'):
            text = 'The firm has obtained $300M+ in results and 50+ million-dollar recoveries. ' + text.split('Featured results include', 1)[1].join(['Featured results include', ''])
        elif text.startswith('SELECTED RESULTS:'):
            text = 'The firm has obtained $300M+ in results and 50+ million-dollar recoveries. Explore selected results below.'
        elif text.startswith('Selected New York'):
            text = 'Selected New York personal injury results from Shapiro Law Offices, PLLC. $300M+ in results and 50+ million-dollar recoveries.'
        else:
            text = text.replace('More than $115 million in selected results.', '$300M+ in results and 50+ million-dollar recoveries.')
    text = text.replace('Serious Injury Cases Built for the Disputes Ahead', 'Serious Cases Require Serious Preparation')
    text = text.replace('No legal fee unless the firm obtains a recovery for you.', 'No Fee Unless We Win Your Case.')
    if text != original:
        exceptions.append({'source': original, 'public': text})
    return text

def filename(url):
    return {'/': 'index.html', '/attorneys/': 'about.html', '/practice-areas/': 'practice-areas.html', '/results/': 'results.html', '/contact/': 'contact.html'}.get(url, url.strip('/') + '.html')

def soupfile(name):
    return BeautifulSoup((ROOT / name).read_text(), 'html.parser')

def original(name):
    return BeautifulSoup(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT,text=True),'html.parser')

def node(soup, tag, text='', cls=None, **attrs):
    if cls:
        attrs['class'] = cls
    n = soup.new_tag(tag, attrs=attrs)
    n.string = text
    return n

def settext(soup, selector, text):
    n = soup.select_one(selector)
    if n:
        n.clear()
        n.append(text)
    return n

def groups(page):
    result = []
    for b in page['blocks']:
        if b['style'].startswith('Heading'):
            result.append([b['text'], []])
        elif result:
            result[-1][1].append(b)
    return result

def render(soup, target, blocks, prefix=''):
    ul = None
    for b in blocks:
        raw = b['text']
        if raw.startswith(('INTERNAL REFERENCE', 'DO NOT PUBLISH', 'PROFILE DETAILS TO ADD')):
            exceptions.append({'source':raw, 'public':'Omitted internal note'})
            continue
        if raw.startswith('FEATURED RESULTS:'):
            continue
        if raw.startswith('[REQUEST A FREE CONSULTATION]'):
            target.append(node(soup,'a','Request a Free Consultation','client-btn',href=prefix+'contact.html#contact-form'))
            continue
        if raw.startswith('[EXPLORE '):
            label, url = raw.split(']',1)
            target.append(node(soup,'a',label[1:].title(),'client-text-link',href=prefix+filename(url.strip())))
            continue
        text = clean(raw)
        if not text:
            continue
        if b['style'] == 'ListBullet':
            if ul is None:
                ul = node(soup,'ul')
                target.append(ul)
            ul.append(node(soup,'li',text))
        else:
            ul = None
            target.append(node(soup, 'h2' if b['style'].startswith('Heading') else 'p', text))

templates = {name:original(name) for name in ['index.html','about.html','contact.html','practice-areas.html','results.html','practice-areas/construction-scaffold.html']}

def shared(soup, relative, english=True):
    prefix = '../' * (len(Path(relative).parts)-1)
    for n in soup.select('[data-copy-id]'):
        del n['data-copy-id']
    for img in soup.select('img[src*="lawyers-guide-book"]'):
        img['src'] = prefix + 'images/lawyers-guide-actual-cover.png'
        img['width'],img['height'] = '310','466'
    for logo in soup.select('.client-logo'):
        logo.clear()
        logo.append(node(soup,'img',src=prefix+'images/shapiro-official-logo.png',alt='Shapiro Law Offices, PLLC',width='280',height='77'))
    controls = soup.select_one('.mobile-header-controls')
    if controls and not controls.select_one('.client-mobile-socials'):
        socials=node(soup,'div',cls='client-mobile-socials')
        for n in soup.select('.client-header__actions .client-social'):
            socials.append(copy.deepcopy(n))
        lang=controls.select_one('.lang-pill-mobile')
        textlink=soup.select_one('.client-text-us')
        if textlink:
            socials.append(copy.deepcopy(textlink))
        if lang:
            socials.append(lang.extract())
        controls.insert(0,socials)
    for text in list(soup.find_all(string=True)):
        if text.parent.name in ('script','style'):
            continue
        value=str(text)
        value=re.sub(r'No Fee (?:Until|Unless) We Win(?: Your Case)?!*','No Fee Unless We Win Your Case',value,flags=re.I)
        value=value.replace('Free Consultations','Free Consultation').replace('★ Se Habla Español ★','Se Habla Español')
        if value != str(text):
            text.replace_with(value)
    for n in soup.select('.client-practice-card > span'):
        if n.get_text(strip=True).isdigit():
            n.decompose()
    style=soup.select_one('link[href*="approved-copy.css"]')
    if style:
        style['href']=prefix+'css/approved-copy.css?v=20260927-1'
    if english:
        for a in soup.select('.client-btn[href*="contact.html"]'):
            a.string='Request a Free Consultation'
        for cta in soup.select('.client-cta'):
            settext(cta,'h2','Speak With a New York Personal Injury Attorney')
            settext(cta,'h5','No Fee Unless We Win Your Case')
            settext(cta,'p','Evidence can disappear and legal deadlines can be shorter than expected. Call Shapiro Law Offices, PLLC at 718.295.7000 for a free consultation. Se habla español.')
    return soup

def interior(page, relative):
    exists=subprocess.run(['git','cat-file','-e',BASE+':'+relative],cwd=ROOT,capture_output=True).returncode==0
    source = relative if exists else 'practice-areas/construction-scaffold.html'
    soup=original(source)
    if not exists:
        for a in soup.select('a[aria-current="page"]'):
            a.attrs.pop('aria-current',None)
        # No invented Spanish translation or false language-equivalent metadata.
        for alt in soup.select('link[hreflang]'):
            alt.decompose()
        for a in soup.select('.client-lang,.lang-pill-mobile'):
            a['href']='../es/practice-areas.html'
    main=soup.select_one('main')
    hero=copy.deepcopy(main.select_one('.client-inner-hero'))
    cta=copy.deepcopy(main.select_one('.client-cta'))
    main.clear()
    main.append(hero)
    if cta:
        main.append(cta)
    title=clean(page['blocks'][0]['text'])
    settext(soup,'.client-inner-hero h1',title)
    settext(soup,'.client-breadcrumbs li:last-child',title)
    return soup,main,cta

for page in pages:
    relative=filename(page['url'])
    prefix='../' if '/' in relative else ''
    if relative=='index.html':
        soup=copy.deepcopy(templates['index.html'])
        g=dict(groups(page))
        settext(soup,'.client-hero h1','Personal Injury Trial Attorneys')
        settext(soup,'.client-hero__promises li:nth-child(1)','No Fee Unless We Win Your Case')
        settext(soup,'.client-hero__promises li:nth-child(2)','Free Consultation')
        settext(soup,'.client-hero__promises li:nth-child(3)','Se Habla Español')
        # Put source copy into the approved sections, not a replacement page layout.
        strip=soup.select_one('.client-source-strip')
        if strip: strip.decompose()
        section=node(soup,'section',cls='client-section client-september-intro')
        shell=node(soup,'div',cls='client-shell')
        section.append(shell)
        render(soup,shell,g['New York Personal Injury Trial Attorneys'])
        shell.append(node(soup,'h2','Led by Jason Shapiro'))
        render(soup,shell,g['Led by Jason Shapiro'])
        soup.select_one('.client-proof').insert_after(section)
        settext(soup,'.client-results h2','Results That Changed Lives')
        settext(soup,'.client-results .client-intro',clean(g['Proven Results. Personal Attention.'][0]['text']))
        settext(soup,'.client-results .client-text-link','View More Case Results')
        settext(soup,'.client-practice > .client-shell > h2','Serious Cases Require Serious Preparation')
        heading=soup.select_one('.client-practice > .client-shell > h2')
        heading.insert_after(node(soup,'p','We prepare cases from the outset with the possibility of trial in mind. '+g['Focused Personal Injury Representation'][0]['text'],'client-intro'))
        names=['Scaffold and Construction Accidents','Motor-Vehicle Accidents','Premises and Sidewalk Accidents','Medical Malpractice and Birth Injuries']
        overview=pages[2]
        og=dict(groups(overview))
        for card,name in zip(soup.select('.client-practice-card'),names):
            card.clear();card.append(node(soup,'h3',name));render(soup,card,og[name][:1])
        firm=soup.select_one('.client-firm > .client-shell');firm.clear()
        firm.append(node(soup,'p','Why Choose Our Firm','client-eyebrow'))
        firm.append(node(soup,'h2','Experienced Lawyers Handle Your Case'))
        render(soup,firm,g['Experienced Lawyers Handle Your Case'])
        panel=node(soup,'div',cls='client-firm__panel');firm.append(panel)
        panel.append(node(soup,'h3','Why Injured New Yorkers Choose Shapiro Law Offices, PLLC'))
        render(soup,panel,g['Why Injured New Yorkers Choose Shapiro Law Offices, PLLC'])
        ap=dict(groups(pages[1]))
        settext(soup,'.client-attorneys .client-intro',ap['A Trial-Focused Team'][0]['text'].replace('—', ', '))
        cards=soup.select('.client-attorney-card')
        for card,key in zip(cards,['Jason Shapiro, Esq.','Hon. Ernest Buonocore']):
            card.clear();card.append(node(soup,'h3',key));render(soup,card,ap[key][:2])
            card.append(node(soup,'a','Meet Our Attorneys','client-text-link',href='about.html'))
        book=soup.select_one('.client-book__copy')
        if book:
            book.clear();book.append(node(soup,'h2','He Wrote the Book on Personal Injury Law'))
            render(soup,book,g['He Wrote the Book on Personal Injury Law'])
            book.append(node(soup,'a','Meet Jason Shapiro','client-btn',href='about.html#jason-shapiro'))
        # Keep one detailed intake form on Contact, with the document's homepage call to action.
        contact=soup.select_one('.client-contact')
        if contact:
            contact.clear();shell=node(soup,'div',cls='client-shell');contact.append(shell)
            shell.append(node(soup,'h2','Tell Us What Happened'));render(soup,shell,g['Tell Us What Happened'])
            shell.append(node(soup,'a','Request a Free Consultation','client-btn',href='contact.html#contact-form'))
    elif relative=='about.html':
        soup=copy.deepcopy(templates['about.html']);g=dict(groups(page))
        intro=soup.select_one('.client-inner-intro .client-shell');intro.clear()
        intro.append(node(soup,'h2',page['blocks'][0]['text']));render(soup,intro,g[page['blocks'][0]['text']])
        for selector,title in [('#jason-shapiro','Jason Shapiro, Esq.'),('#ernest-buonocore','Hon. Ernest Buonocore')]:
            content=soup.select_one(selector+' .client-attorney-profile__content');content.clear()
            content.append(node(soup,'h2',title));render(soup,content,g[title])
        pending=soup.select_one('[data-photo-pending]')
        if pending:
            pending.clear();pending.attrs={'class':['client-attorney-quote']}
            pending.append(node(soup,'h3','A Trial-Focused Team'))
            render(soup,pending,g['A Trial-Focused Team'])
        book=soup.select_one('.client-book-feature__copy');book.clear()
        book.append(node(soup,'h2','He Wrote the Book on Personal Injury Law'));render(soup,book,g['He Wrote the Book on Personal Injury Law'])
    elif relative=='contact.html':
        soup=copy.deepcopy(templates['contact.html']);g=dict(groups(page))
        settext(soup,'.client-inner-hero h1','Tell Us What Happened')
        shell=soup.select_one('.client-contact > .client-shell')
        intro=node(soup,'div',cls='client-september-intro');render(soup,intro,g['Tell Us What Happened']);shell.insert(0,intro)
        settext(soup,'#contact-form-title','Request a Free Consultation')
        settext(soup,'#contact-disclaimer',next(b['text'].removeprefix('FORM NOTICE: ') for b in page['blocks'] if b['text'].startswith('FORM NOTICE:')))
        form=soup.select_one('.client-contact__form-grid');form.clear()
        fields=[('Name *','name','text'),('Telephone *','phone','tel'),('Email','email','email'),('Preferred language','language','text'),('Date of accident or malpractice','date','date'),('Location','location','text'),('Type of matter','matter','text'),('Brief description','description','textarea'),('Best time and method to contact you','preferred-contact','text'),('How did you hear about us?','referral','text')]
        for label,name,typ in fields:
            wrap=node(soup,'div',cls='client-contact__field');form.append(wrap)
            wrap.append(node(soup,'label',label,**{'for':'f-'+name}))
            inp=node(soup,'textarea' if typ=='textarea' else 'input',id='f-'+name,name=name)
            if typ!='textarea':inp['type']=typ
            else:inp['rows']='6'
            if label.endswith('*'):inp['required']=''
            wrap.append(inp)
        info=node(soup,'section',cls='client-section');inner=node(soup,'div',cls='client-shell');info.append(inner)
        for key in ['What Happens After You Contact Us','Emergency Guidance']:
            inner.append(node(soup,'h2',key));render(soup,inner,g[key])
        soup.select_one('.client-contact').insert_after(info)
    else:
        soup,main,cta=interior(page,relative)
        section=node(soup,'section',cls='client-section client-september-content')
        shell=node(soup,'div',cls='client-shell');section.append(shell)
        if cta:cta.insert_before(section)
        else:main.append(section)
        if relative=='results.html':
            blocks=page['blocks']
            for b in blocks[1:5]:render(soup,shell,[b])
            grid=node(soup,'div',cls='client-complete-results');shell.append(grid)
            count=0
            for i,b in enumerate(blocks):
                if b['text'].startswith('Pending Settlements'):break
                if re.fullmatch(r'\$[\d,]+',b['text']):
                    title=clean(blocks[i+1]['text']) or 'Selected Recovery';description=clean(blocks[i+2]['text'])
                    if not description:
                        description = {
                            'Medical Malpractice Verdict':'A $3 million verdict in a medical malpractice case handled by the firm.',
                            'Slip-and-Fall on Water':'A $2 million recovery in a case involving a slip-and-fall on water.',
                            'Stairway Fall':'A $1 million recovery in a case involving a stairway fall.',
                            'Selected Recovery':f"A {b['text']} recovery obtained by Shapiro Law Offices, PLLC.",
                        }.get(title, f"The firm obtained {b['text']} in this {title.lower()} case.")
                        exceptions.append({'source':blocks[i+2]['text'],'public':description,'reason':'Client-authorized factual filler'})
                    card=node(soup,'article',cls='client-case-result');grid.append(card)
                    card.append(node(soup,'strong',b['text']));card.append(node(soup,'h2',title));card.append(node(soup,'p',description));count+=1
            assert count==50,count
            g=dict(groups(page));shell.append(node(soup,'h2','Your Case Deserves the Same Level of Preparation'));render(soup,shell,g['Your Case Deserves the Same Level of Preparation'])
        elif relative=='practice-areas.html':
            g=groups(page)
            render(soup,shell,g[0][1],prefix)
            grid=node(soup,'div',cls='client-practice-index__grid');shell.append(grid)
            for heading,blocks in g[1:5]:
                card=node(soup,'article',cls='client-practice-index-card');grid.append(card)
                card.append(node(soup,'h2',heading));render(soup,card,blocks,prefix)
            for heading,blocks in g[5:]:
                shell.append(node(soup,'h2',heading));render(soup,shell,blocks,prefix)
        else:
            render(soup,shell,page['blocks'][1:],prefix)
            if relative in ('practice-areas/construction-scaffold.html','practice-areas/motor-vehicle.html','practice-areas/premises.html','practice-areas/medical-malpractice.html'):
                media=original(relative).select_one('.client-practice-media')
                if media:
                    media['class']=['client-september-media']
                    shell.insert(0,media)
    shared(soup,relative)
    soup.title.string=clean(page['title'])
    soup.select_one('meta[name="description"]')['content']=clean(page['description'])
    soup.body['class']=list(dict.fromkeys(soup.body.get('class',[])+['client-september-copy']))
    (ROOT/relative).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/relative).write_text(str(soup).rstrip()+'\n')

# Make every new guide reachable from the overview, with real relative URLs.
overview=soupfile('practice-areas.html')
shell=overview.select_one('.client-september-content .client-shell')
shell.append(node(overview,'h2','Explore Our Practice Area Guides'))
links=node(overview,'ul',cls='client-guide-links');shell.append(links)
for page in pages[9:]:
    li=node(overview,'li');li.append(node(overview,'a',page['title'].split(' | ')[0],href=filename(page['url'])));links.append(li)
(ROOT/'practice-areas.html').write_text(str(overview).rstrip()+'\n')

# Shared asset and mobile-header fixes also apply to existing Spanish pages.
for path in (ROOT/'es').rglob('*.html'):
    relative=str(path.relative_to(ROOT));soup=shared(original(relative),relative,False)
    path.write_text(str(soup).rstrip()+'\n')
out=ROOT/'docs/september-update';out.mkdir(parents=True,exist_ok=True)
(out/'source-audit.json').write_text(json.dumps({'source':SOURCE.name,'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'pages':[{'file':filename(p['url']),'title':p['title']} for p in pages],'exceptions':exceptions,'background':'Unchanged by explicit request','spanish':'Shared header/assets updated; September Spanish copy migration pending'},indent=2,ensure_ascii=False)+'\n')
print(f'Updated {len(pages)} English pages and shared assets on Spanish pages.')
