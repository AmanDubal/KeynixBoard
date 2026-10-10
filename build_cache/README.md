# Build cache

Only the small `config.json` files (key-timing metadata) are kept here to
keep the repo lean. The large source recordings were deleted after the
sliced output was generated into `../keyboard_sound/sounds/`.

To fully regenerate from scratch (re-download the raw Mechvibes recordings
and re-slice them, plus re-synthesize the gun sounds):

```bash
BASE="https://raw.githubusercontent.com/hainguyents13/mechvibes/main/src/audio"

# single-sprite packs (config.json + sound.ogg)
for p in cherrymx-blue-pbt cherrymx-red-abs cherrymx-brown-pbt topre-purple-hybrid-pbt; do
  mkdir -p "$p"
  curl -sf "$BASE/$p/config.json" -o "$p/config.json"
  curl -sf "$BASE/$p/sound.ogg"   -o "$p/sound.ogg"
done

# nk-cream: individual per-letter + special-key wav files
mkdir -p nk-cream
curl -sf "$BASE/nk-cream/config.json" -o nk-cream/config.json
for f in space enter backspace shift tab a b c d e f g h i j k l m n o p q r s t u v w x y z; do
  curl -sf "$BASE/nk-cream/$f.wav" -o "nk-cream/$f.wav"
done

# holy-pandas: individual mp3 files
mkdir -p holy-pandas
curl -sf "$BASE/holy-pandas/config.json" -o holy-pandas/config.json
for f in BACKSPACE ENTER SPACE GENERIC_R0 GENERIC_R1 GENERIC_R2 GENERIC_R3 GENERIC_R4; do
  curl -sf "$BASE/holy-pandas/$f.mp3" -o "holy-pandas/$f.mp3"
done

# turquoise: individual mp3 files under press/
mkdir -p turquoise/press
curl -sf "$BASE/turquoise/config.json" -o turquoise/config.json
for f in BACKSPACE ENTER SPACE GENERIC_R0 GENERIC_R1 GENERIC_R2 GENERIC_R3 GENERIC_R4; do
  curl -sf "$BASE/turquoise/press/$f.mp3" -o "turquoise/press/$f.mp3"
done

pip install soundfile numpy scipy
python3 slice_build.py     # -> keyboard_sound/sounds/{thocky,creamy,clacky,clicky,marbly,mechanical,silent}
python3 synth_guns.py      # -> keyboard_sound/sounds/{gun_pistol,gun_shotgun,gun_sniper,gun_rifle}
```

To regenerate the `fahh` theme (downloads + trims the "Fahh" meme sound
effect from YouTube):

```bash
pip install yt-dlp soundfile numpy
python3 fetch_fahh.py      # -> keyboard_sound/sounds/fahh
```
