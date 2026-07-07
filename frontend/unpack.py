import json
import base64
import gzip
import os
import re

def unpack():
    with open('AI Clone Setup (standalone).html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Find the manifest JSON
    match = re.search(r'<script type="__bundler/manifest">\s*(.*?)\s*</script>', html, re.DOTALL)
    if not match:
        print("Could not find manifest!")
        return

    manifest = json.loads(match.group(1))
    
    os.makedirs('unpacked_ui', exist_ok=True)
    
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry['data'])
        if entry.get('compressed'):
            data = gzip.decompress(data)
            
        # Determine extension
        ext = '.txt'
        mime = entry.get('mime', '')
        if 'javascript' in mime or 'babel' in mime: ext = '.jsx'
        elif 'css' in mime: ext = '.css'
        elif 'json' in mime: ext = '.json'
            
        filename = f"unpacked_ui/file_{uuid[:8]}{ext}"
        with open(filename, 'wb') as f:
            f.write(data)
        print(f"Extracted {filename}")

if __name__ == '__main__':
    unpack()
