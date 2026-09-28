import {chromium} from '/Users/aehun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const files=JSON.parse(await fs.readFile('docs/design-review/content-preservation.json','utf8')).map(x=>x.file);
const b=await chromium.launch({executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true});const checks=[];
for(const width of [320,390,768,1024,1440]){
 const p=await b.newPage({viewport:{width,height:950}});
 for(const file of files){
  await p.goto('http://127.0.0.1:8124/'+file+'?review=off',{waitUntil:'domcontentloaded'});
  const result=await p.evaluate(async()=>{await document.fonts.ready;const h=document.querySelector('.client-header .brand-wordmark'),f=document.querySelector('.client-footer__logo .brand-wordmark');const name=h.querySelector('.brand-wordmark__name'),line=h.querySelector('.brand-wordmark__line');return {sameMarkup:h.innerHTML===f.innerHTML,noLogoImages:!document.querySelector('.client-logo img,.client-footer__logo img'),sameWidth:Math.abs(h.getBoundingClientRect().width-f.getBoundingClientRect().width)<1,leftAligned:Math.abs(name.getBoundingClientRect().left-line.getBoundingClientRect().left)<1,width:f.getBoundingClientRect().width,overflow:document.documentElement.scrollWidth>innerWidth};});
  result.edgeAlignment=await p.evaluate(()=>Array.from(document.querySelectorAll('.brand-wordmark')).map(mark=>{const name=mark.querySelector('.brand-wordmark__name');const range=document.createRange();range.setStart(name.firstChild,6);range.setEnd(name.firstChild,7);const o=range.getBoundingClientRect();const s=mark.querySelector('.brand-wordmark__offices > :last-child').getBoundingClientRect();return Math.abs(o.right-parseFloat(getComputedStyle(name).letterSpacing)-s.right);}));
  if(!result.sameMarkup||!result.noLogoImages||!result.sameWidth||!result.leftAligned||result.width<1||result.overflow||result.edgeAlignment.some(delta=>delta>0.5))throw Error(JSON.stringify({file,width,...result}));
  checks.push({file,width,...result});
  if(['about.html','es/about.html'].includes(file)&&[390,1440].includes(width)){await p.locator('.client-footer').screenshot({path:`docs/design-review/screenshots/shared-logo-${file.replaceAll('/','-').replace('.html','')}-${width}.jpg`,quality:85});await p.locator('.client-header').screenshot({path:`docs/design-review/screenshots/shared-logo-header-${file.replaceAll('/','-').replace('.html','')}-${width}.jpg`,quality:85});}
 }
 await p.close();
}
await b.close();await fs.writeFile('docs/design-review/shared-logo-checks.json',JSON.stringify({checks},null,2));console.log(`${checks.length} shared-logo checks passed.`);
