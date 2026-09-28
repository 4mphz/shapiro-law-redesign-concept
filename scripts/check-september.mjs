import {chromium} from '/Users/aehun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const output='docs/september-update';
await fs.mkdir(output+'/screenshots',{recursive:true});
const audit=JSON.parse(await fs.readFile(output+'/source-audit.json','utf8'));
const browser=await chromium.launch({executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true});
const errors=[];
const samples=['index.html','about.html','results.html','contact.html','practice-areas.html','practice-areas/scaffold-accidents.html','es/index.html'];
for(const width of [390,1440,320]) {
 const page=await browser.newPage({viewport:{width,height:900}});
 for(const file of [...audit.pages.map(p=>p.file),'es/index.html']) {
  if(width===320&&!samples.includes(file))continue;
  await page.goto('http://127.0.0.1:8124/'+file+'?review=off',{waitUntil:'networkidle'});
  await page.evaluate(async()=>{await document.fonts.ready;for(const img of document.images)img.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
  const state=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,broken:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src),h1:document.querySelectorAll('h1').length,logo:document.querySelector('.client-logo')?.getBoundingClientRect().toJSON(),icons:[...document.querySelectorAll('.client-mobile-socials a')].map(a=>({name:a.getAttribute('aria-label')||a.textContent,visible:!!a.getClientRects().length}))}));
  if(state.overflow||state.broken.length||state.h1!==1)errors.push({file,width,...state});
  if(samples.includes(file)&&width!==320){
   await page.screenshot({path:output+'/screenshots/'+file.replaceAll('/','-').replace('.html','')+'-'+width+'-after.jpg',fullPage:true,quality:78});
   if(file==='index.html')await page.screenshot({path:output+'/screenshots/hero-'+width+'-after.png'});
  }
 }
 if(width!==320)for(const file of samples.filter(f=>f!=='practice-areas/scaffold-accidents.html')){
  await page.goto('http://127.0.0.1:8123/'+file+'?review=off',{waitUntil:'networkidle'});
  await page.screenshot({path:output+'/screenshots/'+file.replaceAll('/','-').replace('.html','')+'-'+width+'-before.jpg',fullPage:true,quality:78});
 }
 await page.close();
}
await browser.close();
await fs.writeFile(output+'/browser-checks.json',JSON.stringify({errors},null,2));
console.log(JSON.stringify(errors,null,2));
if(errors.length)process.exitCode=1;
