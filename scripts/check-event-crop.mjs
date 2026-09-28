import {chromium} from '/Users/aehun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const b=await chromium.launch({executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true});const checks=[];
for(const width of [320,390,768,1024,1440])for(const file of ['about.html','es/about.html']){
 const p=await b.newPage({viewport:{width,height:950}});await p.goto('http://127.0.0.1:8124/'+file+'?review=off');
 await p.evaluate(async()=>{await document.fonts.ready;for(const i of document.images)i.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
 const state=await p.locator('.client-attorney-profile__media--event').evaluate(el=>{const r=el.getBoundingClientRect(),img=el.querySelector('img');return {ratio:r.width/r.height,fit:getComputedStyle(img).objectFit,loaded:img.naturalWidth>0,overflow:document.documentElement.scrollWidth>innerWidth};});
 if(Math.abs(state.ratio-1.25)>.02||state.fit!=='cover'||!state.loaded||state.overflow)throw Error(JSON.stringify({width,file,...state}));
 checks.push({width,file,...state});
 if([390,1440].includes(width))await p.screenshot({path:`docs/design-review/screenshots/${file.replaceAll('/','-').replace('.html','')}-${width}-after.jpg`,fullPage:true,quality:78});
 await p.close();
}
await b.close();await fs.writeFile('docs/design-review/event-crop-checks.json',JSON.stringify({checks},null,2));console.log('10 event-photo layout checks passed.');
