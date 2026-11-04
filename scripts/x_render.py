# X(シロネ)の投稿画像の部品。1200x675・壁はラベンダーからクリーム・机は白・シロネは背丈10cm(docs/X_POSTING.md)。
# 使い方: from x_render import *  → base() で背景、place() で物とシロネを机に立たせ、bar() で高さの目盛り、credit() で出典。
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,DESK=1200,675,500
CM=360/13
ACC=(122,107,170)
# 文字はサイトの見出しと同じ丸文字 Zen Maru Gothic(scripts/fonts、OFL)
import os as _os
FD=_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"fonts")
F=lambda n,w="Bold": ImageFont.truetype(f"{FD}/ZenMaruGothic-{w}.ttf", n)
SH=r"D:/MyDocument/ClaudeApp/media/CozyDesk/docs/character/shirone/"
def base():
    # 継ぎ目のない撮影用の背景(壁と机の境目の線を作らない)。上の淡いラベンダーから下の白へ、なめらかに変える。
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    top,mid,bot=(236,230,245),(244,240,240),(250,249,247)
    for y in range(H):
        t=y/H
        if t<0.55: a,b,u=top,mid,t/0.55
        else: a,b,u=mid,bot,(t-0.55)/0.45
        u=u*u*(3-2*u)
        d.line([(0,y),(W,y)],fill=tuple(int(a[i]+(b[i]-a[i])*u) for i in range(3)))
    return im
def body(path,crop=None):
    im=Image.open(path).convert("RGBA")
    if crop: im=im.crop(crop)
    return im.crop(im.getbbox())
def place(im,obj,cx,cm=None,px=None):
    h=px or int(cm*CM); w=int(obj.width*h/obj.height)
    o=obj.resize((w,h),Image.LANCZOS)
    sh=Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.ellipse([cx-w*0.55,DESK-10,cx+w*0.55,DESK+14],fill=(90,80,100,60))
    sh=sh.filter(ImageFilter.GaussianBlur(10)); im.paste(sh,(0,0),sh)
    x=int(cx-w/2); im.paste(o,(x,DESK-h),o)
    return x,x+w,DESK-h
def bar(im,x,top,cm,side):
    d=ImageDraw.Draw(im)
    d.line([(x,top),(x,DESK+16)],fill=ACC,width=3)
    for y in (top,DESK+16): d.line([(x-8,y),(x+8,y)],fill=ACC,width=3)
    t=f"{cm:g}cm"; f=F(30); tw=d.textlength(t,font=f)
    tx= x-16-tw if side=="l" else x+16
    d.text((tx,(top+DESK)/2-18),t,font=f,fill=ACC)
def label(im,text,cx,y,size=44):
    d=ImageDraw.Draw(im); f=F(size); tw=d.textlength(text,font=f)
    d.text((cx-tw/2,y),text,font=f,fill=ACC)
def credit(im,text):
    ImageDraw.Draw(im).text((24,634),text,font=F(20),fill=(140,130,150))
