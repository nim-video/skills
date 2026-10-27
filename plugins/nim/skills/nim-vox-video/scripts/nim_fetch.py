# /// script
# requires-python = ">=3.10"
# ///
"""Wait for Nim production generations and download them, without polling status in the chat.

usage: uv run nim_fetch.py promptId=out/path.jpg [promptId=out2.jpg ...] [--timeout 600]
Uses https://mcp.nim.video/mcp/generations/<promptId>/download?output=0 (the generate_image result's downloadUrl):
it answers with the image once the generation has finished. Retries every 8 s until every file is saved or
the timeout passes. Prints one line per file. Keep each result's mediaUrl from generate_image / status only if
a later edit needs it as a reference (fileInputs); the download URL is not a public reference URL."""
import sys, time, os, urllib.request
args = [a for a in sys.argv[1:] if '=' in a and not a.startswith('--')]
timeout = float(sys.argv[sys.argv.index('--timeout') + 1]) if '--timeout' in sys.argv else 600
todo = dict(a.split('=', 1) for a in args); t0 = time.time()
while todo and time.time() - t0 < timeout:
    for pid, out in list(todo.items()):
        try:
            r = urllib.request.urlopen(urllib.request.Request(f'https://mcp.nim.video/mcp/generations/{pid}/download?output=0', headers={'User-Agent': 'curl/8.4.0'}), timeout=60)
            ct = r.headers.get('Content-Type', '')
            if ct.startswith(('image/', 'video/', 'audio/')):
                os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True); open(out, 'wb').write(r.read())
                print(f'{pid} -> {out} ({time.time() - t0:.0f}s)', flush=True); todo.pop(pid)
        except Exception:
            pass
    if todo: time.sleep(8)
for pid, out in todo.items(): print(f'TIMEOUT {pid} -> {out}: check get_generation_status')
