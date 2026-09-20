// Browser smoke test against the running local server. Does not submit a paid
// generation or modify automation settings. Credentials are read without logging.
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(path.join(root,'output/jev-vs-llms/package.json'));
const {chromium}=require('playwright');
const password=fs.readFileSync(path.join(root,'secrets/dashboard-login.txt'),'utf8').match(/Password: (.+)/)[1];
const browser=await chromium.launch({headless:true,executablePath:fs.existsSync('/usr/bin/google-chrome')?'/usr/bin/google-chrome':undefined});const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];
page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:2021');await page.locator('#login').waitFor({state:'visible'});
await page.locator('#password').fill(password);await page.locator('#login-form button').click();
await page.locator('#app').waitFor({state:'visible'});
await page.screenshot({path:path.join(root,'state/dashboard-desktop.png'),fullPage:true});
await page.locator('#recent [data-video="jev-vs-llms"]').click();
await page.locator('video').waitFor();await page.waitForFunction(()=>document.querySelector('video').readyState>=1);
const duration=await page.locator('video').evaluate(v=>v.duration);
if(duration<319||duration>321)throw Error('Unexpected video duration');
await page.locator('[data-close="detail-dialog"]').click();await page.locator('#new-video').click();
await page.locator('#create-form input[name="topic"]').fill('Example topic — not submitted');
await page.locator('[data-close="create-dialog"]').click();
await page.locator('nav [data-tab="settings"]').click();await page.locator('#settings-form').waitFor({state:'visible'});
await page.locator('nav [data-tab="overview"]').click();await page.setViewportSize({width:390,height:844});
await page.screenshot({path:path.join(root,'state/dashboard-mobile.png'),fullPage:true});
if(errors.length)throw Error(errors.join('\n'));
await browser.close();console.log('Browser smoke passed: login, dashboard, Jev video playback metadata, create form, settings and mobile layout.');
