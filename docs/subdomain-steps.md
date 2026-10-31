# cozydesk.gadgetterminal.com を使えるようにする手順

サイトは GitHub Pages(GT と同じ仕組み)に置き、アドレスを cozydesk.gadgetterminal.com にする。

## 1. Claude がやること(本人の OK のあと)

- GitHub に公開リポジトリ `afrorz/cozy-desk` を作り、サイト一式を置く
- GitHub Pages を「GitHub Actions で公開」にして、独自ドメインに `cozydesk.gadgetterminal.com` を入れる

## 2. 本人がやること(Cloudflare、5分)

1. [Cloudflare](https://dash.cloudflare.com/) にログインし、**gadgetterminal.com** を開く
2. 左のメニューの **DNS** → **レコード** を開く
3. **「レコードを追加」** を押して、次のとおり入れる

   | 項目 | 入れる値 |
   |---|---|
   | タイプ | CNAME |
   | 名前 | cozydesk |
   | ターゲット | afrorz.github.io |
   | プロキシ ステータス | **オフ**(雲が灰色の「DNS のみ」) |

4. **「保存」** を押す

プロキシをオフにするのは、GitHub が自動で鍵(https)を発行できるようにするため。

## 3. Claude がやること(DNS のあと)

- 数分〜1時間で GitHub が https の鍵を発行する。発行されたら「HTTPS を強制」をオンにして、https://cozydesk.gadgetterminal.com/ が開くか確かめる
