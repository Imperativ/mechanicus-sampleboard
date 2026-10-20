# NOOSPHERE // Mechanicus Sampleboard

Fertig aufbereitetes Offline-Sampleboard mit echten heruntergeladenen Aufnahmen, ohne synthetische Ersatzsounds. `index.html` ist der Einstieg; kein Webserver oder Internetzugang für die Wiedergabe erforderlich.

## Inhalt des endgültigen Boards

**366 Clips**, jeweils als WAV und MP3:

- **352 einzeln heruntergeladene WAV-Dateien** aus dem vom Video-Uploader emu öffentlich verlinkten Archiv.
- **13 Binharic-Uploads** von RoboDestiny / Voicemod Tuna; keinem Charakter sicher zugeordnet.
- **1 vollständige Opening-Scene-Audiospur** als Kontextaufnahme, einschließlich Begleitton, nicht als freigestellte Charakterstimme.

| Charakter | Einzeldateien |
|---|---:|
| Captrix | 24 |
| Faustinius | 27 |
| Khepra | 35 |
| Reditus | 43 |
| Rhezak | 35 |
| Rho | 35 |
| Scaevola | 39 |
| Tiresus | 22 |
| Videx | 40 |
| Xerxetes | 22 |
| Epsilius Dammek-Yoth | 30 |

Namensnormalisierung: Im Uploader-Text bzw. Dateinamen steht teils `Faustinus`, im Videobild `Faustinius`; Dateinamen für Khepra enthalten `KEPRAH`. Originaldateinamen bleiben im Manifest erhalten. Die Videx-Kategorien sind aus den Dateinamen übernommen, nicht aus einer behaupteten Übersetzung des Binharic.

### Ehrlich dokumentierte Lücken

Gegenüber den im Video angegebenen Asset-Zahlen fehlen im verlinkten WAV-Archiv sieben nummerierte Dateien:

- Captrix: **15, 20**
- Khepra: **23, 33**
- Scaevola: **7, 16, 37**

Diese Dateien wurden nicht erfunden oder durch Synthese ersetzt. Die vollständigen Video-Audiospuren sind zusätzlich erhalten. Die zunächst automatisch daraus erzeugten **369 Clips** stehen mit einem eigenen Board in `video-cuts/index.html` zur Verfügung. Dessen Pausenschnitte sind nicht mit nativen Asset-Grenzen gleichzusetzen und nicht einzeln gehörgeprüft; es handelt sich um eine ergänzende, separate Schnittfassung, nicht um weitere 369 einzigartige Originalassets.

## Funktionen

Suche; Charakter-, Gruppen- und Quellenfilter; Waveform-Vorschau; Abspielen/Stoppen; Loop je Clip; optional gleichzeitige Wiedergabe; Master-Lautstärke zunächst **35 %**; WAV-/MP3-Einzeldownloads; Quellenlink pro Sample.

Tasten **1–9** spielen die ersten neun aktuell sichtbaren Pads; **Escape** stoppt alles. Eingaben in Suchfeldern lösen keine Sounds aus. Kein Autoplay.

## Verarbeitung

- Ein Board-Clip pro heruntergeladener Einzel-WAV-Datei; **keine internen Pausenschnitte** im endgültigen Board.
- Nur Randstille gekürzt: 10-ms-RMS-Fenster, Schwelle −42 dBFS, 25 ms Randreserve.
- Spitzenpegel höchstens −3 dBFS; Anhebung maximal 6 dB; 5 ms Ein-/Ausblendung.
- WAV: PCM 16 Bit, 48 kHz, Stereo. MP3: 160 kbit/s.
- Keine Rauschrekonstruktion, keine erfundenen Frequenzprofile, keine synthetischen Fallbacks.
- Die unveränderten heruntergeladenen Einzel-WAVs liegen in `sources/originals/`; deren SHA-256 sowie die verarbeiteten WAV-Prüfsummen stehen im Manifest. Die Board-Dateien sind wegen der Aufbereitung nicht bitgleich mit den heruntergeladenen Dateien.
- `start` / `end` im endgültigen Manifest beziehen sich bei Einzel-WAVs auf die jeweilige Quelldatei, nicht auf eine YouTube-Zeitmarke.

Die vollständigen drei heruntergeladenen Video-Audiospuren liegen außerdem als `sources/*-audio.flac` vor. FLAC erhält das dekodierte Signal verlustfrei; es macht die ursprüngliche AAC-/Opus-Quelle nicht rückwirkend verlustfrei. Quellcontainer, Metadaten und Kapitelbilder wurden aufbewahrt.

## Herkunft

- Hauptspiel-Video: https://www.youtube.com/watch?v=3pvnxOn5LUE
- Heretek-Video: https://www.youtube.com/watch?v=n-cZkW30IHI
- Öffentlich vom Uploader verlinktes WAV-Archiv: https://drive.google.com/drive/folders/1N6W3JciCkNYvcqn_kwvdZYn-r553niD-
- Tuna-Ausgangspunkt: https://tuna.voicemod.net/sound/54837fc4-a5a0-4aff-8fac-20b1979465df
- Opening Scene: https://www.youtube.com/watch?v=WyK7lX4sk0c

Die einzelnen Datei-/Sample-URLs sind in `manifest.json` dokumentiert. Charakterbilder an Kapitelgrenzen wurden visuell ausgewertet. Die Authentizität als unveränderte native Spielassets wurde nicht unabhängig bestätigt; keine Behauptung einer vollständigen Hörprüfung aller Aufnahmen.

**Rechte:** Spiel- und Aufnahme-Rechte bleiben bei den jeweiligen Rechteinhabern bzw. Uploadenden. Öffentliche Verfügbarkeit ist keine Weiterverbreitungslizenz. Das Paket enthält keine behauptete Lizenzfreigabe für Veröffentlichung oder kommerzielle Nutzung.

## Verzeichnis und Prüfungen

- `index.html`, `app.js`, `style.css`, `samples.js`: fertiges Offline-Board.
- `samples/`: verarbeitete WAV-/MP3-Dateien nach Gruppe und Charakter.
- `manifest.json`: Quellen, Originalnamen, Dauer, Rand-Schnittpositionen, Pegel und echte Prüfsummen.
- `sources/`: unveränderte Downloads, extrahierte Gesamtspuren, Metadaten und Kapitelbilder.
- `video-cuts/`: erhaltene automatische Videoschnitt-Fassung.
- `logs/asset-validation.json`: Prüfung sämtlicher **732** Board-Audiodateien, inklusive MP3-Dekodierung und der **352** heruntergeladenen Original-WAV-Prüfsummen.
- `logs/browser-validation.json`: tatsächliche Chromium-Tests über `file://`, einschließlich WAV-/MP3-Wiedergabe, Loops, Filter, Tastatur, Fehlerfälle und mobilem Layout.
- `logs/sampleboard-desktop.png`, `logs/sampleboard-mobile.png`: Screenshots des geprüften Boards.

Die portable ZIP enthält das endgültige Board samt allen 366 WAV-/MP3-Paaren, Manifest, diesem Dokument und Prüfberichten. Die umfangreichen Rohquellen, das separate Video-Schnittboard und lokale Entwicklungswerkzeuge verbleiben im Projektordner und werden nicht redundant in die portable ZIP aufgenommen.


## Lokale Ablage und Entwicklung

Der vollständige Entwicklungsbestand liegt seit dem 20. Oktober 2026 unter
`/home/imp/Pi-projekte.lokal/mechanicus-sampleboard`. Zum Öffnen genügt
`index.html`; die Schreibtischverknüpfung verweist ebenfalls auf diesen Ort.

Das Repository enthält das fertige Board, WAV-/MP3-Dateien, Rohquellen,
Videoschnitt-Fassung, Werkzeuge, Tests und Prüfberichte. Das bereits vorhandene
portable `Mechanicus-Sampleboard.zip`, heruntergeladene `tools/yt-dlp`, installierte
`node_modules` und temporäre `.log`-Dateien bleiben lokal und sind durch
`.gitignore` ausgeschlossen. Eine frische Kopie von GitHub funktioniert für die
Wiedergabe ohne diese Dateien.

Für die vorhandenen Prüfungen werden Python mit NumPy, FFmpeg und Chromium
benötigt. Die Browser-Testabhängigkeit wird bei Bedarf so installiert:

```bash
npm ci --prefix tools/browser-check
python3 tests/test_assets.py
node tests/browser-test.cjs
```

Der ursprüngliche Entwicklungsverlauf wurde im Pi Coding Agent gespeichert:
Session `01a11347-de28-717d-a86d-6b25858d694d`, 7. Oktober 2026 (Europe/Berlin).
Die Umsetzung erfolgte nach dem Modellwechsel mit `openai-codex / gpt-6.1-sol`.
