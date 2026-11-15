"""Run with the repository Python Playwright installation and a running Vite server.
DOMROV_BASE_URL=http://127.0.0.1:5173 .venv/bin/python react-client/scripts/domrov_qa.py
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
BASE=os.environ.get('DOMROV_BASE_URL','http://127.0.0.1:5173')
OUT=Path('docs/domrov-qa'); OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE','/home/panha/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome'),headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for width in (360,768,1440):
  page.set_viewport_size({'width':width,'height':1000})
  for path,name in [('/','home'),('/chat','chat'),('/procedures','procedures'),('/procedures/driving-licence','procedure'),('/search?q=ប័ណ្ណបើកបរ','search'),('/articles/1/8','article'),('/saved','saved')]:
   page.goto(BASE+path);page.wait_for_timeout(1000);page.evaluate('document.fonts.ready')
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,path,'overflow')
   assert page.evaluate("document.fonts.check('16px \"Noto Sans Khmer\"')")
   page.screenshot(path=str(OUT/f'{name}-{width}.png'),full_page=True)
 print('PASS: 21 route/viewport checks, Khmer font loaded, no horizontal overflow')
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto(BASE+'/');page.get_by_label('តើថ្ងៃនេះ យើងអាចជួយអ្វីអ្នកបាន?').fill('តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?')
 page.get_by_role('button',name='សួរ DOMROV').click();expect(page.get_by_label('សំណួររបស់អ្នក')).to_have_value('តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?')
 page.get_by_role('button',name='ផ្ញើ').click();expect(page.get_by_text('ប្រភពយោង',exact=True).first).to_be_visible()
 expect(page.get_by_role('link',name='អានអត្ថបទ').first).to_be_visible()
 assert page.get_by_role('link',name='បើក PDF ដើម').first.get_attribute('href').startswith('https://')
 page.screenshot(path=str(OUT/'answer-1440.png'),full_page=True)
 page.set_viewport_size({'width':360,'height':900});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');page.screenshot(path=str(OUT/'answer-360.png'),full_page=True)
 page.set_viewport_size({'width':1440,'height':1000})
 page.get_by_role('link',name='អានអត្ថបទ').first.click();expect(page.get_by_text('អត្ថបទដើម',exact=True)).to_be_visible()
 page.goto(BASE+'/procedures/driving-licence');page.get_by_role('checkbox').first.check();page.get_by_role('button',name='រក្សាទុកបញ្ជី',exact=True).click()
 page.reload();expect(page.get_by_role('checkbox').first).to_be_checked()
 page.evaluate('window.print=()=>window.__printed=true');page.get_by_role('button',name='បោះពុម្ព / PDF').click();assert page.evaluate('window.__printed')
 page.pdf(path=str(OUT/'checklist.pdf'),format='A4',print_background=True)
 page.goto(BASE+'/saved');expect(page.get_by_text('គំរូ · 1/3')).to_be_visible();page.get_by_role('button',name='លុបបញ្ជីទាំងអស់').click();page.reload();expect(page.get_by_text('មិនទាន់មានការងាររក្សាទុក')).to_be_visible()
 print('PASS: question → answer → citation → article; checklist save/reload/delete; print action and PDF')
 page.goto(BASE+'/chat');page.get_by_label('សំណួររបស់អ្នក').fill('xyz-no-evidence');page.get_by_role('button',name='ផ្ញើ').click();expect(page.get_by_text('មិនអាចផ្តល់ចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់')).to_be_visible()
 page.goto(BASE+'/search?q=xyz-no-evidence');expect(page.get_by_text('រកមិនឃើញលទ្ធផល',exact=True)).to_be_visible()
 page.goto(BASE+'/search?q=8&mode=exact_article');expect(page.get_by_role('link',name='អានអត្ថបទ').first).to_be_visible()
 page.goto(BASE+'/articles/unknown/9');expect(page.get_by_text('រកមិនឃើញអត្ថបទ',exact=True)).to_be_visible()
 page.goto(BASE+'/');page.keyboard.press('Tab');expect(page.get_by_role('link',name='រំលងទៅមាតិកា')).to_be_focused();page.keyboard.press('Enter');expect(page.locator('main')).to_be_focused()
 page.emulate_media(reduced_motion='reduce');assert page.locator('.service-card').first.evaluate('(e)=>getComputedStyle(e).transitionDuration')=='0s'
 page.goto(BASE+'/saved');page.evaluate("localStorage.setItem('domrov.checklists.v1', 'invalid')");page.reload();expect(page.get_by_text('មិនអាចអានទិន្នន័យលើឧបករណ៍បានទេ។',exact=False)).to_be_visible()
 page.get_by_role('button',name='លុបបញ្ជីទាំងអស់').click();page.reload();assert page.evaluate("localStorage.getItem('domrov.checklists.v1')") is None
 assert not errors,errors
 print('PASS: insufficient evidence, empty and exact-article search, missing article, keyboard skip/focus, reduced motion, corrupt storage; no runtime errors')
 browser.close()
