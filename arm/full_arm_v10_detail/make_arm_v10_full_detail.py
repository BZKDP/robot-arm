from pathlib import Path

ROOT = Path(r".\arm")
OUT = ROOT / "full_arm_v10_detail"
SRC = ROOT / "base_j1" / "arm_v8_5axis.html"
THREE = ROOT / "printed" / "hall_j1_dual_index_v2" / "three.r160.min.js"


def replace_between(text: str, begin: str, end: str, replacement: str) -> str:
    a = text.index(begin)
    b = text.index(end, a)
    return text[:a] + replacement + text[b:]


html = SRC.read_text(encoding="utf-8")
html = html.replace(
    "<title>Робо-рука v8 — 5 осей, метал. муфты, всё соединено</title>",
    "<title>Робо-рука v10 — полная детальная сборка, 6 осей</title>",
)
html = html.replace(
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>',
    "<script>" + THREE.read_text(encoding="utf-8") + "</script>",
)

controls = r'''<div id="ui" class="panel">
  <h1>🦾 Рука v10 — детальная сборка, 6 осей</h1>
  <div class="sub">Основа v8: реальные отверстия, муфты и крепёж. Добавлены новый J3, перенесённый roll, клетки M5×80 и датчики.</div>
  <div class="row"><label>J1 база <b id="v1">15°</b></label><input id="j1" type="range" min="-180" max="180" value="15"></div>
  <div class="row"><label>J2 плечо <b id="v2">22°</b></label><input id="j2" type="range" min="-95" max="95" value="22"></div>
  <div class="row"><label style="color:#ffb347">J3 новый локоть <b id="v3">-48°</b></label><input id="j3" type="range" min="-125" max="125" value="-48"></div>
  <div class="row"><label style="color:#65d8ff">J4 roll после J3 <b id="v4">0°</b></label><input id="j4" type="range" min="-180" max="180" value="0"></div>
  <div class="row"><label>J5 запястье <b id="v5">-35°</b></label><input id="j5" type="range" min="-120" max="120" value="-35"></div>
  <div class="row"><label>J6 головка <b id="v6">0°</b></label><input id="j6" type="range" min="-180" max="180" value="0"></div>
  <div class="buttons"><button onclick="pose('fold')">Сложить</button><button onclick="pose('work')">Рабочая</button><button onclick="pose('straight')">Прямо</button></div>
  <div class="buttons"><button onclick="toggleFasteners()">Винты</button><button onclick="toggleSensors()">Датчики</button><button onclick="togglePanels()">Панели</button></div>
  <div class="buttons"><button onclick="resetCamera()">Общий вид</button><button onclick="closeCamera()">Крупный вид</button><button onclick="pose('work')">Сборка</button></div>
  <div id="hint">ЛКМ — вращение · колесо — масштаб · ПКМ — сдвиг · клик по детали — описание крепления.</div>
</div>
<button id="panelToggle" onclick="togglePanels()">☰ Панели</button>
'''
html = replace_between(html, '<div id="ui" class="panel">', '<div id="bom"', controls)
html = html.replace(
    "#card .nm{font-weight:700;font-size:13.5px;color:#ffce6b}",
    "#card .nm{font-weight:700;font-size:13.5px;color:#ffce6b}.sub{font-size:11px;color:#9fb0c9;line-height:1.4;margin-bottom:7px}.buttons{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin-top:7px}.buttons button{border:0;border-radius:6px;padding:6px 3px;background:#34445f;color:#fff;cursor:pointer}.buttons button:hover{background:#496184}#panelToggle{position:fixed;z-index:6;left:12px;bottom:12px;border:1px solid #536783;border-radius:8px;padding:7px 10px;background:#1d293b;color:#fff;cursor:pointer}",
)

bom = r'''const BOM={
 baseCage:{n:'Корпус нижнего NEMA17 — клетка M5×80',d:'Двигатель не разбирается. Задняя плита, нижняя обойма, вентилируемая крышка и разъёмная передняя рамка стянуты четырьмя M5×80 с увеличенными шайбами и nyloc.',s:'🖨 актуально'},
 vise:{n:'Тиски — временная опора',d:'Зажимаются широкие боковые поверхности нижней печатной обоймы, не корпус двигателя и не верхняя крышка.',s:'стенд'},
 motor17L:{n:'NEMA17 длинный 42,3×42,3×48',d:'Силовые оси J1, J2 и новый J3. Заводские стяжные винты не откручиваются.',s:'✅ есть'},
 motor17S:{n:'NEMA17 короткий 42,3×42,3×47',d:'Используется в J4 roll и J5.',s:'✅ есть'},
 gb71:{n:'Планетарный редуктор CM36 1:71',d:'Корпус Ø36×35, торец Ø22, вал Ø8×16, четыре M3 по окружности Ø27,5.',s:'✅ есть'},
 hallJ1:{n:'J1: два SS49E + магнит D3×2',d:'Два неподвижных SS49E лежат в отдельных карманах кольцевого кронштейна и прижаты рамкой 2×M3×6. Магнит вращается вместе с дном U-скобы.',s:'🖨 v2'},
 j1d:{n:'J1: металлическая муфта → дно U-скобы',d:'Муфта Ø8 фиксируется на лыске и прикручивается к дну четырьмя M3. Показаны винты, гайки и реальная сетка отверстий.',s:'✅ собрано'},
 chan2:{n:'J2: U-скоба 96×48',d:'Стенки 96×48×2,5; три Ø14 с шагом 24 и полная сетка Ø4,2 с шагом 8 мм.',s:'✅ есть'},
 chan3:{n:'J3: новая U-скоба 96×48',d:'Новый сгибающийся локоть — полноценная копия силового pitch-узла J2.',s:'новое'},
 j3Cup:{n:'Стакан труба J2 → U-скоба J3',d:'Карман 20,4×20,4 глубиной 33,5; фланец 58×52×8; восемь M4 к штатной сетке дна и два поперечных M4×40 через полый вкладыш.',s:'🖨 готов'},
 adapV2:{n:'Адаптер редуктора v2',d:'Четыре M3×10 в CM36 и два M4×12 в крайние бобышки адаптера.',s:'✅'},
 mcoup:{n:'Металлическая фланцевая муфта Ø8',d:'Фланец Ø21,8×2; хаб Ø14,1; BC отверстий 16,5; установочный винт в лыску.',s:'✅'},
 bridge:{n:'Мост V7/T5',d:'40×56×5; радиальные пазы под муфту BC18–24; два M4 к трубе; центральный проход Ø9,2.',s:'🖨 финал'},
 cass:{n:'Кассета внутри трубы',d:'Поддерживает стенки профиля и удерживает шайбы с гайками M4, не позволяя смять трубу.',s:'✅'},
 kfl08:{n:'Противоположная опора KFL08',d:'Ромбический подшипник под вал Ø8; прикручен двумя M4×16 к существующей диагонали отверстий скобы.',s:'✅'},
 rod8:{n:'Опорный вал Ø8×36',d:'Жёстко вращается вместе с трубой, входит в KFL08. На торце расположен магнит для AS5600.',s:'металл'},
 pcb:{n:'AS5600 на выходной оси',d:'Плата закреплена козырьком на болтах KFL08 и смотрит чипом на магнит выходного вала.',s:'датчик'},
 tube2:{n:'Труба J2→J3 — 140 мм',d:'Алюминиевый профиль 20×20×1,5; отверстия под ось и два M4, проводка проходит внутри.',s:'✅'},
 tube3:{n:'Труба J3→roll — 110 мм',d:'Новый профиль 20×20×1,5; на дальнем конце установлен перенесённый roll.',s:'новое'},
 rollCage:{n:'J4 roll — клетка M5×80',d:'Задний стакан, квадратный ключ, разъёмная передняя рамка и четыре внешних M5×80. Заводские винты NEMA17 не трогаются.',s:'🖨 v5'},
 chan5:{n:'J5: наклон запястья',d:'Третий полный pitch-узел: U-скоба, CM36, муфта, мост V7, ось Ø8, KFL08 и AS5600.',s:'как J2'},
 tube5:{n:'Труба J5→J6 — 110 мм',d:'Профиль 20×20×1,5 с внутренней кассетой и проводкой.',s:'металл'},
 wristMnt:{n:'Стакан кисти NEMA14',d:'Крепит NEMA14 к торцу трубы J5. В модели показаны поперечные M4 и моторный крепёж.',s:'прототип'},
 j6d:{n:'J6: поворот головки и захват',d:'NEMA14 вращает головку; показан условный электрический захват.',s:'концепт'},
 wire:{n:'Проводка',d:'Жгуты проходят внутри полых труб, у каждого сустава оставляется сервисная петля.',s:'маршрут'}
};

'''
html = replace_between(html, "const BOM={", "const allG=[];", bom)

mat_old_start = "const M=c=>"
mat_old_end = "const BOM={"
a = html.index(mat_old_start)
b = html.index(mat_old_end, a)
mat_new = '''const M=c=>new THREE.MeshStandardMaterial({color:c,roughness:.55,metalness:.35});
const mat={alu:M(0xc8ccd2),motor:M(0x24272d),gb:M(0x315ba8),face:M(0x9aa4ad),shaft:M(0xe6e6e6),
 printed:M(0xe0912b),newj:M(0xffa13d),roll:M(0x36bfe5),buy:M(0x555c66),screw:M(0x22252b),scrHi:M(0xe5bd4b),pcb:M(0x1b7f3b),
 mag:M(0xd93030),tube:M(0xb4bac2),sup:M(0x555a64),n14:M(0x3d4450),hall:M(0x31c982),sensorA:M(0xffd84a),sensorB:M(0xc86ce8),wire:M(0x101216),wireR:M(0xb52a2a),
 hole:new THREE.MeshBasicMaterial({color:0x2e333b,side:THREE.DoubleSide})};

'''
html = html[:a] + mat_new + html[b:]

helper_marker = "// МЕТАЛ. МУФТА как настоящая"
helpers = r'''
function wireBetween(g,a,b,r=1,m=mat.wire){const A=new THREE.Vector3(...a),B=new THREE.Vector3(...b),v=B.clone().sub(A);const q=new THREE.Mesh(new THREE.CylinderGeometry(r,r,v.length(),12),m);q.position.copy(A.clone().add(B).multiplyScalar(.5));q.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),v.clone().normalize());g.add(q);return q}
function washerY(g,d,x,y,z){const q=new THREE.Mesh(new THREE.TorusGeometry(d/2,1,8,24),mat.scrHi);q.rotation.x=Math.PI/2;q.position.set(x,y,z);g.add(q);return q}
function label3(text,color=0xffffff,w=300){const c=document.createElement('canvas');c.width=w;c.height=64;const x=c.getContext('2d');x.fillStyle='rgba(10,15,23,.82)';x.fillRect(0,5,w,50);x.font='700 25px Segoe UI';x.textAlign='center';x.fillStyle='#'+color.toString(16).padStart(6,'0');x.fillText(text,w/2,38);const s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),transparent:true,depthTest:false}));s.scale.set(w*.25,16,1);return s}

'''
html = html.replace(helper_marker, helpers + helper_marker, 1)

base_marker = "// ================= БАЗА + J1"
ui_marker = "// ================= UI ================="
chain = r'''// ================= ДЕТАЛЬНАЯ БАЗА + ШЕСТЬ ОСЕЙ =================
// Тиски — только для понимания установки.
const vise=G('vise');scene.add(vise);box(132,28,86,mat.sup,0,14,0,vise);box(16,45,86,mat.sup,-45,48,0,vise);box(16,45,86,mat.sup,45,48,0,vise);

// Актуальная клетка нижнего мотора M5×80.
const baseCage=G('baseCage');scene.add(baseCage);
box(78,8,78,mat.printed,0,18,0,baseCage);box(72,50,10,mat.printed,0,45,-31,baseCage);box(72,50,8,mat.printed,0,45,31,baseCage);
box(10,50,52,mat.printed,-31,45,0,baseCage);box(10,50,52,mat.printed,31,45,0,baseCage);
// Разъёмная передняя рамка вокруг CM36.
box(19.6,8,78,mat.hall,-29.2,72,0,baseCage);box(19.6,8,78,mat.hall,29.2,72,0,baseCage);box(39,8,19.6,mat.hall,0,72,-29.2,baseCage);box(39,8,19.6,mat.hall,0,72,29.2,baseCage);
for(const x of [-20,-10,0,10,20])box(5,20,.35,mat.hole,x,45,35.1,baseCage);
for(const x of [-31,31])for(const z of [-31,31]){boltY(baseCage,5,80,x,14,z,1);washerY(baseCage,15,x,18,z);washerY(baseCage,15,x,76,z);nutY(baseCage,8,x,80,z)}
const baseLab=label3('КЛЕТКА J1 · 4×M5×80',0xffc35a);baseLab.position.set(-82,43,0);baseCage.add(baseLab);

const mJ1=G('motor17L');scene.add(mJ1);box(42.3,48,42.3,mat.motor,0,44,0,mJ1);
const gbJ1=G('gb71');scene.add(gbJ1);cylY(36,35,mat.gb,0,85.5,0,gbJ1);cylY(22,1.6,mat.face,0,103.8,0,gbJ1);cylY(8,16,mat.shaft,0,111,0,gbJ1);

// Неподвижный двойной Hall-кронштейн J1.
const hallJ1=G('hallJ1');scene.add(hallJ1);const hallRing=new THREE.Mesh(new THREE.TorusGeometry(22,3,12,48),mat.hall);hallRing.rotation.x=Math.PI/2;hallRing.position.y=105.2;hallJ1.add(hallRing);
box(18.7,2.6,13,mat.hall,0,106.2,15.6,hallJ1);box(4.6,1.8,3.5,mat.sensorA,-2.7,108.2,15.6,hallJ1);box(4.6,1.8,3.5,mat.sensorB,2.7,108.2,15.6,hallJ1);box(18.7,.9,8,mat.newj,0,109.55,15.6,hallJ1);
for(const x of [-7.5,7.5])boltY(hallJ1,3,6,x,110,15.6,-1);
for(const x of [-4,-2.7,-1.4,1.4,2.7,4])wireBetween(hallJ1,[x,107,16],[x,100,25],.35,mat.wire);
const hallLab=label3('2× SS49E',0x63e6a1,190);hallLab.position.set(48,112,18);hallJ1.add(hallLab);

// Вращающаяся часть J1.
const g1=new THREE.Group();scene.add(g1);const mc1=G('mcoup');g1.add(mc1);coupY(mc1,105);
const bJ1=G('j1d');g1.add(bJ1);for(const a of [45,135,225,315]){const x=7.5*Math.cos(a*Math.PI/180),z=7.5*Math.sin(a*Math.PI/180);boltY(bJ1,3,8,x,121.5,z,-1);nutY(bJ1,6,x,114,z)}
// Магнит вращается вместе со скобой и проходит между A/B.
cylY(3,2,mat.mag,0,114.8,15.6,bJ1);

const u2=pitchUnit('chan2','tube2',140,'motor17L');u2.root.position.set(0,117,0);g1.add(u2.root);
const l2=label3('J2 · 140 мм',0xffffff,220);l2.position.set(58,60,0);u2.root.add(l2);

// Силовой стакан J2→J3: реальный фланец, гильза, 8+2 винта.
const j3Mount=new THREE.Group();j3Mount.position.set(0,u2.tubeTop,9);u2.pivot.add(j3Mount);
const j3Cup=G('j3Cup');j3Mount.add(j3Cup);
box(30,33.5,30,mat.newj,0,-16.75,0,j3Cup);box(20.4,33.7,20.4,mat.tube,0,-16.7,0,j3Cup);box(58,8,52,mat.newj,0,4,0,j3Cup);
holeY(7,0,8.05,0,j3Cup);
for(const [x,z] of [[-16,-8],[-16,8],[16,-8],[16,8],[-8,-16],[8,-16],[-8,16],[8,16]]){boltY(j3Cup,4,16,x,10,z,-1);nutY(j3Cup,7,x,0,z)}
for(const y of [-9.5,-23.5]){const q=new THREE.Mesh(new THREE.CylinderGeometry(2,2,40,16),mat.scrHi);q.rotation.z=Math.PI/2;q.position.set(0,y,0);j3Cup.add(q);nutZ(j3Cup,7,22,y,0);washerY(j3Cup,12,-20,y,0)}
const cupLab=label3('СТАКАН J3 · 8×M4 + 2×M4',0xffb347,350);cupLab.position.set(-72,-20,0);j3Cup.add(cupLab);

const u3=pitchUnit('chan3','tube3',110,'motor17L');u3.root.position.set(0,8,0);j3Mount.add(u3.root);
const l3=label3('J3 НОВЫЙ · 110 мм',0xffb347,290);l3.position.set(66,60,0);u3.root.add(l3);

// Перенесённый roll в актуальной клетке M5×80.
function makeRollCage(){const root=G('rollCage');
 box(30.4,32.5,30.4,mat.roll,0,-16.25,0,root);box(78,8,78,mat.roll,0,4,0,root);box(43,3.5,43,mat.hall,0,9.75,0,root);
 const mot=G('motor17S');root.add(mot);box(42.3,47,42.3,mat.motor,0,35,0,mot);
 box(19.6,8,78,mat.hall,-29.2,62.5,0,root);box(19.6,8,78,mat.hall,29.2,62.5,0,root);box(39,8,19.6,mat.hall,0,62.5,-29.2,root);box(39,8,19.6,mat.hall,0,62.5,29.2,root);
 for(const x of [-31,31])for(const z of [-31,31]){boltY(root,5,80,x,0,z,1);washerY(root,15,x,4,z);washerY(root,15,x,66,z);nutY(root,8,x,70,z)}
 const gb=G('gb71');root.add(gb);cylY(36,35,mat.gb,0,84,0,gb);cylY(22,1.6,mat.face,0,102.3,0,gb);cylY(8,16,mat.shaft,0,110,0,gb);
 const mc=G('mcoup');root.add(mc);coupY(mc,104);const rot=new THREE.Group();rot.position.set(0,116,0);root.add(rot);
 for(const a of [45,135,225,315]){const x=8.25*Math.cos(a*Math.PI/180),z=8.25*Math.sin(a*Math.PI/180);boltY(root,3,8,x,118,z,-1);nutY(root,6,x,110,z)}
 const lab=label3('J4 ROLL · КЛЕТКА M5×80',0x65d8ff,340);lab.position.set(80,55,0);root.add(lab);return{root,rot}}
const rollBase=new THREE.Group();rollBase.position.set(0,u3.tubeTop,9);u3.pivot.add(rollBase);const roll=makeRollCage();rollBase.add(roll.root);

const u5=pitchUnit('chan5','tube5',110,'motor17S');u5.root.position.set(0,0,0);roll.rot.add(u5.root);const l5=label3('J5 · 110 мм',0xffffff,220);l5.position.set(58,60,0);u5.root.add(l5);

// Кисть J6.
const wristG=new THREE.Group();wristG.position.set(0,u5.tubeTop,9);u5.pivot.add(wristG);const wCup=G('wristMnt');wristG.add(wCup);
box(29.4,31,29.4,mat.printed,0,-14,0,wCup);box(42,5,42,mat.printed,0,4,0,wCup);for(const y of [-9,-23]){const q=new THREE.Mesh(new THREE.CylinderGeometry(2,2,40,16),mat.scrHi);q.rotation.z=Math.PI/2;q.position.set(0,y,0);wCup.add(q)}
const j6d=G('j6d');wristG.add(j6d);box(35.2,28,35.2,mat.n14,0,20.5,0,j6d);cylY(5,8,mat.shaft,0,38.5,0,j6d);
const g6=new THREE.Group();g6.position.set(0,43,0);wristG.add(g6);box(34,8,22,mat.hall,0,4,0,g6);box(7,34,5,mat.hall,-13,21,0,g6);box(7,34,5,mat.hall,13,21,0,g6);const l6=label3('J6 ГОЛОВКА',0xffffff,230);l6.position.set(55,24,0);wristG.add(l6);

// Видимые участки жгутов; основная магистраль остаётся внутри труб.
const wires=G('wire');scene.add(wires);wireBetween(u2.pivot,[6,-18,16],[6,u2.tubeTop-8,16],1.25,mat.wire);wireBetween(u3.pivot,[6,-18,16],[6,u3.tubeTop-8,16],1.25,mat.wireR);wireBetween(u5.pivot,[6,-18,16],[6,u5.tubeTop-8,16],1.25,mat.wire);

'''
html = replace_between(html, base_marker, ui_marker, chain)

ui = r'''// ================= UI =================
const listEl=document.getElementById('list'),cardEl=document.getElementById('card');
const order=['baseCage','vise','motor17L','motor17S','gb71','hallJ1','j1d','chan2','tube2','j3Cup','chan3','tube3','adapV2','mcoup','bridge','cass','kfl08','rod8','pcb','rollCage','chan5','tube5','wristMnt','j6d','wire'];
for(const k of order){const b=BOM[k];if(!b)continue;const d=document.createElement('div');d.className='item';d.dataset.k=k;d.innerHTML=b.n+' <span class="st">'+b.s+'</span>';d.onclick=()=>select(k);listEl.appendChild(d)}
let selKey=null,selTarget=null,flashT=0;function select(k,target){selKey=k;selTarget=target||null;flashT=1;for(const e of listEl.children)e.classList.toggle('sel',e.dataset.k===k);const b=BOM[k];cardEl.style.display='block';cardEl.innerHTML='<div class="nm">'+b.n+'</div>'+b.d}
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();let downXY=null;renderer.domElement.addEventListener('pointerdown',e=>downXY=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!downXY)return;if(Math.hypot(e.clientX-downXY[0],e.clientY-downXY[1])<5){mouse.x=e.clientX/innerWidth*2-1;mouse.y=-(e.clientY/innerHeight)*2+1;ray.setFromCamera(mouse,cam);for(const h of ray.intersectObjects(scene.children,true)){let o=h.object;while(o&&!o.userData.bom)o=o.parent;if(o&&BOM[o.userData.bom]){select(o.userData.bom,o);break}}}downXY=null});
function bind(id,vid,fn){const e=document.getElementById(id);e.oninput=()=>{document.getElementById(vid).textContent=e.value+'°';fn(+e.value*Math.PI/180)};e.oninput()}
bind('j1','v1',a=>g1.rotation.y=a);bind('j2','v2',a=>u2.pivot.rotation.z=a);bind('j3','v3',a=>u3.pivot.rotation.z=a);bind('j4','v4',a=>roll.rot.rotation.y=a);bind('j5','v5',a=>u5.pivot.rotation.z=a);bind('j6','v6',a=>g6.rotation.y=a);
const POSES={fold:[10,58,-105,0,72,0],work:[15,22,-48,0,-35,0],straight:[0,0,0,0,0,0]};function pose(k){['j1','j2','j3','j4','j5','j6'].forEach((id,i)=>{const e=document.getElementById(id);e.value=POSES[k][i];e.oninput()})}
let fastOn=true,sensOn=true,panelsOn=true;function toggleFasteners(){fastOn=!fastOn;scene.traverse(o=>{if(o.material===mat.scrHi)o.visible=fastOn})}function toggleSensors(){sensOn=!sensOn;for(const g of allG)if(['hallJ1','pcb'].includes(g.userData.bom))g.visible=sensOn}function togglePanels(){panelsOn=!panelsOn;document.getElementById('ui').style.display=panelsOn?'block':'none';document.getElementById('bom').style.display=panelsOn?'block':'none'}
let th=-.82,ph=1.12,R=760,tgt=new THREE.Vector3(0,335,0),drag=null;function updCam(){cam.position.set(tgt.x+R*Math.sin(ph)*Math.cos(th),tgt.y+R*Math.cos(ph),tgt.z+R*Math.sin(ph)*Math.sin(th));cam.lookAt(tgt)}function resetCamera(){th=-.82;ph=1.12;R=760;tgt.set(0,335,0);updCam()}function closeCamera(){R=500;tgt.set(0,335,0);updCam()}updCam();
renderer.domElement.addEventListener('pointerdown',e=>drag={x:e.clientX,y:e.clientY,b:e.button});addEventListener('pointerup',()=>drag=null);addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;if(drag.b===2){const s=R/700,rt=new THREE.Vector3().subVectors(cam.position,tgt).cross(cam.up).normalize();tgt.addScaledVector(rt,-dx*s);tgt.y+=dy*s}else{th+=dx*.008;ph=Math.min(2.8,Math.max(.25,ph-dy*.008))}updCam()});renderer.domElement.addEventListener('wheel',e=>{R=Math.min(2200,Math.max(180,R*(e.deltaY>0?1.1:.9)));updCam()});renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
(function loop(){requestAnimationFrame(loop);if(selKey&&flashT>0){flashT-=.02;const on=Math.sin(Date.now()*.015)>0,targets=selTarget?[selTarget]:allG.filter(g=>g.userData.bom===selKey);for(const g of targets)g.traverse(o=>{if(o.material&&o.material.emissive)o.material.emissive.setHex(on?0x604000:0)});if(flashT<=0)for(const g of allG)g.traverse(o=>{if(o.material&&o.material.emissive)o.material.emissive.setHex(0)})}renderer.render(scene,cam)})();
'''
html = replace_between(html, ui_marker, "</script>", ui)

OUT.mkdir(parents=True, exist_ok=True)
target = OUT / "ARM_V10_FULL_DETAIL_INTERACTIVE_3D.html"
target.write_text(html, encoding="utf-8")

readme = """# Роборука V10 — полная детальная модель

Открыть `ARM_V10_FULL_DETAIL_INTERACTIVE_3D.html` двойным щелчком. Интернет не нужен.

Это сборочная модель для проверки компоновки, а не единый файл для печати.

Включено: шесть осей J1–J6, подробная геометрия v8, новый J3, перенесённый J4 roll, нижняя клетка M5×80, roll-клетка M5×80, двойной Hall-индекс J1, AS5600 на pitch-суставах, муфты, KFL08, трубы, винты, шайбы, гайки и видимые маршруты жгутов.

Гармонические редукторы HBS17 намеренно не добавлены: они пока только рассматриваются.
"""
(OUT / "README_RU.md").write_text(readme, encoding="utf-8")
print(target)
