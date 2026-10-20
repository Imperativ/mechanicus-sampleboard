#!/usr/bin/env python3
"""Build the offline board from real recordings; never synthesize replacement audio."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import math
import re
import subprocess
import wave
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000
SOURCES = [
    {'id': 'base-game', 'title': 'Mechanicus – einzelne WAV-Dateien',
     'url': 'https://drive.google.com/drive/folders/17r7exNZvj6dOaDQH4PQc9X5miL64sFPM',
     'description': '300 einzelne WAV-Dateien aus dem vom Video-Uploader emu öffentlich verlinkten Archiv.'},
    {'id': 'heretek', 'title': 'Heretek DLC – einzelne WAV-Dateien',
     'url': 'https://drive.google.com/drive/folders/1De47fXbGug7eP_7jlmcgnfUSPs0aj2JG',
     'description': '52 einzelne WAV-Dateien: Xerxetes und Epsilius Dammek-Yoth.'},
    {'id': 'base-game-video', 'title': 'Hauptspiel – Video-Referenz',
     'url': 'https://www.youtube.com/watch?v=3pvnxOn5LUE',
     'description': 'Charakternamen und angezeigte Asset-Zahlen visuell geprüft; vollständige Audiospur erhalten.'},
    {'id': 'heretek-video', 'title': 'Heretek – Video-Referenz',
     'url': 'https://www.youtube.com/watch?v=n-cZkW30IHI',
     'description': 'Charakternamen visuell geprüft; vollständige Audiospur erhalten.'},
    {'id': 'tuna', 'title': 'Binharic noise 1–13 / RoboDestiny',
     'url': 'https://tuna.voicemod.net/sound/54837fc4-a5a0-4aff-8fac-20b1979465df',
     'description': '13 öffentlich abspielbare Uploads desselben Anbieters; Charakter unbekannt.'},
    {'id': 'opening', 'title': 'Mechanicus – Opening Scene',
     'url': 'https://www.youtube.com/watch?v=WyK7lX4sk0c',
     'description': 'Komplette Kontextaufnahme; enthält Begleitton und ist kein isoliertes Sprachsample.'},
]


def run(args: list[str]) -> bytes:
    return subprocess.run(args, check=True, capture_output=True).stdout


def decode(path: Path) -> np.ndarray:
    raw = run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
               '-f', 'f32le', '-ac', '2', '-ar', str(RATE), '-'])
    audio = np.frombuffer(raw, dtype='<f4').reshape(-1, 2)
    if len(audio) == 0 or not np.isfinite(audio).all():
        raise ValueError(f'Invalid decoded audio: {path}')
    return audio


def slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def trim_edges(audio: np.ndarray, threshold_db: float = -42) -> tuple[np.ndarray, int, int]:
    # RMS windows keep intra-phrase binharic pauses intact; only edges are trimmed.
    block = 480
    count = len(audio) // block
    if not count:
        return audio.copy(), 0, len(audio)
    energy = np.sqrt(np.mean(audio[:count * block].reshape(count, block, 2) ** 2, axis=(1, 2)))
    active = np.flatnonzero(energy > 10 ** (threshold_db / 20))
    if not len(active):
        return audio.copy(), 0, len(audio)
    padding = int(.025 * RATE)
    start = max(0, int(active[0]) * block - padding)
    end = min(len(audio), (int(active[-1]) + 1) * block + padding)
    return audio[start:end].copy(), start, end


def encode_clip(audio: np.ndarray, record: dict, trim: bool = True) -> dict:
    if trim:
        audio, left, right = trim_edges(audio)
        record['start'] = round(record.get('start', 0) + left / RATE, 4)
        record['end'] = round(record['start'] + len(audio) / RATE, 4)
    else:
        audio = audio.copy()
    peak = float(np.max(np.abs(audio)))
    if peak <= 0:
        raise ValueError(f'Silent sample: {record["id"]}')
    # Match peak headroom, but never amplify by more than 6 dB.
    gain = min(10 ** (-3 / 20) / peak, 10 ** (6 / 20))
    audio *= gain
    fade = min(int(.005 * RATE), len(audio) // 2)
    if fade:
        audio[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)[:, None]
        audio[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
    pcm = np.rint(np.clip(audio, -1, 1) * 32767).astype('<i2')
    folder = ROOT / 'samples' / slug(record['group']) / slug(record['character'])
    folder.mkdir(parents=True, exist_ok=True)
    wav = folder / (record['id'] + '.wav')
    mp3 = wav.with_suffix('.mp3')
    with wave.open(str(wav), 'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    run(['ffmpeg', '-v', 'error', '-i', str(wav), '-c:a', 'libmp3lame',
         '-b:a', '160k', '-y', str(mp3)])
    waveform = []
    for section in np.array_split(np.max(np.abs(audio), axis=1), 64):
        waveform.append(round(float(np.max(section)) if len(section) else 0, 4))
    record.update({
        'duration': round(len(audio) / RATE, 4),
        'wav': wav.relative_to(ROOT).as_posix(),
        'mp3': mp3.relative_to(ROOT).as_posix(),
        'waveform': waveform,
        'peakDbfs': round(20 * math.log10(float(np.max(np.abs(pcm.astype(np.float32) / 32768)))), 3),
        'gainDb': round(20 * math.log10(gain), 3),
        'sha256Wav': hashlib.sha256(wav.read_bytes()).hexdigest(),
    })
    return record


def build() -> None:
    output = []
    report = []
    originals = json.loads((ROOT / 'sources' / 'original-downloads.json').read_text())
    for character in dict.fromkeys(item['character'] for item in originals):
        files = [item for item in originals if item['character'] == character]
        def convert(item):
            audio = decode(ROOT / item['localPath'])
            stem = Path(item['fileName']).stem
            number = int(re.search(r'(\d+)$', stem)[1])
            category = ''
            if character == 'Videx':
                category = '20 Zeichen · ' if '20lettres' in stem else 'Über 28 Zeichen · '
            rec = {'id': f'{slug(character)}-{slug(stem)}',
                   'title': f'{character} · {category}{number:02}',
                   'character': character, 'group': item['group'], 'sourceId': item['sourceId'],
                   'sourceUrl': item['sourceUrl'], 'sourceFile': item['fileName'],
                   'originalPath': item['localPath'], 'sha256Original': item['sha256Original'],
                   'start': 0, 'end': len(audio) / RATE,
                   'verification': 'Einzeln heruntergeladene WAV-Datei aus dem vom Uploader verlinkten Archiv; native Spielasset-Authentizität nicht unabhängig bestätigt.'}
            return encode_clip(audio, rec)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            output.extend(pool.map(convert, files))
        report.append({'character': character, 'displayedAssetCount': files[0]['displayedAssetCount'],
                       'downloadedFileCount': len(files),
                       'difference': files[0]['displayedAssetCount'] - len(files),
                       'note': 'Ein Board-Clip pro heruntergeladener WAV-Datei; nur Randstille gekürzt, keine interne Segmentierung.'})
        print(character, len(files), 'individual WAV files processed', flush=True)
    candidates = json.loads((ROOT / 'sources' / 'tuna-candidates.json').read_text())
    for item in sorted(candidates, key=lambda rec: int(rec['name'].rsplit(' ', 1)[1])):
        n = int(item['name'].rsplit(' ', 1)[1])
        audio = decode(ROOT / 'sources' / f'tuna-{n:02}.mp3')
        rec = {'id': f'binharic-{n:02}', 'title': f'Binharic Noise {n:02}',
               'character': 'Binharic · nicht zugeordnet', 'group': 'Tuna Samples',
               'sourceId': 'tuna', 'sourceUrl': item['source_url'],
               'author': item['author'], 'start': 0, 'end': len(audio) / RATE,
               'verification': 'Öffentlicher Upload von RoboDestiny; Charakter und native Spielasset-Herkunft ungeprüft.'}
        output.append(encode_clip(audio, rec))
    context = decode(ROOT / 'sources' / 'opening-context.webm')
    output.append(encode_clip(context, {'id': 'opening-context', 'title': 'Opening Scene · kompletter Kontext',
                   'character': 'Kontextaufnahme', 'group': 'Kontext', 'sourceId': 'opening',
                   'start': 0, 'end': len(context) / RATE,
                   'verification': 'Vollständige Audiospur inklusive Begleitton; keine freigestellte Stimme.'}, trim=False))
    processing = {'format': 'WAV PCM 16-bit, 48 kHz, stereo; MP3 160 kbit/s',
                  'peakCeilingDbfs': -3, 'maxBoostDb': 6, 'fadeMilliseconds': 5,
                  'edgePaddingMilliseconds': 25,
                  'segmentation': 'Ein Clip pro öffentlich verlinkter WAV-Datei. Nur Randstille gekürzt; keine internen Schnitte.',
                  'notes': 'Keine Synthese oder Sprachrekonstruktion. 7 gegenüber den Video-Zahlen fehlende WAV-Dateien dokumentiert. Native Asset-Authentizität nicht unabhängig bestätigt.',
                  'clipCountByCharacter': dict(Counter(item['character'] for item in output)),
                  'sourceFileReport': report,
                  'missingFiles': {'Captrix': [15, 20], 'Khepra': [23, 33], 'Scaevola': [7, 16, 37]}}
    manifest = {'title': 'NOOSPHERE // Mechanicus Sampleboard', 'sources': SOURCES,
                'samples': output, 'processing': processing}
    data = json.dumps(manifest, ensure_ascii=False, indent=2)
    (ROOT / 'manifest.json').write_text(data + '\n')
    (ROOT / 'samples.js').write_text('window.SAMPLEBOARD = ' + data + ';\n')
    (ROOT / 'logs' / 'source-file-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Total:', len(output), 'real-audio clips', flush=True)


if __name__ == '__main__':
    build()
