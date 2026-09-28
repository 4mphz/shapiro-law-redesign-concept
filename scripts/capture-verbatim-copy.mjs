import { chromium } from '/Users/aehun/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';

const out = path.resolve('docs/verbatim-copy/screenshots');
await fs.mkdir(out, {recursive:true});
const manifest = JSON.parse(await fs.readFile('docs/verbatim-copy/source-manifest.json','utf8'));
const browser = await chromium.launch({executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true});
const problems=[];
const pages = process.argv.includes('--sample') ? ['index.html','es/index.html','about.html','contact.html'] : Object.keys(manifest.pages);
for (const [device,width,height] of [['desktop',1440,900],['mobile',390,844]]) {
  const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,isMobile:device==='mobile',hasTouch:device==='mobile'});
  const page=await context.newPage();
  for (const relative of pages) {
    for (const [version,port] of [['before',8123],['after',8124]]) {
      if (version === 'before' && process.argv.includes('--after-only')) continue;
      await page.goto(`http://127.0.0.1:${port}/${relative}?review=off`,{waitUntil:'networkidle'});
      await page.evaluate(async()=>{await document.fonts.ready; for(const frame of document.querySelectorAll('iframe')) frame.loading='eager'; for(const image of document.images) image.loading='eager'; await Promise.all(Array.from(document.images).map(i=>i.decode().catch(()=>{})));});
      if (relative.endsWith('index.html')) await page.waitForTimeout(1000);
      const file=relative.replaceAll('/','-').replace('.html','');
      await page.screenshot({path:path.join(out,`${file}-${device}-${version}.jpg`),fullPage:true,type:'jpeg',quality:72});
      if (version==='after') {
        const info=await page.evaluate(()=>({width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,broken:Array.from(document.images).filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src), h1:document.querySelector('h1')?.getBoundingClientRect().toJSON()}));
        if(info.scrollWidth>info.width || info.broken.length) problems.push({relative,device,...info});
        if(relative==='index.html') {
          await page.screenshot({path:path.join(out,`homepage-${device}-after-top.png`)});
        }
      }
      console.log(`${file} ${device} ${version}`);
    }
  }
  await context.close();
}
await browser.close();
await fs.writeFile('docs/verbatim-copy/browser-checks.json',JSON.stringify({pages:pages.length,devices:2,problems},null,2)+'\n');
if(problems.length) {console.log(JSON.stringify(problems,null,2));process.exitCode=1;}
