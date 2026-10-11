// Switchable stylised rendering: material mode + outline + light grade + full-screen post shader.
import * as THREE from 'three';

export const STYLES = [
  { key: 'cel', name: '日式賽璐璐動畫', refs: '《原神》《崩壞：星穹鐵道》、TV 動畫背景',
    desc: '三階硬陰影、咖啡色輪廓線、平塗色（預設風格）',
    mat: 'toon3', line: { on: true, t: 0.0032, c: [0.24, 0.15, 0.11], a: 1 }, post: 0,
    sun: [0xfff3e2, 2.3], hemi: [0xd9e8ff, 0x9a8a78, 1.7] },
  { key: 'ghibli', name: '吉卜力／新海誠手繪背景', refs: '《龍貓》《你的名字》《二之國》',
    desc: '柔和多階陰影、暖色光、光暈（Bloom）、淡淡的輪廓',
    mat: 'toon6', line: { on: true, t: 0.0022, c: [0.35, 0.25, 0.18], a: 0.55 }, post: 1,
    sun: [0xffe2bd, 2.6], hemi: [0xdfe9ff, 0xb59a7a, 1.8] },
  { key: 'moebius', name: 'Moebius／法式漫畫', refs: '《Sable》《無主之地》',
    desc: '粗黑輪廓、平塗、暗部用斜線排線表現',
    mat: 'toon2', line: { on: true, t: 0.0058, c: [0.05, 0.04, 0.04], a: 1 }, post: 2,
    sun: [0xfff6e8, 2.5], hemi: [0xe6eef8, 0x8d8172, 1.4] },
  { key: 'sumi', name: '水墨／浮世繪', refs: '《大神》《對馬戰鬼》黑澤模式',
    desc: '墨色濃淡分階、宣紙紋理、墨線',
    mat: 'lambert', line: { on: true, t: 0.0045, c: [0.06, 0.06, 0.06], a: 1 }, post: 3,
    sun: [0xffffff, 2.2], hemi: [0xffffff, 0x777777, 1.5] },
  { key: 'crayon', name: '蠟筆／繪本', refs: '《耀西的手工世界》《Tearaway》',
    desc: '紙張紋理、蠟筆筆觸、線條微微抖動、色彩溫暖',
    mat: 'toon3', line: { on: true, t: 0.0035, c: [0.30, 0.20, 0.25], a: 0.8 }, post: 4,
    sun: [0xffeccc, 2.3], hemi: [0xe8eaff, 0xa89070, 1.8] },
  { key: 'halftone', name: '漫畫網點（黑白）', refs: '原作漫畫、《Comic Jumper》',
    desc: '黑白印刷感，陰影用網點表現，黑色線條',
    mat: 'toon2', line: { on: true, t: 0.0045, c: [0, 0, 0], a: 1 }, post: 5,
    sun: [0xffffff, 2.6], hemi: [0xffffff, 0x888888, 1.3] },
  { key: 'lowpoly', name: '低多邊形扁平', refs: '《Monument Valley》《A Short Hike》',
    desc: '每個面單一顏色、無貼圖、無線條、粉嫩配色',
    mat: 'flat', line: { on: false }, post: 6,
    sun: [0xfff0e0, 2.4], hemi: [0xdde8ff, 0xb0a090, 1.9] },
  { key: 'pixel', name: '像素風 3D（HD-2D）', refs: '《Octopath Traveler》《A Short Hike》',
    desc: '低解析度像素、色彩分階、上下移軸模糊',
    mat: 'toon3', line: { on: true, t: 0.002, c: [0.15, 0.10, 0.10], a: 1 }, post: 7,
    sun: [0xffeedd, 2.4], hemi: [0xd9e8ff, 0x9a8a78, 1.7] },
  { key: 'spiderverse', name: '漫畫動態（新宇宙／Hi-Fi Rush）', refs: '《蜘蛛人：新宇宙》《Hi-Fi Rush》',
    desc: '高飽和、彩色網點、色版錯位、每秒 12 格的動畫感',
    mat: 'toon2', line: { on: true, t: 0.005, c: [0.02, 0.02, 0.05], a: 1 }, post: 8,
    sun: [0xfff2e0, 2.8], hemi: [0xd0e0ff, 0x806a8a, 1.6] },
];

function ramp(levels) {
  const data = new Uint8Array(levels.length * 4);
  levels.forEach((v, i) => data.set([v, v, v, 255], i * 4));
  const t = new THREE.DataTexture(data, levels.length, 1);
  t.minFilter = t.magFilter = THREE.NearestFilter; t.needsUpdate = true;
  return t;
}
const RAMPS = {
  toon2: ramp([110, 255]),
  toon3: ramp([105, 185, 255]),
  toon6: ramp([120, 150, 180, 205, 230, 255]),
};

const POST_FRAG = /* glsl */`
uniform sampler2D tDiffuse; uniform vec2 uRes; uniform int uStyle; uniform float uTime; uniform float uPR;
varying vec2 vUv;
float luma(vec3 c){ return dot(c, vec3(0.299,0.587,0.114)); }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),f.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x), f.y); }
vec3 toS(vec3 c){ return pow(max(c,0.), vec3(1./2.2)); }
vec3 toL(vec3 c){ return pow(max(c,0.), vec3(2.2)); }
vec3 sat(vec3 c, float s){ return mix(vec3(luma(c)), c, s); }
vec3 tapS(vec2 uv){ return toS(texture2D(tDiffuse, uv).rgb); }
float dots(vec2 fc, float cell, float ang, float amount){            // halftone dot mask (1 = ink)
  mat2 R = mat2(cos(ang), -sin(ang), sin(ang), cos(ang));
  vec2 p = R * fc / cell; vec2 f = fract(p) - 0.5;
  return step(length(f), sqrt(clamp(amount,0.,1.)) * 0.62);
}
void main(){
  vec2 px = 1.0 / uRes; vec2 fc = gl_FragCoord.xy / uPR;
  vec3 c = tapS(vUv);
  if (uStyle == 1) {                       // ghibli: bloom + warm grade + vignette
    vec3 b = vec3(0.);
    for (int i = 0; i < 12; i++) { float a = float(i) * 0.5236; for (int r = 1; r <= 2; r++) {
      vec3 s = tapS(vUv + vec2(cos(a), sin(a)) * px * float(r) * 6.0 * uPR); b += max(s - 0.72, 0.); } }
    c += b / 24.0 * 1.6;
    c = sat(c * vec3(1.05, 1.0, 0.9), 1.08);
    c *= 1.0 - 0.25 * pow(length(vUv - 0.5) * 1.3, 2.0);
  } else if (uStyle == 2) {                // moebius: diagonal hatching in shadows
    float l = luma(c);
    float h1 = step(0.5, fract((fc.x + fc.y) / 5.0));
    float h2 = step(0.5, fract((fc.x - fc.y) / 5.0));
    float ink = (l < 0.55 ? (1.0 - h1) : 0.0) * 0.55 + (l < 0.32 ? (1.0 - h2) : 0.0) * 0.55;
    c = sat(c, 0.85) * vec3(1.0, 0.98, 0.93);
    c = mix(c, vec3(0.08, 0.06, 0.05), clamp(ink, 0., 0.85));
  } else if (uStyle == 3) {                // sumi-e: stepped ink on rice paper
    float l = luma(c);
    float n = noise(fc * 0.9) * 0.6 + noise(fc * 0.08) * 0.4;
    l = floor((l + (n - 0.5) * 0.12) * 4.0 + 0.5) / 4.0;
    vec3 paper = vec3(0.95, 0.92, 0.85) * (0.94 + 0.06 * noise(fc * 0.3));
    c = mix(vec3(0.10, 0.09, 0.09), paper, clamp(l * 1.15, 0., 1.));
    if (luma(tapS(vUv)) > 0.85 && vUv.y > 0.45) c = mix(c, vec3(0.88, 0.3, 0.25), 0.0);
  } else if (uStyle == 4) {                // crayon picture book
    vec2 w = vec2(noise(fc * 0.05 + 3.1), noise(fc * 0.05 + 7.7)) - 0.5;
    c = tapS(vUv + w * px * 3.0 * uPR);
    float stroke = noise(vec2((fc.x + fc.y) * 0.9, (fc.x - fc.y) * 0.08));
    float grain = noise(fc * 0.7);
    c = floor(c * 7.0 + 0.5) / 7.0;
    c *= 0.86 + 0.14 * mix(stroke, grain, 0.5);
    c = mix(c, vec3(0.98, 0.95, 0.88), 0.08);
  } else if (uStyle == 5) {                // manga halftone, black & white
    float l = luma(c);
    float ink = dots(fc, 6.0, 0.785, 1.0 - l * 1.12);
    c = l < 0.12 ? vec3(0.03) : mix(vec3(0.99, 0.98, 0.96), vec3(0.04), ink);
  } else if (uStyle == 6) {                // low poly: candy colours
    c = sat(c, 1.18) * 1.04;
    c = floor(c * 10.0 + 0.5) / 10.0;
  } else if (uStyle == 7) {                // pixel HD-2D: pixelate + posterize + tilt shift
    float ps = 4.0 * uPR;
    vec2 uv = (floor(gl_FragCoord.xy / ps) * ps + ps * 0.5) / (uRes * uPR);
    float blur = smoothstep(0.25, 0.5, abs(vUv.y - 0.5));
    vec3 s = tapS(uv); vec3 acc = s;
    for (int i = 1; i <= 4; i++) { float o = float(i) * ps * blur / (uRes.y * uPR);
      acc += tapS(uv + vec2(0., o)) + tapS(uv - vec2(0., o)); }
    c = mix(s, acc / 9.0, blur);
    c = floor(sat(c, 1.15) * 12.0 + 0.5) / 12.0;
  } else if (uStyle == 8) {                // spider-verse: RGB misregistration + colour halftone
    vec2 off = px * 2.5 * uPR;
    c = vec3(tapS(vUv + off).r, c.g, tapS(vUv - off).b);
    float l = luma(c);
    float d = dots(fc, 7.0, 0.4, (0.6 - l) * 1.6);
    c = sat(c, 1.35);
    c = mix(c, c * vec3(0.35, 0.25, 0.6), d * 0.75);
  }
  gl_FragColor = vec4(toL(c), 1.0);
  #include <colorspace_fragment>
}`;

export function createStyler({ renderer, scene, camera, effect, sun, hemi }) {
  let current = 0, frame = 0;
  const size = new THREE.Vector2();
  const pr = () => renderer.getPixelRatio();
  renderer.getSize(size);
  const rt = new THREE.WebGLRenderTarget(size.x * pr(), size.y * pr(), { type: THREE.HalfFloatType, samples: 4 });
  const post = new THREE.ShaderMaterial({
    uniforms: { tDiffuse: { value: rt.texture }, uRes: { value: size.clone() }, uStyle: { value: 0 }, uTime: { value: 0 }, uPR: { value: pr() } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }',
    fragmentShader: POST_FRAG, depthTest: false, depthWrite: false,
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), post);
  const postScene = new THREE.Scene(); postScene.add(quad);
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const cache = new Map();
  const avg = new Map();
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const cx = cv.getContext('2d', { willReadFrequently: true });
  function avgColor(src) {           // flat colour of a textured material (for low-poly)
    if (avg.has(src)) return avg.get(src);
    const col = src.color.clone();
    if (src.map && src.map.image) {
      try { cx.drawImage(src.map.image, 0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data;
        col.multiply(new THREE.Color().setRGB(d[0] / 255, d[1] / 255, d[2] / 255, THREE.SRGBColorSpace)); } catch (e) { /* ignore */ }
    }
    avg.set(src, col); return col;
  }
  function materialFor(src, st) {
    const key = st.mat + '|' + src.uuid;
    if (!cache.has(key)) {
      const common = { transparent: src.transparent, opacity: src.opacity, side: src.side };
      let m;
      if (st.mat === 'flat') m = new THREE.MeshLambertMaterial({ ...common, color: avgColor(src), flatShading: true });
      else if (st.mat === 'lambert') m = new THREE.MeshLambertMaterial({ ...common, color: src.color, map: src.map });
      else m = new THREE.MeshToonMaterial({ ...common, color: src.color, map: src.map, gradientMap: RAMPS[st.mat] });
      if (m.map) m.map.colorSpace = THREE.SRGBColorSpace;
      if (src.transparent) m.depthWrite = false;
      m.userData.noLine = src.transparent || src.userData.toon_outline === 0;
      cache.set(key, m);
    }
    const m = cache.get(key);
    m.userData.outlineParameters = (!st.line.on || m.userData.noLine) ? { visible: false }
      : { visible: true, thickness: st.line.t, color: st.line.c, alpha: st.line.a };
    return m;
  }

  function apply(i, root) {
    current = ((i % STYLES.length) + STYLES.length) % STYLES.length;
    const st = STYLES[current];
    root.traverse((o) => { if (o.isMesh && o.userData._src) o.material = materialFor(o.userData._src, st); });
    sun.color.set(st.sun[0]); sun.intensity = st.sun[1];
    hemi.color.set(st.hemi[0]); hemi.groundColor.set(st.hemi[1]); hemi.intensity = st.hemi[2];
    post.uniforms.uStyle.value = st.post;
    return st;
  }

  function resize(w, h) {
    rt.setSize(w * pr(), h * pr());
    post.uniforms.uRes.value.set(w, h);
    post.uniforms.uPR.value = pr();
  }

  function render(t) {
    frame++;
    // "animated on twos": the comic-motion style only refreshes every other frame (≈12–15 fps feel)
    if (STYLES[current].key === 'spiderverse' && frame % 2) return;
    post.uniforms.uTime.value = t;
    renderer.setRenderTarget(rt);
    effect.render(scene, camera);
    renderer.setRenderTarget(null);
    renderer.render(postScene, postCam);
  }

  return { apply, resize, render, get index() { return current; } };
}
