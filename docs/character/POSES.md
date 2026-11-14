# シロネのポージング集(Gemini 用の文)

2026-11-14 本人「シロネのポージング集をつくっておこうか」。
サイト・X の返信・まとめ記事・お知らせなどで、場面に合う姿を選んで使うための素材。
(X の新作画像には入れない。11/14 に本人が「シロネはいらない、ロゴにする」と決めた)

## できているもの(2026-11-14、17種)

`assets/shirone/poses/<名前>.png`(背景を抜いた素材、長い辺 900px)。
元の Gemini の絵は `images/shirone/`(git に入れていない)。抜き直すときは `scripts/shirone_poses.py`。

wave・point-right・point-left・measure・peek・sit・sit-edge(白い台つき)・wow・think・sleepy・look-back・hop・sign(白い無地の札つき)・lie・bow・headphones、
それと stand(少しほほえんで片手をポケットに入れた立ち姿。最初の試しの1枚)。

- measure はファスナーにもメジャーが残っていて、手のメジャーと2つある(小さいので目立たない)

## 作り方

1. Gemini に **設定画 `shirone-sheet.jpg` と斜めの姿 `shirone/diag.png` を添付**し、下の「共通の文」＋「ポーズの文」を1つずつ渡す(1枚に1ポーズ。何ポーズも1枚に入れると顔や服がずれやすい)
2. できた絵は `docs/character/poses/<名前>.png` に置く。Claude が猫耳ヘッドホン・左耳のマイク・髪・パーカー・メジャー・短パン・靴を確かめ、rembg で背景を抜いて `assets/shirone/poses/<名前>.png` にする
3. **左右反転はしない。** マイクが右耳に移ってしまうので、右向き・左向きはそれぞれ作る

## 共通の文(毎回、ポーズの文の前に付ける)

```
Use the attached character sheet and figure image as the exact reference for the character. Keep her face, hair, outfit, proportions and colors identical.
The character: a tiny collectible desk figure girl, about 10 cm tall. Big head (about 1:2.5), round soft face, large pale grey-blue eyes, light blush on the cheeks. Chin-length pale silver bob with a faint lavender tint and blunt bangs. White cat-ear gaming headphones worn on the head, with a small white boom microphone from her LEFT ear cup. Oversized plain pale ice-blue zip-up hoodie (no text, no logo) with sleeves partly covering the hands, a tiny white retractable tape measure hanging from the zipper, pale grey shorts, light grey socks, chunky white sneakers. Soft matte 3D vinyl figure style, pastel, no black.
Image rules: one character only, centered, on a plain flat light grey background (#E6E8EC) with no floor line and no scenery. Soft even studio light, only a small soft contact shadow under her. No text, no logo, no other objects unless the pose says so. Square image, the whole figure visible with margin around it.
```

## ポーズの文(16種)

| 名前 | 使いどころ |
|---|---|
| wave | あいさつ・プロフィール・お知らせ |
| point-right / point-left | 物や文の横に立って「これ」と示す |
| measure | 測る係の看板の姿。記事のサイズ表の横など |
| peek | 写真や枠のふちから顔をのぞかせる |
| sit / sit-edge | 棚・見出し・ページの端にちょこんと |
| wow | 新作・セール・値下げのお知らせ |
| think | 比べる・迷う・「どっちがいい？」の問いかけ |
| sleepy | 朝・夜の投稿、更新お休みのお知らせ |
| look-back | ページの一番下・「またね」 |
| hop | 新しい種類・特集の始まり |
| sign | 白い無地の札を掲げる(文字はあとで Claude が入れる) |
| lie | 記事の終わり・まとめの横に寝そべる |
| bow | お礼・お詫び |
| headphones | 耳のヘッドホンを両手で押さえる(音・配信の物の話題) |

```
[wave] Pose: standing, facing the viewer, raising her right hand up to wave with the sleeve sliding down a little, left hand relaxed at her side. A small calm smile, eyes slightly sleepy.
```
```
[point-right] Pose: standing in three-quarter view turned toward the right side of the image, pointing to the right with her right index finger peeking out of the sleeve, arm stretched out at shoulder height. Looking in the same direction she points, calm face. Leave empty space on the right.
```
```
[point-left] Pose: standing in three-quarter view turned toward the left side of the image, pointing to the left with her left index finger peeking out of the sleeve, arm stretched out at shoulder height. Looking in the same direction she points, calm face. Leave empty space on the left.
```
```
[measure] Pose: standing, facing the viewer, holding the tiny white tape measure from her zipper with both hands and pulling the tape out sideways to about her own width, the thin white tape stretched straight between her hands. Focused, serious little face looking at the tape.
```
```
[peek] Pose: peeking up from behind an invisible straight edge: only her head, cat-ear headphones and both hands are visible, fingers resting on the edge, the image cuts across just below her chin in a perfectly straight horizontal line. Big curious eyes looking at the viewer.
```
```
[sit] Pose: sitting on the ground with both legs stretched straight out in front, sneakers pointing up, hands resting on her lap inside the sleeves. Facing the viewer, calm slightly sleepy face.
```
```
[sit-edge] Pose: sitting on the edge of a plain white rectangular block, legs dangling down over the front edge, hands holding the edge beside her hips. Facing the viewer, relaxed calm face. The white block is simple with no texture.
```
```
[wow] Pose: standing, both hands raised up near her cheeks in surprise with the sleeves falling back, mouth a small round "o", eyes wide open. Facing the viewer.
```
```
[think] Pose: standing, head tilted to one side, one hand (inside the sleeve) touching her chin, other arm folded under it. Eyes looking up to the side, puzzled thinking face.
```
```
[sleepy] Pose: standing, rubbing one eye with her sleeve-covered fist, other hand hanging loosely, a small yawn, eyes half closed. Facing the viewer.
```
```
[look-back] Pose: seen from behind, walking away, turning her head back over her right shoulder to look at the viewer, one hand raised a little to say bye. Calm small smile.
```
```
[hop] Pose: a small happy jump, both feet off the ground with knees bent, both arms up, sleeves flapping. Happy face with closed curved eyes (like the happy face on the sheet). A soft shadow on the ground below her.
```
```
[sign] Pose: standing, facing the viewer, holding up a blank plain white rectangular card above her head with both hands, the card about as wide as her shoulders and completely empty with no text. Calm face looking at the viewer.
```
```
[lie] Pose: lying on her stomach, chin resting on both hands (sleeves bunched up), feet up in the air behind her and crossed at the ankles. Facing the viewer, relaxed calm face.
```
```
[bow] Pose: standing, a polite small bow with the upper body tilted forward, both hands together in front of her shorts. Eyes closed, gentle face. Side three-quarter view.
```
```
[headphones] Pose: standing, both hands (sleeves partly covering) pressing the cat-ear headphone cups to her ears, eyes closed, a tiny content smile, head tilted slightly as if listening to music. Facing the viewer.
```

## 決まり(絵を使うときも同じ)

- 使った感想を言わせる場面には使わない(CHARACTER.md の「守ること」)
- 物を持たせない。ガジェットを使っている絵にすると「使った感想」に見えるため。測る・指す・のぞくまでにする
