# chant_sim — simulated Exodus 40 recordings (issue #7)

Most of Exodus 40 was never captured from bible.ort.org. This directory holds the tooling used to
(a) recover what the Wayback Machine kept [ and detritus from the scrollscraper.adatshalom.net web server ] and (b) *simulate* the remaining verses in the same Hazzan's
voice, by splicing and re-pitching his recordings of other verses. The simulations are placeholders
until a skilled chanter records the real thing (PR 2 in the issue's plan).

## Audio layout (`misc_mp3s/t2/40/`)

| dir | contents |
|---|---|
| `from_wayback/` | genuine ORT recordings recovered from web.archive.org: 40:1–4, 6, 15–17, 27–29, 33–36 (`fetch_wayback.sh`) |
| `from_scrollscraper/` | genuine ORT recordings from an earlier ScrollScraper capture: 40:31, 32 |
| `replacements/` | simulated verses + `PROVENANCE.txt` (where every word came from) |

All MP3s use the `local_ort_mp3s` format: 16 kHz, stereo, 48 kbps.

Notes on the hand-collected files (`/tmp/miscExodus40`, from the web server, checked with `misc_check.py`):
40:33 and 40:34 [ from web server ] are the same takes as the Wayback copies (≈1.1 s extra leading silence).
40:38 there is *not* the ORT Hazzan (voice-profile outlier, 24 kHz mono, ~40 s), so it isn't used.

## How the simulation works

1. **Text** — `data/entire_torah.json` (Tanach with ta'amim). `heb.py` romanizes pointed Hebrew for the aligner
   and extracts accent (trope) signatures.
2. **Alignment** — `align.py` force-aligns every source verse to its words with torchaudio's MMS_FA
   (multilingual CTC aligner; ~1.2 GB model downloaded on first use). Results are cached in
   `~/.cache/scrollscraper_align/`.
3. **Unit selection** — `synth3.py` covers the target verse with the fewest spans whose letters, vowels *and*
   trope match exactly, drawn from all ~5,800 recordings in `local_ort_mp3s/t1..t5` (same Hazzan, same key
   across all five books: median ≈ G3, ±0.5 semitone). A Viterbi search over up to 8 occurrences per span
   minimizes join costs: pitch jump at the boundary, tempo mismatch, timbre mismatch, and a penalty for the
   low-bitrate Wayback sources.
4. **Re-pitching** — words that only occur with a different trope take the donor occurrence whose own pitch
   contour is closest to a word that *does* carry the target trope; that melody is imposed with Praat PSOLA,
   without time-warping and with shifts capped at 4 semitones. If the donor is already within 0.9 semitone
   it is used untouched.
5. **Assembly from pieces** — the few words that never occur at all (e.g. לִקְטֹ֔רֶת, וּבְקָרְבָתָ֛ם, הֵעָלֹתֽוֹ)
   are stitched from sub-word pieces using per-letter alignment, then re-pitched. These are the weakest spots.
6. **End of book (40:38)** — modelled on Deut 34:12: verse raised ~2 semitones, the tipcha word re-sung on
   Deut's "לְעֵינֵ֖י" contour, and "בְּכָל־מַסְעֵיהֶֽם" on Deut's "כָּל־יִשְׂרָאֵֽל" contour with its long final melisma.

## How the ta'amim are used

The cantillation marks drive the melody choices; the plain consonants and vowels alone would not.

- **Splice matching** requires letters, vowels *and* every trope mark to match exactly; the only mark allowed
  to differ is meteg/ga'ya, and only as a second-best fallback. So "וַיַּקְטֵ֥ר" (mercha) matches only other
  mercha occurrences, never "וַיַּקְטֵ֖ר" (tipcha).
- **Longer matches are preferred** because a conjunctive's tune depends on the disjunctive that follows it. A span
  like "כַּאֲשֶׁ֛ר צִוָּ֥ה יְהוָ֖ה אֶת־מֹשֶֽׁה" carries the whole tevir–mercha–tipcha–silluq phrase as he sang it.
- **Re-pitching** takes the melody from a word carrying the correct mark, chosen by: the accent itself, the
  stressed syllable (where the mark sits), syllable count, the mark on the *following* word (similar
  conjunctive→disjunctive context), and whether it is the verse-final silluq.
- **Verse endings** must come from a verse-final occurrence, so the sof pasuk cadence is genuine.
- **The 40:38 book ending** maps tipcha onto Deut 34:12's tipcha word and the silluq phrase onto Deut's silluq phrase.
- **Not used by the aligner**: forced alignment only needs the sounds, so it uses romanized letters and vowels.

Matching is against the *printed* marks. Where the Hazzan's rendering is non-standard, the splice
inherits his own rendering of that printed mark from another verse. In practice he is very consistent, so
this reproduces his style; it would only go wrong in a passage he sang differently from the marks.

`synth2.py` is the earlier version (first-match selection, time-warping re-pitch); `synth3.py` builds on it.

## Running

```sh
python3 -m venv ~/venvs/chant_sim && ~/venvs/chant_sim/bin/pip install -r utilities/chant_sim/requirements.txt
make download-mp3s                                   # populates local_ort_mp3s/ if needed
utilities/chant_sim/fetch_wayback.sh                 # recover Wayback verses
~/venvs/chant_sim/bin/python utilities/chant_sim/synth3.py 5,7,8,9       # simulate verses (comma list)
~/venvs/chant_sim/bin/python utilities/chant_sim/synth3.py 16,27 _loo    # blind tests of verses we have
~/venvs/chant_sim/bin/python utilities/chant_sim/make_listen_page.py /tmp/ex40listen --loo <dir-with-_loo.mp3>
python3 -m http.server --directory /tmp/ex40listen --bind 127.0.0.1 0
```

Output goes to `misc_mp3s/t2/40/replacements/` unless `CHANT_SIM_OUT` is set. A verse takes ~1–2 minutes
on a laptop CPU (mostly alignment; later runs reuse the cache).

Diagnostics: `coverage.py` (how much of each missing verse has exact-trope matches), `pitch.py books`
(key consistency across books), `bookend.py` (pitch profile of the book-ending verses), `misc_check.py`.
