// Starts the FitFinder backend in the browser with Pyodide, then answers the React app's /api calls.
// Loaded before the app; build.sh inlines it into index.html.
(() => {
  const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/'
  const PACKAGES = ['pydantic', 'sqlalchemy', 'sqlite3', 'fastapi', 'starlette', 'anyio', 'sniffio',
    'typing-extensions', 'annotated-types', 'idna']
  const here = (p) => new URL(p, document.baseURI).href

  const overlay = document.createElement('div')
  overlay.id = 'ff-boot'
  overlay.innerHTML = '<div><strong>Starting FitFinder</strong><span id="ff-boot-step">Loading Python…</span>' +
    '<small>The real FitFinder backend runs inside this page. First load takes about 10–20 seconds.</small></div>'
  const style = document.createElement('style')
  style.textContent = `#ff-boot{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;
    background:#2F3BFF;font:16px/1.4 system-ui,sans-serif;color:#fff}
    #ff-boot div{display:flex;flex-direction:column;gap:6px;max-width:340px;padding:24px;text-align:center}
    #ff-boot strong{font-size:22px} #ff-boot small{color:rgba(255,255,255,.8)} #ff-boot.err{background:#1E1A4D}`
  const step = (t) => { const e = document.getElementById('ff-boot-step'); if (e) e.textContent = t }
  document.addEventListener('DOMContentLoaded', () => { document.head.append(style); document.body.append(overlay) })

  const loadScript = (src) => new Promise((ok, fail) => {
    const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = () => fail(new Error('Could not load ' + src))
    document.head.append(s)
  })

  window.__fitfinder = (async () => {
    await loadScript(PYODIDE + 'pyodide.js')
    const py = await globalThis.loadPyodide({ indexURL: PYODIDE })
    step('Loading FastAPI, Pydantic and SQLite…')
    await py.loadPackage(PACKAGES)
    step('Loading 1,722 products and their size charts…')
    const files = await (await fetch(here('py/fitfinder.json'))).json() // {path: text}
    for (const [path, text] of Object.entries(files)) {
      const full = '/home/pyodide/fitfinder/' + path
      py.FS.mkdirTree(full.slice(0, full.lastIndexOf('/')))
      py.FS.writeFile(full, text)
    }
    py.runPython(await (await fetch(here('py/bridge.txt'))).text())
    await py.globals.get('startup')()
    overlay.remove()
    return py
  })().catch((err) => {
    console.error(err)
    overlay.classList.add('err')
    step('FitFinder could not start: ' + err.message + '. Try reloading the page.')
    throw err
  })

  const realFetch = window.fetch.bind(window)
  window.fetch = async (input, init = {}) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href)
    const at = url.pathname.indexOf('/api/')
    if (at < 0) return realFetch(input, init)
    const py = await window.__fitfinder
    const result = await py.globals.get('handle')(init.method || 'GET', url.pathname.slice(at), url.search.slice(1), init.body || '')
    const [status, body] = result.toJs()
    result.destroy()
    return new Response(body, { status, headers: { 'content-type': 'application/json' } })
  }
})()
