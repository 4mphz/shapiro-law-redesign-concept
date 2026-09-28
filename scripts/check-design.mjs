import {chromium} from '/Users/aehun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const stage=process.argv[2]||'after';
const out='docs/design-review';await fs.mkdir(out+'/screenshots',{recursive:true});
const audit=JSON.parse(await fs.readFile('docs/september-update/source-audit.json','utf8'));
const samples=['index.html','practice-areas.html','practice-areas/construction-scaffold.html','practice-areas/scaffold-accidents.html','about.html','results.html','contact.html','es/index.html','es/practice-areas.html'];
const files=stage==='before'?samples:[...audit.pages.map(x=>x.file),'es/index.html','es/about.html','es/practice-areas.html','es/results.html','es/contact.html','es/practice-areas/construction-scaffold.html','es/practice-areas/premises.html','es/practice-areas/motor-vehicle.html','es/practice-areas/medical-malpractice.html'];
const b=await chromium.launch({executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true});const errors=[];let checks=0;
for(const width of (stage==='before'?[390,1440]:[320,390,768,1024,1440])){
 const p=await b.newPage({viewport:{width,height:950}});
 for(const file of files){
  await p.goto('http://127.0.0.1:8124/'+file+'?review=off',{waitUntil:'domcontentloaded'});
  await p.evaluate(async()=>{await document.fonts.ready;for(const i of document.images)i.loading='eager';for(const i of document.querySelectorAll('iframe'))i.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
  const state=await p.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,broken:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src),h1:document.querySelectorAll('h1').length,missingLabels:[...document.querySelectorAll('[aria-labelledby]')].flatMap(e=>e.getAttribute('aria-labelledby').split(' ').filter(id=>!document.getElementById(id))),looseBullets:[...document.querySelectorAll('.client-section li')].filter(li=>getComputedStyle(li,'::before').content==='""'&&parseFloat(getComputedStyle(li).paddingLeft)<10).length}));
  checks++;
  if(state.overflow||state.broken.length||state.h1!==1||(stage==='after'&&(state.missingLabels.length||state.looseBullets)))errors.push({file,width,...state});
  if(stage==='after'){
   if(await p.locator('.client-inner-hero').count()&&!(await p.locator('.client-inner-hero__intro').count()))errors.push({file,width,issue:'Missing header introduction'});
   if(file==='about.html'||file==='es/about.html'){
    if(await p.locator('.client-recognition-list li').count()!==4)errors.push({file,width,issue:'Recognition list must have four bullets'});
    if(!(await p.locator('#jason-shapiro .client-attorney-profile__media img').getAttribute('src')).endsWith('jason-top-lawyers-2026.jpg'))errors.push({file,width,issue:'Incorrect biography photo'});
   }
   const hiddenImages=await p.locator('main img').evaluateAll(es=>es.filter(e=>e.getBoundingClientRect().width<1&&getComputedStyle(e).display!=='none').map(e=>e.src));
   if(hiddenImages.length)errors.push({file,width,hiddenImages});
  }
  if(samples.includes(file)&&[390,1440].includes(width)){
   const key=file.replaceAll('/','-').replace('.html','');
   await p.screenshot({path:`${out}/screenshots/${key}-${width}-${stage}.jpg`,fullPage:true,quality:78});
   for(const [name,selector] of [['top','main > section:first-child'],['content','main > section:nth-child(2)']]){
    const el=p.locator(selector).first();const box=await el.boundingBox();
    if(box&&box.height<2600)await el.screenshot({path:`${out}/screenshots/${key}-${name}-${width}-${stage}.jpg`,quality:85});
   }
  }
 }
 await p.close();
}
await b.close();await fs.writeFile(`${out}/${stage}-checks.json`,JSON.stringify({checks,errors},null,2));console.log(JSON.stringify({checks,errors}));if(stage==='after'&&errors.length)process.exitCode=1;
