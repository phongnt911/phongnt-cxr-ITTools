"""Local UI replay. Only cached read responses; no live system mutation bridge."""
import json
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import sys
sys.path.insert(0, str(Path(__file__).parent))
from qa_windows import CASES, ROOT, SCRATCH
fixtures = {}
for case, (method, _) in CASES.items():
    path = SCRATCH / (case + '.json')
    if path.exists():
        fixtures[method] = json.loads(path.read_text(encoding='utf-8'))
fixtures['get_logs'] = []
fixtures['get_fluent_cleaner_info'] = {'success': True, 'version': '26.09.01', 'installed': True}
bridge = '''<script>
window.pywebview = {api: new Proxy({}, {get: (_, method) => (...args) => {
  const node = document.createElement('span'); node.dataset.method = method;
  node.textContent = method; node.hidden = true; document.body.append(node);
  return fetch('/qa-fixture/' + encodeURIComponent(method)).then(r=>r.json());
}})};
window.addEventListener('DOMContentLoaded', () => window.dispatchEvent(new Event('pywebviewready')));
</script>'''
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT / 'ITTools/web'),**kwargs)
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path.startswith('/qa-fixture/'):
            method = self.path.split('/')[-1]
            data = fixtures.get(method, {'success': False, 'message': 'QA: live mutation/unrecorded method blocked'})
            payload = json.dumps(data,ensure_ascii=False).encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(payload)
        elif self.path in ('/','/index.html'):
            html = (ROOT / 'ITTools/web/index.html').read_text(encoding='utf-8')
            html = html.replace('<script src="app.js', bridge + '<script src="app.js')
            self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(html.encode('utf-8'))
        else: super().do_GET()
print('QA replay http://127.0.0.1:8765',flush=True)
ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
