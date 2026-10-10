# Audio Attribution

This project bundles real mechanical-switch recordings from the
**[Mechvibes](https://github.com/hainguyents13/mechvibes)** project by Hai Nguyen,
licensed under the **MIT License** (full text below). Mechvibes bundles and
redistributes community-recorded sound packs for exactly this kind of reuse.

| Our theme    | Source Mechvibes pack            | Notes |
|--------------|-----------------------------------|-------|
| `clicky`     | `cherrymx-blue-pbt`               | sliced from the pack's sound sprite |
| `clacky`     | `cherrymx-red-abs`                | sliced from the pack's sound sprite |
| `mechanical` | `cherrymx-brown-pbt`              | sliced from the pack's sound sprite |
| `creamy`     | `nk-cream` (original by Ryan)     | individual per-key recordings |
| `thocky`     | `holy-pandas` (Copyright Thomas Lai) | individual per-key recordings |
| `marbly`     | `turquoise` (Copyright Thomas Lai)   | individual per-key recordings |
| `silent`     | derived from `topre-purple-hybrid-pbt` | heavily low-pass filtered + attenuated by us to emulate a dampened/silenced switch |
| `fahh`       | [YouTube: "Fahh" - meme sound effect](https://www.youtube.com/watch?v=VP6eZu3SAak) | audio extracted & trimmed to the sound itself (silence removed) by us; plays in full on every keystroke |
| `gun_pistol` | —                                   | 100% procedurally **synthesized** by this project — pistol crack + mag-release/slap reload |
| `gun_shotgun`| —                                   | 100% procedurally **synthesized** by this project — shotgun boom + shell-insert/pump reload |
| `gun_sniper` | —                                   | 100% procedurally **synthesized** by this project — crack+boom + slow bolt-action reload |
| `gun_rifle`  | —                                   | 100% procedurally **synthesized** by this project — sharp rifle crack + mag-swap/bolt reload |

## Mechvibes MIT License

```
MIT License

Copyright (c) 2021 Hai Nguyen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The individual `holy-pandas` and `turquoise` community packs additionally
carry a `Copyright (c) Thomas Lai` MIT notice from their original recorder,
reproduced above under the same terms.

**Disclaimer on the `gun_*` themes:** every file in
`keyboard_sound/sounds/gun_pistol/`, `gun_shotgun/`, `gun_sniper/` and
`gun_rifle/` was generated from scratch with NumPy/SciPy signal processing
(filtered noise, synthesized tones, and envelopes) for this project. No real
gunfire audio, sample library, or copyrighted recording was used or
distributed.

**Note on the `fahh` theme:** the audio is extracted from the public YouTube
video ["Fahh" - meme sound effect](https://www.youtube.com/watch?v=VP6eZu3SAak),
trimmed to remove leading/trailing silence. It is included here as a short,
widely-circulated meme sound effect for personal/fun use; if you redistribute
this project, please keep this attribution and the original video link intact.
