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
| 左を空けるよう強く書いたら、カメラが引いて主役(キーボード)がとても小さくなった | カメラを「机の近くから、商品写真のように」と書き、大きさを割合で書く(机は右60%で右と下にはみ出す・主役は横幅の1/3・左の空きは40%) |
| 「左」を空けるよう書いたら、カメラが左前から机の角を見る形になり、L字の机が部屋の真ん中に出て、椅子が机の向こう(壁側)に入った(電源タップ) |「まっすぐな長方形の机(L字・角の机ではない)」「カメラは奥の壁にほぼ正面から向く。机の手前のふちは絵の下の方をほぼ水平に横切る」と書く。椅子の置き場に迷いそうなら「椅子は入れない」と書く |
| 共通の文のまま作ると、どの記事も「正面から壁と机」で同じ絵になった(11/5 六角形ライト、本人「同じパターンだなぁ」) | 記事ごとに視点を変える。「斜め上から」と書くと真上からの見下ろしになった。本人が欲しかったのは「左斜め後ろから」(座る人の数歩うしろ・少し左に立ち、右前の机と壁を斜めに見る・椅子の背中が手前)。例は docs/boards/hexagon-wall-lights.txt |
| 机の上が主役と植物だけで、さびしかった(11/5 本人「シンプルすぎる。もっとガジェット女子っぽく」) | 机の上に、パステルのキーボード・デスクマット・ヘッドホンとスタンド・スピーカー・小さなフィギュアやぬいぐるみなどを並べ、にぎやかにする(色は白とパステルだけ) |
| 文で頼んでも横1024ピクセルのまま | Gemini の保存の選択肢(高画質・拡大)を本人に使ってもらう。なければそのまま使う |

## 共通の文(毎回そのまま入れる)

```
One single continuous room scene, seen in one shot. Not a split image, not a diptych, not two panels — the wall, the light and the floor continue smoothly across the whole picture.

Style: a soft, minimal 3D illustration of a cozy, all-white home office, like a pastel interior render. Warm off-white walls, soft diffused morning light from a window on the right, gentle leaf shadows on the wall.

Floor: very pale whitewashed oak flooring, almost white with a faint warm cream tint. Never brown or medium wood.

Furniture: one simple straight rectangular white desk (not L-shaped, not a corner desk), with its back edge pushed flush against the wall (no gap between the desk and the wall). If a chair is visible, it is a white gaming-style chair (tall backrest with side wings, headrest pillow, lumbar pillow) in off-white and cream with subtle blush-pink accents. No black parts.

Camera: facing the back wall almost straight on, from slightly above and slightly to the left, like a product photo of a desk setup. The front edge of the desk runs almost horizontally across the lower part of the picture (the desk corner never points at the camera). The camera is near the desk, not far away in the room.

Layout and sizes: the desk stands against the back wall. The desk top fills the right 60% of the picture and runs off the right and bottom edges of the frame. The hero product is LARGE (about one third of the image width). To the left of the desk, only the same wall continues as calm empty space with soft light — about 40% of the picture, nothing placed there (a title card and product photos will be added later).

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
