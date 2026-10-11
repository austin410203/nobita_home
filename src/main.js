// 野比家 — first-person exploration (three.js, manga / toon look)
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { OutlineEffect } from 'three/addons/effects/OutlineEffect.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

const MODEL_URL = './models/nobita_house.glb';
const EYE = 1.5;            // eye height (m) – a 5th grader would be ~1.25, an adult ~1.6
const RADIUS = 0.28;        // body radius for wall collision
const WALK = 2.0, RUN = 3.8; // m/s
const REACH = 2.6;          // interaction distance
const STEP = 0.45;          // max step-up height (stairs risers are 0.2 m)

// ---------------------------------------------------------------- renderer / scene
const app = document.getElementById('app');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
app.appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(window.innerWidth, window.innerHeight);
Object.assign(labelRenderer.domElement.style, { position: 'fixed', inset: '0', pointerEvents: 'none' });
app.appendChild(labelRenderer.domElement);

const scene = new THREE.Scene();
scene.background = makeSky();
scene.fog = new THREE.Fog(0xd6ebff, 35, 110);

const camera = new THREE.PerspectiveCamera(72, window.innerWidth / window.innerHeight, 0.05, 300);

// anime-style lighting: cool sky fill + warm sun with crisp shadows
scene.add(new THREE.HemisphereLight(0xd9e8ff, 0x9a8a78, 1.7));
const sun = new THREE.DirectionalLight(0xfff3e2, 2.3);
sun.position.set(-14, 20, 16);
sun.target.position.set(3, 0, -5);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 70 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);

// outlines (inverted hull) – brown ink like the reference sheet
const effect = new OutlineEffect(renderer, { defaultThickness: 0.0032, defaultColor: [0.24, 0.15, 0.11], defaultAlpha: 1 });

// 3-step toon ramp
const gradient = new THREE.DataTexture(new Uint8Array([105, 105, 105, 255, 185, 185, 185, 255, 255, 255, 255, 255]), 3, 1);
gradient.minFilter = gradient.magFilter = THREE.NearestFilter;
gradient.needsUpdate = true;

// ---------------------------------------------------------------- sky (equirectangular canvas)
function makeSky() {
  const w = 2048, h = 1024, c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  const grd = g.createLinearGradient(0, 0, 0, h / 2);
  grd.addColorStop(0, '#3f86e6'); grd.addColorStop(0.75, '#9ccbfa'); grd.addColorStop(1, '#e3f1ff');
  g.fillStyle = grd; g.fillRect(0, 0, w, h / 2);
  g.fillStyle = '#e3f1ff'; g.fillRect(0, h / 2, w, h / 2);
  // fluffy cumulus clouds: white puffs with a lavender underside
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let k = 0; k < 26; k++) {
    const cx = rnd() * w, cy = h * (0.18 + rnd() * 0.27), s = 30 + rnd() * 70;
    for (let i = 0; i < 9; i++) {
      const x = cx + (rnd() - 0.5) * s * 3.2, y = cy + (rnd() - 0.6) * s * 0.9, r = s * (0.45 + rnd() * 0.6);
      g.fillStyle = 'rgba(205,212,238,0.95)'; g.beginPath(); g.ellipse(x, y + r * 0.18, r, r * 0.62, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = 'rgba(255,255,255,0.97)'; g.beginPath(); g.ellipse(x, y, r * 0.95, r * 0.55, 0, 0, Math.PI * 2); g.fill();
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// ---------------------------------------------------------------- controls & HUD
const controls = new PointerLockControls(camera, document.body);
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('start');
const progressEl = document.getElementById('progress');
const tooltip = document.getElementById('tooltip');
const ttName = tooltip.querySelector('.name'), ttDesc = tooltip.querySelector('.desc'), ttHint = tooltip.querySelector('.hint');
const roomEl = document.getElementById('room');
const crosshair = document.getElementById('crosshair');

startBtn.addEventListener('click', () => controls.lock());
controls.addEventListener('lock', () => overlay.classList.add('hidden'));
controls.addEventListener('unlock', () => { overlay.classList.remove('hidden'); startBtn.textContent = '繼續探索'; });

const keys = new Set();
addEventListener('keydown', (e) => {
  keys.add(e.code);
  if (e.code === 'KeyE' && controls.isLocked) interact();
  if (e.code === 'KeyL') { showTags = !showTags; refreshTags(true); }
});
addEventListener('keyup', (e) => keys.delete(e.code));
addEventListener('mousedown', (e) => { if (controls.isLocked && e.button === 0) interact(); });
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); labelRenderer.setSize(innerWidth, innerHeight);
});

// ---------------------------------------------------------------- load the house
const draco = new DRACOLoader().setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/gltf/');
const loader = new GLTFLoader().setDRACOLoader(draco);

const walkables = [];   // floors, stairs ramp, ground
const solids = [];      // walls, furniture, closed doors…
const pickables = [];   // everything visible (for the crosshair)
let mixer, clips = new Map();
const tagged = [];      // objects that get a floating name tag (L)
let showTags = false;

loader.load(MODEL_URL, (gltf) => {
  const root = gltf.scene;
  const cache = new Map();
  root.traverse((o) => {
    if (!o.isMesh) return;
    const src = o.material;
    if (!cache.has(src)) {
      const m = new THREE.MeshToonMaterial({
        color: src.color, map: src.map, gradientMap: gradient,
        transparent: src.transparent, opacity: src.opacity, side: src.side,
      });
      if (m.map) m.map.colorSpace = THREE.SRGBColorSpace;
      if (src.transparent) m.depthWrite = false;
      const noLine = src.transparent || src.userData.toon_outline === 0;
      m.userData.outlineParameters = noLine ? { visible: false } : { thickness: 0.0032, color: [0.24, 0.15, 0.11], alpha: 1 };
      cache.set(src, m);
    }
    o.material = cache.get(src);
    o.castShadow = !src.transparent;
    o.receiveShadow = true;

    const name = o.name;
    if (/colonly/i.test(name)) { o.visible = false; walkables.push(o); return; }   // invisible stair ramp
    if (findUp(o, (n) => n.userData.room)) walkables.push(o);
    else if (!/^(BD_FarGround|Street_Line|Wire|Living_Rug|Stairs_Risers)/.test(name)) solids.push(o);
    pickables.push(o);
  });
  scene.add(root);

  // animations: one "<name>_Open" clip per openable object (0 = closed -> end = open)
  mixer = new THREE.AnimationMixer(root);
  for (const c of gltf.animations) clips.set(c.name, c);
  root.traverse((o) => { if (o.userData.openable && clips.has(o.userData.anim_open_action)) openables.push(o); });

  // floating name tags for interactive objects + main furniture
  const skip = /(_Casing|_Frame|_SashA|_Glass|_Cap|_Leaves\d+|_Trunk|_Kakebuton|_Pillow|_Cushions|_Spokes|_Tyre|_Grips|_Handlebar|_Saddle|_Carrier|_Basket|_Fenders|_Mattress|_Cover|_Pillows)$/;
  root.traverse((o) => {
    const u = o.userData;
    if (!u.label || skip.test(o.name) || /^(BlockWall|Tree_|UtilityPole|Stair_|Win_.*_Frame)/.test(o.name) || /(_Pedestal|_CenterDrawer|_Sideboard|_TVStand|_Cabinet|_Chest|_Dresser|_Tansu)$/.test(o.name) && !u.openable) return;
    if (o.parent && o.parent.userData.label === u.label && !u.openable) return;
    const el = document.createElement('div');
    el.className = 'tag' + (u.openable ? ' open' : '');
    el.textContent = u.label;
    const tag = new CSS2DObject(el);
    const box = new THREE.Box3().setFromObject(o);
    tag.position.copy(o.worldToLocal(box.getCenter(new THREE.Vector3()).setY(box.max.y)));
    tag.visible = false;
    o.add(tag);
    tagged.push({ obj: o, tag });
  });

  // spawn on the street in front of the gate, facing the house
  const spawn = root.getObjectByName('Spawn_Street');
  const p = spawn ? spawn.getWorldPosition(new THREE.Vector3()) : new THREE.Vector3(3.9, 0, 5.5);
  camera.position.set(p.x, p.y + EYE, p.z);
  camera.lookAt(p.x, EYE + 1.2, p.z - 10);

  document.getElementById('loading').style.display = 'none';
  startBtn.disabled = false;
}, (e) => { if (e.total) progressEl.textContent = Math.round((e.loaded / e.total) * 100) + '%'; },
(err) => { progressEl.textContent = '載入失敗：' + err.message; console.error(err); });

function findUp(o, pred) {
  for (let n = o; n; n = n.parent) if (pred(n)) return n;
  return null;
}

// ---------------------------------------------------------------- interaction
const ray = new THREE.Raycaster();
const center = new THREE.Vector2(0, 0);
let focused = null;   // { label, openable }

const openables = [];   // filled after load
const _box = new THREE.Box3(), _p = new THREE.Vector3();
function pick() {
  ray.setFromCamera(center, camera);
  ray.far = 8;
  const hit = ray.intersectObjects(pickables, false)[0];
  const hitDist = hit ? hit.distance : Infinity;
  // bounding-box test so thin things (gate bars, drawer fronts, window sashes) are easy to aim at
  let best = null, bestD = Infinity;
  for (const o of openables) {
    _box.setFromObject(o).expandByScalar(0.03);
    const p = ray.ray.intersectBox(_box, _p);
    if (!p) continue;
    const d = p.distanceTo(ray.ray.origin);
    if (d < bestD && d <= REACH && d <= hitDist + 0.12) { best = o; bestD = d; }
  }
  if (best) return { openable: best, labelled: best, dist: bestD };
  if (!hit) return null;
  const openable = findUp(hit.object, (n) => n.userData.openable);
  const labelled = findUp(hit.object, (n) => n.userData.label);
  if (!labelled && !openable) return null;
  return { openable: hit.distance <= REACH ? openable : null, labelled: labelled || openable, dist: hit.distance };
}

function toggle(obj) {
  const clip = clips.get(obj.userData.anim_open_action);
  if (!clip) return;
  const a = mixer.clipAction(clip);
  const open = !obj.userData._open;
  obj.userData._open = open;
  a.setLoop(THREE.LoopOnce, 1);
  a.clampWhenFinished = true;
  a.enabled = true;
  a.paused = false;
  a.timeScale = open ? 1 : -1;
  if (!a.isRunning()) {
    if (open && a.time >= clip.duration - 1e-3) a.time = 0;
    if (!open && a.time <= 1e-3) a.time = clip.duration;
  }
  a.play();
}

function interact() {
  const f = pick();
  if (f && f.openable) toggle(f.openable);
}

function updateHUD() {
  const f = pick();
  focused = f;
  if (f && f.labelled && f.dist < 6) {
    const u = f.labelled.userData;
    ttName.textContent = u.label || '';
    ttDesc.textContent = u.desc || '';
    ttHint.textContent = f.openable ? `[E] ${f.openable.userData._open ? '關上' : '打開'}` : '';
    tooltip.classList.add('show');
  } else tooltip.classList.remove('show');
  crosshair.classList.toggle('active', !!(f && f.openable));
}

let tagTimer = 0;
function refreshTags(force) {
  if (!force && performance.now() - tagTimer < 250) return;
  tagTimer = performance.now();
  const me = camera.position;
  const v = new THREE.Vector3();
  for (const { obj, tag } of tagged) {
    obj.getWorldPosition(v);
    tag.visible = showTags && v.distanceTo(me) < 5 && Math.abs(v.y - (me.y - EYE)) < 2.4;
  }
}

// ---------------------------------------------------------------- movement & collision
const down = new THREE.Raycaster(); down.far = 4;
const side = new THREE.Raycaster();
let vy = 0, feet = null;
const DOWN = new THREE.Vector3(0, -1, 0);

function groundAt(x, z, fromY) {
  down.set(new THREE.Vector3(x, fromY + STEP, z), DOWN);
  const h = down.intersectObjects(walkables, false)[0];
  return h || null;
}

function blocked(from, dir, dist) {
  for (const hgt of [STEP + 0.1, 1.0, 1.45]) {
    side.set(new THREE.Vector3(from.x, from.y + hgt, from.z), dir);
    side.far = dist + RADIUS;
    if (side.intersectObjects(solids, false).length) return true;
  }
  return false;
}

function move(dt) {
  if (feet === null) feet = camera.position.y - EYE;
  const speed = keys.has('ShiftLeft') || keys.has('ShiftRight') ? RUN : WALK;
  const fwd = new THREE.Vector3(); camera.getWorldDirection(fwd); fwd.y = 0; fwd.normalize();
  const right = new THREE.Vector3().crossVectors(fwd, camera.up).normalize();
  const wish = new THREE.Vector3();
  if (keys.has('KeyW') || keys.has('ArrowUp')) wish.add(fwd);
  if (keys.has('KeyS') || keys.has('ArrowDown')) wish.sub(fwd);
  if (keys.has('KeyD') || keys.has('ArrowRight')) wish.add(right);
  if (keys.has('KeyA') || keys.has('ArrowLeft')) wish.sub(right);
  if (wish.lengthSq() > 0) wish.normalize().multiplyScalar(speed * dt);

  const base = new THREE.Vector3(camera.position.x, feet, camera.position.z);
  // axis-separated sliding collision (the house is axis-aligned)
  for (const axis of ['x', 'z']) {
    const d = wish[axis];
    if (!d) continue;
    const dir = new THREE.Vector3(axis === 'x' ? Math.sign(d) : 0, 0, axis === 'z' ? Math.sign(d) : 0);
    if (!blocked(base, dir, Math.abs(d))) base[axis] += d;
  }
  // gravity + step up/down onto walkable surfaces
  const g = groundAt(base.x, base.z, feet);
  vy -= 9.8 * dt;
  let ny = feet + vy * dt;
  if (g && ny <= g.point.y + 0.001) { ny = g.point.y; vy = 0; }
  if (g && g.point.y > feet && g.point.y - feet <= STEP) { ny = g.point.y; vy = 0; }
  if (ny < -5) { ny = 0; vy = 0; }
  feet = ny;
  camera.position.set(base.x, feet + EYE, base.z);

  const room = g && findUp(g.object, (n) => n.userData.room);
  roomEl.textContent = room ? room.userData.room : '';
}

// ---------------------------------------------------------------- loop
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);
  if (mixer) mixer.update(dt);
  if (controls.isLocked) move(dt);
  if (mixer) { updateHUD(); refreshTags(false); }
  effect.render(scene, camera);
  labelRenderer.render(scene, camera);
});

// debug helper in the console: window.nobita.toggle('Door_2F_Nobita')
window.nobita = {
  scene, camera, THREE, solids, walkables,
  probe: (dx, dz, far = 1) => {   // what blocks the player in a direction?
    const f = camera.position.y - EYE, r = new THREE.Raycaster(); const out = [];
    for (const h of [STEP + 0.1, 1.0, 1.45]) {
      r.set(new THREE.Vector3(camera.position.x, f + h, camera.position.z), new THREE.Vector3(dx, 0, dz).normalize()); r.far = far;
      const x = r.intersectObjects(solids, false)[0]; out.push(x ? `${h}: ${x.object.name} @${x.distance.toFixed(2)}` : `${h}: -`);
    }
    return out;
  },
  toggle: (n) => { const o = scene.getObjectByName(n); if (o) toggle(o); },
  // simulate holding keys for `sec` seconds (e.g. nobita.walk(['KeyW'], 2)) – handy for automated tests
  walk: (codes, sec) => { codes.forEach((c) => keys.add(c)); for (let t = 0; t < sec; t += 1 / 60) move(1 / 60); codes.forEach((c) => keys.delete(c)); return { pos: camera.position.toArray().map((v) => +v.toFixed(2)), room: roomEl.textContent }; },
  look: (yawDeg, pitchDeg = 0) => { camera.rotation.set(THREE.MathUtils.degToRad(pitchDeg), THREE.MathUtils.degToRad(yawDeg), 0, 'YXZ'); },
  tick: (sec) => { for (let t = 0; t < sec; t += 1 / 60) mixer.update(1 / 60); scene.updateMatrixWorld(true); },
  shot: () => { effect.render(scene, camera); return 'ok'; },
  focus: () => { updateHUD(); return focused && { label: focused.labelled?.userData.label, openable: focused.openable?.name }; },
  interact,
};
