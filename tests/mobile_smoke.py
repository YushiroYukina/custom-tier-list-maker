"""Headless Chromium regression checks. Run with a Python Playwright installation."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)
results = []

def check(label, condition):
    assert condition, label
    results.append(label)
    print('PASS '+label,flush=True)

def count(page, selector):
    return page.locator(selector).count()

def touch(cdp, kind, x=0, y=0):
    cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [] if kind == 'touchEnd' else [{'x': x, 'y': y}]})

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True, device_scale_factor=1)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())
    page.goto((ROOT/'index.html').as_uri())
    page.wait_for_selector('.item-card')
    check('initial demo cards', count(page,'.item-card') == 8)
    for width, height in [(320,740),(390,844),(430,932),(768,1024),(844,390)]:
        page.set_viewport_size({'width':width,'height':height})
        check(f'no horizontal overflow {width}x{height}', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check(f'toolbar labels visible {width}', page.locator('#btnAddItem .btn-text').is_visible())
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#fileImport').set_input_files(str(ROOT/'examples/素材池示例.json'))
    page.wait_for_function("document.querySelectorAll('#poolTrack .item-card').length === 4")
    check('legacy JSON imports', count(page,'.tier-track .item-card') == 0)
    card = page.locator('#poolTrack .thumb').first
    card.tap()
    page.locator('[data-move="0"]').click()
    check('tap pool card to first tier', count(page,'.tier-track .item-card') == 1 and count(page,'#poolTrack .item-card') == 3)
    page.locator('.tier-track .thumb').first.tap()
    page.locator('[data-move="1"]').click()
    check('tap cross-tier move', count(page,'.tier-track[data-tierid="tr2"] .item-card') == 1)
    page.locator('#poolTrack .thumb').first.tap()
    page.locator('[data-move="1"]').click()
    ids = page.locator('.tier-track[data-tierid="tr2"] .item-card').evaluate_all('(els)=>els.map(e=>e.dataset.itemid)')
    page.locator('.tier-track[data-tierid="tr2"] .thumb').nth(1).tap()
    page.locator('[data-step="-1"]').click()
    check('tap reorder within tier', page.locator('.tier-track[data-tierid="tr2"] .item-card').evaluate_all('(els)=>els.map(e=>e.dataset.itemid)') == ids[::-1])
    # Existing autosave is debounced by 260 ms and writes IndexedDB asynchronously.
    page.wait_for_timeout(700)
    page.reload()
    page.wait_for_selector('.item-card')
    check('reload retains order', page.locator('.tier-track[data-tierid="tr2"] .item-card').evaluate_all('(els)=>els.map(e=>e.dataset.itemid)') == ids[::-1])
    # Real browser touch input on a cover must scroll without starting a drag.
    cdp = context.new_cdp_session(page)
    page.locator('.tier-track[data-tierid="tr2"] .thumb').first.scroll_into_view_if_needed()
    r = page.locator('.tier-track[data-tierid="tr2"] .thumb').first.bounding_box()
    x, y = r['x']+r['width']/2, r['y']+r['height']*.8
    before = page.evaluate('scrollY')
    touch(cdp,'touchStart',x,y)
    for step in range(1,9):
        touch(cdp,'touchMove',x,y-step*12)
        page.wait_for_timeout(20)
    touch(cdp,'touchEnd')
    page.wait_for_timeout(180)
    check('swipe cover scrolls page', page.evaluate('scrollY') > before+20)
    check('swipe does not open menu or leave ghost', count(page,'.modal-mask, #dragGhost') == 0)
    # Handle drag into the preceding empty tier.
    page.wait_for_timeout(700)
    page.locator('.tier-track[data-tierid="tr2"] .grab-handle').first.scroll_into_view_if_needed()
    page.evaluate('scrollBy(0,-220)')
    handle = page.locator('.tier-track[data-tierid="tr2"] .grab-handle').first.bounding_box()
    target = page.locator('.tier-track[data-tierid="tr1"]').bounding_box()
    x,y=handle['x']+22,handle['y']+22
    touch(cdp,'touchStart',x,y)
    check('handle starts touch drag', count(page,'#dragGhost') == 1)
    tx,ty=target['x']+target['width']/2,target['y']+target['height']/2
    touch(cdp,'touchMove',tx,ty)
    touch(cdp,'touchEnd')
    check('touch drop transfers item', count(page,'.tier-track[data-tierid="tr1"] .item-card') == 1)
    check('drag cleans up ghost', count(page,'#dragGhost') == 0)
    page.evaluate('scrollTo(0,0)')
    handle = page.locator('.tier-track[data-tierid="tr1"] .grab-handle').first.bounding_box()
    touch(cdp,'touchStart',handle['x']+22,handle['y']+22)
    touch(cdp,'touchMove',200,835)
    before=page.evaluate('scrollY')
    page.wait_for_timeout(250)
    check('stationary edge drag auto-scrolls', page.evaluate('scrollY') > before+20)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]})
    check('touch cancel cleans up', count(page,'#dragGhost') == 0)
    page.set_viewport_size({'width':320,'height':740})
    page.locator('[data-act="tiercolor"]').first.click()
    check('palette fits narrow screen',page.locator('.palette').evaluate('(el)=>{let r=el.getBoundingClientRect();return r.left>=0 && r.right<=innerWidth && r.bottom<=innerHeight}'))
    page.locator('.palette button').first.click()
    page.set_viewport_size({'width':390,'height':844})
    # PNG preview is decoded, then download bytes are checked.
    page.locator('#btnExportImg').click()
    preview = page.locator('.export-preview')
    preview.wait_for()
    page.wait_for_function("document.querySelector('.export-preview').naturalWidth > 0")
    check('mobile PNG preview', preview.evaluate('(img)=>img.naturalWidth >= 760'))
    with page.expect_download() as dl:
        page.locator('#saveExport').click()
    png = Path(dl.value.path()).read_bytes()
    check('PNG download signature', png[:8] == b'\x89PNG\r\n\x1a\n')
    page.locator('[data-close]').click()
    with page.expect_download() as dl:
        page.locator('#btnExportJson').click()
    data = json.loads(Path(dl.value.path()).read_text(encoding='utf-8'))
    check('JSON export compatible', data['app']=='hanla-ranking' and data['version']==1 and len(data['data']['items'])==4)
    # Upload via the existing image file input.
    page.locator('#btnAddItem').click()
    page.locator('#fileAdd').set_input_files(str(ROOT/'assets/screenshot.png'))
    page.wait_for_function("document.querySelectorAll('.item-card').length === 5")
    check('local image upload', count(page,'.item-card') == 5)
    page.evaluate('scrollTo(0,0)')
    page.screenshot(path=str(OUT/'mobile-390.png'),full_page=True)
    check('no JavaScript errors', not errors)
    context.close()
    desktop = browser.new_context(viewport={'width':1440,'height':1000})
    page = desktop.new_page()
    page.goto((ROOT/'index.html').as_uri())
    page.wait_for_selector('.item-card')
    card = page.locator('.item-card').first
    item_id=card.get_attribute('data-itemid')
    card.scroll_into_view_if_needed()
    track=page.locator('.tier-track').last
    target=track.get_attribute('data-tierid')
    r=card.locator('.thumb').bounding_box(); t=track.bounding_box()
    page.mouse.move(r['x']+60,r['y']+55); page.mouse.down()
    page.mouse.move(t['x']+30,t['y']+40,steps=12); page.mouse.up()
    check('desktop mouse drag', count(page,f'.tier-track[data-tierid="{target}"] [data-itemid="{item_id}"]')==1)
    with page.expect_download() as dl:
        page.locator('#btnExportImg').click()
    check('desktop PNG download', dl.value.suggested_filename.endswith('.png'))
    page.screenshot(path=str(OUT/'desktop-1440.png'),full_page=True)
    desktop.close(); browser.close()

(OUT/'mobile-results.json').write_text(json.dumps({'passed':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(results),'checks':results},ensure_ascii=False))
