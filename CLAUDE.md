# Cozy Desk

白デスク・淡色デスクに合う、白と淡い色のガジェットを種類ごとに紹介するサイト(https://cozydesk.gadgetterminal.com)。
Gadget Terminal(`media\GadgetTerminal`)の姉妹サイト。収益は紹介料(もしも経由の楽天・Amazon・Yahoo!ショッピング)。

```
content/posts/*.md → python scripts/build.py → public/ → git push で GitHub Pages に公開
```

## 決まり

- **最大の目的は紹介料で稼ぐこと(2026-10-31 本人)。** 載せる物は楽天・Amazon・Yahoo の1つ以上で正規に売っている物(3つそろう必要はない)。機能や記事を足すときは、クリックと購入が増えるかを先に考える
- **記事の書き方は `docs/WRITING.md`。** 公式ページで確かめた事実だけ・使った感想を書かない・値段は「掲載時点」・「技適」などの専門用語を出さない(裏では確かめる)
- 種類(9つ)・トップの絵の押せる点・紹介リンクは `config/site.yaml`
- トップの絵 `assets/scene.jpg` は本人が Gemini で作ったもの(2026-10-31)。差し替えたら `scene.points` の位置を合わせ直す
- **もしもの GT 用の a_id をこのサイトに貼らない。** もしもでこのサイトを登録して提携が通ってから `affiliate:` を埋める。空のあいだは普通の検索リンクを出す
- 「女性向け」と名乗らない(本人判断)
- 見た目の元になった見本は `notes\desk-gadgets\design\`

## 写真の点検

- `python scripts/check_images.py` で、記事の写真が今も開けるかを確かめる(11/1 に Lian Li の公式サイトがロボットよけ画面を返し、写真が2枚消えたため)。開けない写真は、同じ物の公式・日本の正規代理店・公式ストアの写真に替える
- 「要ブラウザ確認」(403)は、ブラウザでは開けることがある(エレコムなど)

## 公開

検証(build.py が通る・記事数が想定どおり)してから push してよい。push すると数分で公開される。

## コマンド(Windows)

```bash
python scripts/build.py           # public/ を作り直す
python scripts/build.py --serve   # http://localhost:8790
```
