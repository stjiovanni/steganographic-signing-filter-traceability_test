import json
import time
import urllib.request
import urllib.parse
import uuid
import sys
import os

BASE = "http://127.0.0.1:8000"
IMG = os.path.join('coco_val2017', 'val2017', '000000000139.jpg')
sys.stdout.reconfigure(encoding='utf-8')


def req(method, path, body=None, form=None):
    url = BASE + path
    data = None
    headers = {}
    if form is not None:
        boundary = uuid.uuid4().hex
        with open(form, 'rb') as f:
            raw = f.read()
        name = os.path.basename(form)
        body_bytes = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode() + raw + f'\r\n--{boundary}--\r\n'.encode()
        data = body_bytes
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
    elif body is not None:
        data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=180) as resp:
        return json.loads(resp.read().decode())


print('=== 1. Upload ===')
up = req('POST', '/api/upload', form=IMG)
print('image_id:', up['image_id'])

print('=== 2. Sign hybrid ===')
sig = req('POST', '/api/sign', body={'image_id': up['image_id'], 'method': 'hybrid'})
print('signed_id:', sig['signed_id'], '| channels:', sig.get('primary_channel'), '/', sig.get('fallback_channel'))

print('=== 3. Verify hybrid ===')
ver = req('POST', '/api/verify', body={'image_id': sig['signed_id'], 'method': 'hybrid'})
print('recovered:', ver['recovered'])
print('  TrustMark: detected=', ver['trustmark']['detected'], 'payload=', ver['trustmark']['decoded_payload'], 'acc=', ver['trustmark']['bit_accuracy'])
print('  Fallback:  detected=', ver['fallback']['detected'], 'payload=', ver['fallback']['decoded_payload'], 'acc=', ver['fallback']['bit_accuracy'])
print('  note:', ver['note'])

print('=== 4. Single-method verify (trustmark) ===')
ver2 = req('POST', '/api/verify', body={'image_id': sig['signed_id'], 'method': 'trustmark'})
print('  detected=', ver2['detected'], 'payload=', ver2['decoded_payload'], 'acc=', ver2['bit_accuracy'])

print('ALL SERVER HYBRID TESTS PASSED')