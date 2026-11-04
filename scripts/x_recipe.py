# X の「デスクレシピ」画像(1200x1500)。11/4 の見本(変わり種の電源タップ8選)を作ったときのもの。c1.png〜c8.png(切り抜き)と names を差し替えて使う。決まりは docs/X_POSTING.md
from PIL import Image, ImageDraw, ImageFont, ImageFilter
# 文字はサイトの見出しと同じ丸文字 Zen Maru Gothic(scripts/fonts、OFL)。11/4 本人「フォントもかわいく」
FD=__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"fonts")
F=lambda n,b=True,w=None: ImageFont.truetype(f"{FD}/ZenMaruGothic-{w or ('Bold' if b else 'Medium')}.ttf", n)
names=[("コンセントハウス","おうちの形|煙突にUSBの口"),("エレコム 球体タップ","手のひらサイズ|壁に直接挿す"),("サンワ タワー型","4つの面に|コンセント12口"),("CIO Tap002","USB-Cケーブルが|出て、戻る"),("Pixio TAP COMPACT","スマホを|立てられる"),("Fargo TAPKING T5","くるっと回る|コンセント6口"),("サンワ スリムタップ","縦にも横にも|挿せる"),("CIO Tap001","5cm角の|小さな直挿し")]
W,H=1200,1500
im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
for y in range(H):
    t=y/H; a,b=(238,233,247),(250,248,244)
    d.line([(0,y),(W,y)],fill=tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3)))
ACC=(110,96,160); INK=(70,62,90); SUB=(125,117,140)
d.text((70,56),"机の上に、小さな家",font=F(34),fill=SUB)
d.text((70,100),"変わり種の白い電源タップ 8選",font=F(62,w="Black"),fill=INK)
cw,ch=510,250; gx,gy=40,24; x0,y0=(W-2*cw-gx)//2,210
for k,(nm,ft) in enumerate(names):
    r,c=divmod(k,2); x=x0+c*(cw+gx); y=y0+r*(ch+gy)
    sh=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([x,y+6,x+cw,y+ch+6],24,fill=(90,80,120,40)); sh=sh.filter(ImageFilter.GaussianBlur(10)); im.paste(sh,(0,0),sh)
    d=ImageDraw.Draw(im); d.rounded_rectangle([x,y,x+cw,y+ch],24,fill=(255,255,255))
    cut=Image.open(f"c{k+1}.png"); cut.thumbnail((215,215 if cut.width/cut.height<3 else 400),Image.LANCZOS)
    im.paste(cut,(x+18+(215-cut.width)//2,y+(ch-cut.height)//2),cut)
    tx=x+252
    d.text((tx,y+22),f"{k+1}",font=F(28),fill=(190,180,220))
    nl=[nm] if d.textlength(nm,font=F(29))<=240 else nm.split(" ",1)
    for j,l in enumerate(nl): d.text((tx,y+60+j*38),l,font=F(29),fill=INK)
    yy=y+66+len(nl)*38+8
    lines=ft.split("|")
    for j,l in enumerate(lines): d.text((tx,yy+j*31),l,font=F(22,False),fill=SUB)
yb=y0+4*(ch+gy)+6
sh_=Image.open(r"D:/MyDocument/ClaudeApp/media/CozyDesk/docs/character/shirone/front.png").convert("RGBA"); sh_=sh_.crop(sh_.getbbox())
fh=130; f=sh_.resize((int(sh_.width*fh/sh_.height),fh),Image.LANCZOS)
im.paste(f,(x0+20,yb),f)
d.rounded_rectangle([x0+108,yb+26,x0+590,yb+90],32,fill=(255,255,255))
d.text((x0+136,yb+40),"買える場所は、返信のリンクから",font=F(26),fill=ACC)
d.text((W-x0-200,yb+44),"Cozy Desk",font=F(34),fill=(170,158,205))
d.text((x0,H-42),"画像: ソニック・エレコム・サンワサプライ・CIO Mate・Pixio・Fargo 各公式・Cozy Desk(シロネ)",font=F(18,False),fill=(150,142,160))
im.save("recipe.jpg",quality=90); print(yb+fh)
