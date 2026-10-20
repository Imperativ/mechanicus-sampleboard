#!/usr/bin/env python3
"""Download only WAVs explicitly listed in the uploader's public Drive folders."""
import concurrent.futures
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = [
    ('Captrix', 'base-game', 'Hauptspiel', '1sJpgAsSXrLLo1sbhPm01QiOblu1YsG9B', 26),
    ('Faustinius', 'base-game', 'Hauptspiel', '1LPZREI6hxh8ZZcaOgfsqJfGU2xu9iOoh', 27),
    ('Khepra', 'base-game', 'Hauptspiel', '1RoRQRra12PzK3CNIaxTKWjAOdI4DofUp', 37),
    ('Reditus', 'base-game', 'Hauptspiel', '1zLY2m5YhS9QtoRnjfHyau6UgWaqHFS6H', 43),
    ('Rhezak', 'base-game', 'Hauptspiel', '1u9626UHeqPeve3VRlfNeifwLS7mPAYMd', 35),
    ('Rho', 'base-game', 'Hauptspiel', '1gcADAW4J2kqq6D_GQHtpjEzCiADc4jU5', 35),
    ('Scaevola', 'base-game', 'Hauptspiel', '1OxJPveQY2RY1ONCJWsj47Skh9JH7pmVH', 42),
    ('Tiresus', 'base-game', 'Hauptspiel', '1Ir5VeGeBooVdOf1e5RjPzByt78stCXqE', 22),
    ('Videx', 'base-game', 'Hauptspiel', '1RskgjDnO_bX3dRXToh_mo53p3XrZEPNZ', 40),
    ('Xerxetes', 'heretek', 'Heretek DLC', '1-JBE02G0bajSs-0nj_LSYkjytATyVSM_', 22),
    ('Epsilius Dammek-Yoth', 'heretek', 'Heretek DLC', '1eEzYRufcVOYYrs2N414To7tlPPN-80bY', 30),
]


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def listing(folder):
    character, source_id, group, folder_id, expected = folder
    html = get(f'https://drive.google.com/drive/folders/{folder_id}').decode('utf8')
    match = re.search(r"window\['_DRIVE_ivd'\] = '(.*?)';", html)
    if not match:
        raise RuntimeError(f'No public listing for {character}')
    payload = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m[1], 16)), match[1]).replace(r'\/', '/')
    entries = json.loads(payload)[0]
    records = []
    for entry in entries:
        if entry[3] != 'audio/wav':
            continue
        name = entry[2]
        if Path(name).name != name or not name.lower().endswith('.wav'):
            raise ValueError(f'Invalid listed filename: {name}')
        records.append({'fileId': entry[0], 'fileName': name, 'character': character,
                        'sourceId': source_id, 'group': group, 'folderId': folder_id,
                        'displayedAssetCount': expected,
                        'sourceUrl': f'https://drive.google.com/file/d/{entry[0]}/view',
                        'downloadUrl': f'https://drive.google.com/uc?export=download&id={entry[0]}'})
    print(character, len(records), 'listed WAV files', flush=True)
    return records


def download(record):
    folder = ROOT / 'sources' / 'originals' / re.sub(r'[^a-z0-9]+', '-', record['character'].lower()).strip('-')
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / record['fileName']
    if target.is_file():
        data = target.read_bytes()
    else:
        data = None
        error = None
        for attempt in range(3):
            try:
                data = get(record['downloadUrl'])
                if not (data.startswith(b'RIFF') and data[8:12] == b'WAVE'):
                    raise ValueError('Download is not a RIFF/WAVE audio file')
                break
            except Exception as exc:
                error = exc
                if attempt < 2:
                    time.sleep(1 + attempt * 2)
        if data is None or not (data.startswith(b'RIFF') and data[8:12] == b'WAVE'):
            raise RuntimeError(f"{record['character']}/{record['fileName']}: {error}")
        target.write_bytes(data)
    result = dict(record)
    result['localPath'] = target.relative_to(ROOT).as_posix()
    result['sha256Original'] = hashlib.sha256(data).hexdigest()
    result['bytes'] = len(data)
    return result


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = [r for group in pool.map(listing, FOLDERS) for r in group]
    # Write the listing before downloads so an interrupted run is transparent and resumable.
    (ROOT / 'sources' / 'original-listing.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        completed = list(pool.map(download, records))
    (ROOT / 'sources' / 'original-downloads.json').write_text(json.dumps(completed, ensure_ascii=False, indent=2) + '\n')
    print('Downloaded and RIFF/WAVE-validated:', len(completed), 'files', sum(r['bytes'] for r in completed), 'bytes', flush=True)
