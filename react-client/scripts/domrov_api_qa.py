"""Exercise fetchApiClient using browser-intercepted API responses, not a live backend.
Start Vite with VITE_USE_MOCK=false on port 5174 before running.
"""
import json, os
from playwright.sync_api import sync_playwright, expect
BASE=os.environ.get('DOMROV_API_TEST_URL','http://127.0.0.1:5174')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE','/home/panha/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome'),headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':360,'height':900})
 calls=[]; fail=True
 source=dict(documentId='contract-document',articleNumber='8',title='ឯកសារសាកល្បង API '+('ពាក្យវែង'*40),documentType='Law',documentNumber=None,category=None,issuedDate=None,chapterNumber=None,chapterTitle=None,sectionNumber=None,sectionTitle=None,pdfUrl='https://example.org/test.pdf',sequence=1,recordType='article',reviewRequired=True,reviewReason='ត្រូវពិនិត្យ',excerpt='អត្ថបទសាកល្បង',articleText='អត្ថបទសាកល្បង',score=.9)
 def api(route):
  request=route.request;calls.append((request.method,request.url,request.post_data_json if request.method=='POST' else None))
  if fail: route.abort('failed');return
  if '/api/chat' in request.url:
   msg=request.post_data_json['message']
   route.fulfill(json={'answer':'ចម្លើយសាកល្បង' if msg!='unsafe' else 'UNSUPPORTED_ANSWER','sources':[source] if msg!='unsafe' else [],'hasSufficientEvidence':True,'insufficientEvidenceMessage':None})
  elif '/api/search' in request.url:
   body=request.post_data_json
   route.fulfill(json={'query':body['query'],'mode':body['mode'],'items':[source],'pagination':{'page':1,'pageSize':10,'total':1,'totalPages':1},'hasSufficientEvidence':True})
  elif '/api/articles/' in request.url:
   route.fulfill(json={'article':source,'navigation':{'previousArticleNumber':None,'nextArticleNumber':None}})
 page.route('**/api/**',api)
 page.goto(BASE+'/chat');expect(page.get_by_text('ភ្ជាប់ API · Live')).to_be_visible()
 page.get_by_label('សំណួររបស់អ្នក').fill('contract question');page.get_by_role('button',name='ផ្ញើ').click()
 expect(page.get_by_text('ការស្នើសុំបរាជ័យ។ សូមព្យាយាមម្តងទៀត។')).to_be_visible()
 fail=False;page.get_by_role('button',name='ព្យាយាមម្តងទៀត').click();expect(page.get_by_text('ចម្លើយសាកល្បង',exact=True)).to_be_visible()
 chat=[c for c in calls if '/api/chat' in c[1]]
 assert chat[0][0]=='POST' and chat[0][2]=={'message':'contract question','conversation':[]}
 assert chat[1][2]['conversation']==[{'role':'user','content':'contract question'}]
 page.get_by_role('link',name='អានអត្ថបទ').click();expect(page.get_by_text('អត្ថបទដើម',exact=True)).to_be_visible();assert calls[-1][1].endswith('/api/articles/contract-document/8')
 page.goto(BASE+'/chat');page.get_by_label('សំណួររបស់អ្នក').fill('unsafe');page.get_by_role('button',name='ផ្ញើ').click();expect(page.get_by_text('មិនអាចផ្តល់ចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់')).to_be_visible();assert 'UNSUPPORTED_ANSWER' not in page.locator('body').inner_text()
 fail=True;page.goto(BASE+'/search?q=8&mode=exact_article');expect(page.get_by_text('មិនអាចស្វែងរកបានទេ។ សូមព្យាយាមម្តងទៀត។')).to_be_visible();fail=False;page.get_by_role('button',name='ព្យាយាមម្តងទៀត').click();expect(page.get_by_role('link',name='អានអត្ថបទ')).to_be_visible()
 request=[c[2] for c in calls if '/api/search' in c[1]][-1];assert request['mode']=='exact_article' and request['filters']['articleNumber']=='8'
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 fail=True;page.goto(BASE+'/articles/contract-document/8');expect(page.get_by_text('មិនអាចទាញយកអត្ថបទបានទេ។ សូមព្យាយាមម្តងទៀត។')).to_be_visible();fail=False;page.get_by_role('button',name='ព្យាយាមម្តងទៀត').click();expect(page.get_by_text('អត្ថបទដើម',exact=True)).to_be_visible()
 # localStorage denied: never claim successful persistence.
 page.add_init_script("Storage.prototype.setItem=()=>{throw new Error('blocked')}")
 page.goto(BASE+'/procedures/driving-licence');page.get_by_role('button',name='រក្សាទុកបញ្ជី',exact=True).click();expect(page.get_by_text('មិនអាចរក្សាទុក ឬលុបទិន្នន័យបានទេ។',exact=False)).to_be_visible()
 print('PASS: fetch client POST chat/search payloads and article GET; chat/search/article failure and retry; unsupported answer suppressed; denied storage surfaced')
 browser.close()
