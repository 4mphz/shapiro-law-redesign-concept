import {chromium} from '/Users/aehun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const files=JSON.parse(await fs.readFile('docs/design-review/content-preservation.json','utf8')).map(x=>x.file);
const b=await chromium.launch({executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true});const checks=[];
for(const width of [320,390,1440]){
 const p=await b.newPage({viewport:{width,height:950}});
 for(const file of files){
  await p.goto('http://127.0.0.1:8124/'+file+'?review=off',{waitUntil:'domcontentloaded'});
  const result=await p.evaluate(async()=>{const h=document.querySelector('.client-header .client-logo img'),f=document.querySelector('.client-footer__logo img');await Promise.all([h.decode(),f.decode()]);return {sameAsset:h.src===f.src,loaded:f.naturalWidth>0,width:f.getBoundingClientRect().width,overflow:document.documentElement.scrollWidth>innerWidth};});
  if(!result.sameAsset||!result.loaded||result.width<1||result.overflow)throw Error(JSON.stringify({file,width,...result}));
  checks.push({file,width,...result});
  if(['about.html','es/about.html'].includes(file)&&width!==320){await p.evaluate(()=>document.fonts.ready);await p.locator('.client-footer').screenshot({path:`docs/design-review/screenshots/shared-logo-${file.replaceAll('/','-').replace('.html','')}-${width}.jpg`,quality:85});}
 }
 await p.close();
}
await b.close();await fs.writeFile('docs/design-review/shared-logo-checks.json',JSON.stringify({checks},null,2));console.log(`${checks.length} shared-logo checks passed.`);
