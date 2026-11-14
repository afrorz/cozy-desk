"""シロネのポーズ画像(images/shirone の Gemini の絵)の背景を抜いて assets/shirone/poses/<名前>.png にする。

rembg が入った JapanHasThat-shorts の .venv の Python で動かす:
  ../../shorts/JapanHasThat-shorts/.venv/Scripts/python.exe scripts/shirone_poses.py 10 [名前]
猫耳の内側や袖口のように rembg が透かしてしまう穴は元の色で埋め、足の間など背景色の隙間は透明のまま残す。
新しい絵を足したら下の M にファイル名の一部と名前を足す。
"""
import os,sys
import numpy as np
from scipy import ndimage
from rembg import remove,new_session
from PIL import Image
M={'27lb':'sign','3e8d':'sit-edge','3j7v':'measure','b2im':'lie','dhz8':'headphones','dqt2':'look-back',
'eg49':'hop','fah5':'peek','g8h2':'think','gsut':'stand','gwhe':'point-right','gxfj':'point-left',
'hiut':'wow','k5l5':'sleepy','rdpf':'wave','x8j2':'sit','yfk3':'bow'}
src='images/shirone';out='assets/shirone/poses'
TH=float(sys.argv[1])
s=new_session('isnet-general-use')
for f in sorted(os.listdir(src)):
  k=[k for k in M if k in f]
  if not k or (len(sys.argv)>2 and M[k[0]]!=sys.argv[2]): continue
  name=M[k[0]]
  rgb=np.array(Image.open(os.path.join(src,f)).convert('RGB')).astype(float)
  a=np.array(remove(Image.fromarray(rgb.astype('uint8')),session=s).convert('RGBA'))[...,3].astype(int)
  H,W=a.shape
  bg=np.median(np.concatenate([rgb[:40,:40].reshape(-1,3),rgb[:40,-40:].reshape(-1,3)]),axis=0)
  if name=='sit-edge':
    y0=int(H*0.58); a[y0:][a[y0:]>8]=255
  solid=a>24
  holes=ndimage.binary_fill_holes(solid)&~solid
  lab,n=ndimage.label(holes); log=[]
  for i in range(1,n+1):
    m=lab==i
    dist=np.abs(rgb[m]-bg).mean(axis=1)
    frac=(dist>TH).mean()
    if frac>0.3 or name=='sit-edge': a[m]=255
    log.append(f'{m.sum()}:{frac:.2f}')
  out_im=np.dstack([rgb,a.clip(0,255)]).astype('uint8')
  img=Image.fromarray(out_im,'RGBA')
  img=img.crop(Image.fromarray(((a>24)*255).astype('uint8')).getbbox())
  img.thumbnail((900,900),Image.LANCZOS)
  img.save(os.path.join(out,name+'.png'),optimize=True)
  print(name,bg.round(),log)
