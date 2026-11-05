(function(){var f=document.querySelector('[data-ws]');if(!f)return;var s=f.querySelector('svg'),z=f.querySelector('.ws-size'),kit=f.querySelector('.ws-kit'),sw=f.querySelector('.ws-sw'),N='http://www.w3.org/2000/svg';
var C=[['ピンク','#F3C9D2'],['ラベンダー','#CBB9EA'],['電球色','#F6D9A8'],['ミント','#CDEBDD'],['白','#FFFFFF']],R=11.5,H=R*Math.sqrt(3),Q=10,RW=5,MAX=30,mode='edit',col=0,P={};
var L={5:[[2,4],[3,4],[4,4],[5,4],[6,4]],7:[[5,3],[5,2],[5,4],[4,3],[4,4],[6,3],[6,4]],9:[[3,3],[3,4],[4,3],[4,4],[5,3],[5,4],[6,3],[6,4],[7,3]]};
function key(q,r){return q+','+r}
function xy(q,r){return[2+R+q*R*1.5,2+H/2+r*H+(q%2?H/2:0)]}
function nb(q,r){var o=q%2?[[0,-1],[0,1],[-1,0],[-1,1],[1,0],[1,1]]:[[0,-1],[0,1],[-1,-1],[-1,0],[1,-1],[1,0]];
return o.map(function(d){return[q+d[0],r+d[1]]}).filter(function(c){return c[0]>=0&&c[0]<Q&&c[1]>=0&&c[1]<RW})}
function el(n,a){var e=document.createElementNS(N,n);for(var k in a)e.setAttribute(k,a[k]);return e}
function hex(q,r,a){var p=xy(q,r),pts=[];for(var i=0;i<6;i++){var t=Math.PI/3*i;pts.push((p[0]+R*Math.cos(t)).toFixed(2)+','+(p[1]+R*Math.sin(t)).toFixed(2))}a.points=pts.join(' ');return el('polygon',a)}
function yen(n){return n.toLocaleString('ja-JP')+'円'}
function plan(n){if(!n)return'';var best=null;
for(var a=0;a<=4;a++)for(var b=0;b<=1;b++){if(!a&&!b)continue;var base=a*9+b*5,c=Math.max(0,Math.ceil((n-base)/3)),cost=a*28800+b*20800+c*8000;
if(!best||cost<best.cost||(cost==best.cost&&!b))best={a:a,b:b,c:c,cost:cost,tot:base+c*3}}
var parts=[];if(best.a)parts.push('9枚のセット'+(best.a>1?'×'+best.a:''));if(best.b)parts.push('5枚のセット');if(best.c)parts.push('3枚入りの追加パック×'+best.c);
var t='Shapes ヘキサゴンなら、'+parts.join('＋')+'で'+best.tot+'枚・'+yen(best.cost)+'(掲載時点)。';
if(best.b)t+='5枚のセットは掲載時点で在庫なし。';if(n>21)t+='21枚をこえるので、電源を足す必要があります。';return t}
function draw(){s.innerHTML='';var mw=54,mh=32.5,my=170-8-mh-14,ks=Object.keys(P);
s.appendChild(el('rect',{x:0,y:170,width:182,height:8,fill:'#EAE2D8'}));
s.appendChild(el('rect',{x:91-mw/2,y:my,width:mw,height:mh,rx:1.5,fill:'#FBF9F6',stroke:'#D8CFC6','stroke-width':.6}));
s.appendChild(el('rect',{x:91-mw/2+1.2,y:my+1.2,width:mw-2.4,height:mh-4,rx:.6,fill:'#E9DDF3'}));
s.appendChild(el('rect',{x:88,y:my+mh,width:6,height:170-my-mh,fill:'#E4DCD3'}));
var t=el('text',{x:91,y:my+mh/2+2,'text-anchor':'middle','font-size':3.6,fill:'#8C8178'});t.textContent='24インチのモニター';s.appendChild(t);
var ghosts={};
if(!ks.length)ghosts[key(5,4)]=[5,4];
else if(mode=='edit'&&ks.length<MAX)ks.forEach(function(k){var c=k.split(',').map(Number);nb(c[0],c[1]).forEach(function(n){var kk=key(n[0],n[1]);if(P[kk]===undefined)ghosts[kk]=n})});
Object.keys(ghosts).forEach(function(k){var g=ghosts[k];s.appendChild(hex(g[0],g[1],{'class':'ws-ghost',tabindex:0,role:'button','aria-label':'ここに1枚足す','data-k':k}))});
ks.forEach(function(k){var c=k.split(',').map(Number);s.appendChild(hex(c[0],c[1],{'class':'ws-panel',fill:C[P[k]][1],stroke:'#E7DFD7','stroke-width':.8,tabindex:0,role:'button','aria-label':(mode=='edit'?'このパネルを消す':'このパネルの色を変える'),'data-k':k}))});
if(!ks.length){z.textContent='点線の六角形を押して、1枚目を置いてください';kit.textContent='';return}
var xs=[],ys=[];ks.forEach(function(k){var c=k.split(',').map(Number),p=xy(c[0],c[1]);xs.push(p[0]);ys.push(p[1])});
var w=Math.max.apply(0,xs)-Math.min.apply(0,xs)+2*R,h=Math.max.apply(0,ys)-Math.min.apply(0,ys)+H;
z.textContent=ks.length+'枚 ・ 横 約'+Math.round(w)+'cm × 縦 約'+Math.round(h)+'cm';kit.textContent=plan(ks.length)}
function preset(n){P={};(L[n]||[]).forEach(function(c,i){P[key(c[0],c[1])]=i%3});draw()}
function act(k){if(!k)return;if(P[k]===undefined){if(Object.keys(P).length<MAX)P[k]=col}else if(mode=='edit')delete P[k];else P[k]=col;draw()}
C.forEach(function(c,i){var b=document.createElement('button');b.type='button';b.dataset.c=i;b.setAttribute('aria-pressed',i==0);b.setAttribute('aria-label',c[0]);b.title=c[0];b.innerHTML='<i style="background:'+c[1]+'"></i>';sw.appendChild(b)});
f.addEventListener('click',function(e){var b=e.target.closest('button');
if(b){if(b.dataset.l!==undefined)preset(b.dataset.l);
if(b.dataset.m){mode=b.dataset.m;f.querySelectorAll('[data-m]').forEach(function(x){x.setAttribute('aria-pressed',x===b)});draw()}
if(b.dataset.c!==undefined){col=+b.dataset.c;sw.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-pressed',x===b)})}return}
var h=e.target.closest('[data-k]');if(h)act(h.getAttribute('data-k'))});
s.addEventListener('keydown',function(e){var k=e.target.getAttribute&&e.target.getAttribute('data-k');if((e.key=='Enter'||e.key==' ')&&k){e.preventDefault();act(k);var n=s.querySelector('[data-k="'+k+'"]');if(n)n.focus()}});
preset(5)})();
