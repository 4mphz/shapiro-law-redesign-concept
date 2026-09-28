"""Static acceptance checks for the September migration."""
import json
import re
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'docs/september-update/source-audit.json').read_text())
errors=[]
for item in manifest['pages']:
    path=root/item['file']; soup=BeautifulSoup(path.read_text(),'html.parser')
    text=soup.get_text(' ',strip=True)
    for pattern in [r'\$115',r'\[(?:ADD|CONFIRM)',r'INTERNAL REFERENCE',r'DO NOT PUBLISH',r'anticipated \$',r'Free Consultations',r'No Fee Until',r'★']:
        if re.search(pattern,text,re.I):errors.append([item['file'],pattern])
    for a in soup.select('a[href]'):
        href=a['href'].split('#')[0].split('?')[0]
        if href and not re.match(r'\w+:|//',href) and not (path.parent/href).exists():errors.append([item['file'],'Missing link '+href])
    assert soup.select_one('.client-logo img')['src'].endswith('shapiro-official-logo.png')
    assert len(soup.select('.client-mobile-socials .client-social'))==2
home=BeautifulSoup((root/'index.html').read_text(),'html.parser')
assert home.h1.get_text()=='Personal Injury Trial Attorneys'
assert [li.get_text() for li in home.select('.client-hero__promises li')]==['No Fee Unless We Win Your Case','Free Consultation','Se Habla Español']
assert len(BeautifulSoup((root/'results.html').read_text(),'html.parser').select('.client-case-result'))==50
assert (root/'css/styles.css').read_bytes()==subprocess.check_output(['git','show','b6ab7c99:css/styles.css'],cwd=root)
assert len(manifest['pages'])==29
report={'pages':29,'results':50,'background_styles_unchanged':True,'errors':errors}
(root/'docs/september-update/static-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert not errors
