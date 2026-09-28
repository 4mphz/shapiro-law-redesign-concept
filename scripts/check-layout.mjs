import {chromium} from '/Users/aehun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const stage=process.argv[2]||'after';
const output='docs/layout-polish';
await fs.mkdir(output+'/screenshots',{recursive:true});
const browser=await chromium.launch({executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true});
const errors=[];
for(const width of [320,390,768,1024,1440]) {
 const page=await browser.newPage({viewport:{width,height:900}});
 for(const file of ['index.html','about.html','contact.html','results.html','practice-areas.html','practice-areas/scaffold-accidents.html','es/index.html']) {
  await page.goto('http://127.0.0.1:8124/'+file+'?review=off',{waitUntil:'networkidle'});
  await page.evaluate(async()=>{await document.fonts.ready;for(const img of document.images)img.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
  const state=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,broken:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src)}));
  if(state.overflow||state.broken.length)errors.push({file,width,...state});
  if([390,1440].includes(width)) {
   const name=file.replaceAll('/','-').replace('.html','');
   await page.screenshot({path:`${output}/screenshots/${name}-${width}-${stage}.jpg`,fullPage:true,quality:78});
   if(file==='index.html')for(const [label,selector] of [['hero','.client-hero'],['book','.client-book'],['firm','.client-firm']])await page.locator(selector).screenshot({path:`${output}/screenshots/${label}-${width}-${stage}.png`});
  }
 }
 await page.close();
}
await browser.close();
await fs.writeFile(`${output}/${stage}-checks.json`,JSON.stringify({errors},null,2));
console.log(JSON.stringify(errors));
if(errors.length)process.exitCode=1;
