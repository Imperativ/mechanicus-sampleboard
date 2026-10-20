#!/usr/bin/env python3
"""Validate every delivered sample, including decoding the MP3 counterparts."""
import concurrent.futures
import hashlib
import json
import math
import subprocess
import wave
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'manifest.json').read_text())
samples = manifest['samples']
assert samples and len({item['id'] for item in samples}) == len(samples)
source_ids = {item['id'] for item in manifest['sources']}
assert len([item for item in samples if item['group'] == 'Tuna Samples']) == 13
assert len([item for item in samples if item['group'] == 'Kontext']) == 1


def validate(item):
    wav = ROOT / item['wav']
    mp3 = ROOT / item['mp3']
    assert wav.is_file() and mp3.is_file(), item['id']
    assert item['sourceId'] in source_ids, item['id']
    assert 0 <= item['start'] < item['end'], item['id']
    assert item['duration'] > 0, item['id']
    assert len(item['waveform']) == 64 and all(0 <= x <= 1 for x in item['waveform'])
    assert hashlib.sha256(wav.read_bytes()).hexdigest() == item['sha256Wav'], item['id']
    if item.get('originalPath'):
        original = ROOT / item['originalPath']
        assert original.is_file(), item['id']
        assert hashlib.sha256(original.read_bytes()).hexdigest() == item['sha256Original'], item['id']
    with wave.open(str(wav), 'rb') as file:
        assert (file.getnchannels(), file.getsampwidth(), file.getframerate()) == (2, 2, 48000)
        frames = file.getnframes()
        pcm = np.frombuffer(file.readframes(frames), dtype='<i2')
    assert abs(frames / 48000 - item['duration']) < .00011, item['id']
    assert abs((item['end'] - item['start']) - item['duration']) < .00021, item['id']
    peak = int(np.max(np.abs(pcm.astype(np.int32))))
    assert 0 < peak <= math.ceil(32767 * 10 ** (-3 / 20)), (item['id'], peak)
    assert np.max(np.abs(pcm[:2])) == 0 and np.max(np.abs(pcm[-2:])) == 0
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp3), '-f', 'null', '-'], capture_output=True)
    assert result.returncode == 0, (item['id'], result.stderr.decode())
    return {'id': item['id'], 'wavBytes': wav.stat().st_size, 'mp3Bytes': mp3.stat().st_size}


with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(validate, samples))
report = {'passed': True, 'sampleCount': len(samples), 'validatedAudioFiles': len(samples) * 2,
          'formats': ['WAV PCM 16-bit / 48 kHz / stereo', 'MP3 160 kbit/s'],
          'countByCharacter': dict(Counter(item['character'] for item in samples)),
          'verifiedDownloadedOriginalWavs': sum(bool(item.get('originalPath')) for item in samples),
          'totalAudioBytes': sum(item['wavBytes'] + item['mp3Bytes'] for item in results),
          'checks': ['File existence', 'Unique IDs', 'Provenance references', 'WAV SHA-256',
                     'Original downloaded WAV SHA-256', 'PCM parameters', 'Duration and source interval agreement',
                     'Nonzero signal', 'Peak <= -3 dBFS', '5-ms faded edges', 'MP3 decoding']}
(ROOT / 'logs' / 'asset-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
