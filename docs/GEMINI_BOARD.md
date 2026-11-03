# 看板の絵を Gemini で作るときの文(board_style: scene 用)

まとめ記事の看板を「本人が Gemini で作った部屋の絵＋題の札＋物の写真」にするときに、Claude が本人に渡す文の決まり。
(2026-11-03 モニターアーム・キーボードの2本で、作り直しが続いたので本人「今後同じようなことにならないように」)

## 起きたこと(同じことを起こさない)

| 起きたこと | 防ぎ方(文に必ず入れる) |
|---|---|
| 1画面用のアームに、モニター2台がついていた | 物の「数」と「つながり方」を具体的に書く。2画面用なら「1本の柱から2本の腕、それぞれが1台を支える」まで書く |
| 椅子がふつうの椅子だった(本人はゲーミングチェア風がよかった) | 部屋に置く家具の種類を毎回書く。椅子は白いゲーミングチェア風(下の共通の文) |
| 床のフローリングが茶色かった | 床は毎回「ほぼ白の、白く塗った明るいオーク」と書く(下の共通の文) |
| 画像が横1024ピクセルで小さかった | 「高解像度・横2000ピクセル以上」と書き、本人にも大きいサイズで出してもらうよう伝える |
| 左下に机の角と床が入り、写真を乗せる場所が狭かった | 「左半分は上から下まで何もない壁と床だけ」と書く |
| 机が壁から離れて、宙に浮いたように見えた(キーボード) | 「机の奥のふちは壁にぴったりつける」と書く |
| 「LEFT half は空」と書いたら、左右2枚に分けた絵になった(キーボード) | 「左半分」と書かない。「1つの続いた部屋。机は右寄り、左は同じ壁が続いて空いている」「2枚に分けない」と書く |
| 文で頼んでも横1024ピクセルのまま | Gemini の保存の選択肢(高画質・拡大)を本人に使ってもらう。なければそのまま使う |

## 共通の文(毎回そのまま入れる)

```
One single continuous room scene, seen in one shot. Not a split image, not a diptych, not two panels — the wall, the light and the floor continue smoothly across the whole picture.

Style: a soft, minimal 3D illustration of a cozy, all-white home office, like a pastel interior render. Warm off-white walls, soft diffused morning light from a window on the right, gentle leaf shadows on the wall.

Floor: very pale whitewashed oak flooring, almost white with a faint warm cream tint. Never brown or medium wood.

Furniture: white desk, with its back edge pushed flush against the wall (no gap between the desk and the wall). If a chair is visible, it is a white gaming-style chair (tall backrest with side wings, headrest pillow, lumbar pillow) in off-white and cream with subtle blush-pink accents. No black parts.

Layout: the desk stands against the back wall, placed toward the right side of the room. To the left of the desk, the same wall simply continues as wide, calm empty space with soft light — nothing placed there (a title card and product photos will be added later).

Color palette: off-white, cream, light beige, soft blush pink, pale lavender, pale grey. No black or dark objects.

No brand logos, no text, no letters, no numbers, no watermarks.

Composition: wide 16:9, high resolution (at least 2000 pixels wide), clean, airy, calm and premium mood.
```

## 記事ごとに足す文(主役)

- 主役の物は机の上に置き(机は右寄り)、数・形・つながり方を具体的に書く
- 文字が出やすい物(キーボードのキー、画面、箱)は「文字・記号なし(blank)」と書く
- 画面は「ピンクからラベンダーのやわらかいグラデーションの壁紙」

## 本人に渡すときに一緒に伝えること

- 横2000ピクセル以上で出してもらう(小さいと PC でぼやける)
- 届いたら Claude が先に見て、上の表の6つ(数・椅子・床・大きさ・左半分・机と壁)を確かめてから使う。外れていたら、その部分だけ直す文を渡す

## 届いた絵の入れ方

横1800ピクセルに縮めて `assets/boards/<名前>.jpg` に置き、記事に `board_style: scene` と `board_image:` を書く(docs/WRITING.md)。
