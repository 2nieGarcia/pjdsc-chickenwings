import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { gsap } from 'gsap';

const TIER = { act_now: '#d6322b', prepare: '#f2a33a', monitor: '#86c5e8' };
const STANDBY = '#aeb4bd';
const GROUND = '#e4e5e1';
const PLATE = '#cfd1ca';
const DIM = new THREE.Color('#c3c6c9');
const UNIT = 100; // metres per scene unit
const CRATE_W = 3.2;
const CRATE_H = 1.5;
const PLATE_H = 0.5;
const MAX_CRATES = 8;
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

const rings = (g) => (g.type === 'Polygon' ? [g.coordinates[0]] : g.coordinates.map((p) => p[0]));

// banyera crate side: blue polymer, three deep ribs and a hand slot, sized to read at ~40px on screen
function crateTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#2f68e6';
  g.fillRect(0, 0, 128, 128);
  g.fillStyle = '#1f4fbf';
  for (const y of [44, 72, 100]) g.fillRect(12, y, 104, 14);
  g.fillStyle = '#0a1d52';
  g.fillRect(30, 10, 68, 20);
  g.strokeStyle = '#163a8f';
  g.lineWidth = 8;
  g.strokeRect(4, 4, 120, 120);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

function centroid(ring) {
  let a = 0, x = 0, y = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [x0, y0] = ring[i], [x1, y1] = ring[i + 1];
    const c = x0 * y1 - x1 * y0;
    a += c; x += (x0 + x1) * c; y += (y0 + y1) * c;
  }
  return Math.abs(a) < 1e-9 ? ring[0] : [x / (3 * a), y / (3 * a)];
}

export function createCity(canvas, labelsEl, geojson, { onSelect }) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(GROUND);
  scene.add(new THREE.HemisphereLight('#ffffff', '#d2cdc1', 2.8));

  // equirectangular projection around the city's mean point, in 100 m units; north = -z
  const all = geojson.features.flatMap((f) => rings(f.geometry).flat());
  const lon0 = all.reduce((s, p) => s + p[0], 0) / all.length;
  const lat0 = all.reduce((s, p) => s + p[1], 0) / all.length;
  const kx = (111320 * Math.cos((lat0 * Math.PI) / 180)) / UNIT;
  const ky = 110540 / UNIT;
  const P = ([lon, lat]) => [(lon - lon0) * kx, (lat - lat0) * ky];

  const plateMat = new THREE.MeshLambertMaterial({ color: PLATE });
  const edgeMat = new THREE.LineBasicMaterial({ color: '#9ea39a' });
  const waterMat = new THREE.MeshLambertMaterial({ color: '#86c5e8', transparent: true, opacity: 0.55, depthWrite: false });
  const waterEdge = new THREE.LineBasicMaterial({ color: '#2f7fb8', transparent: true, opacity: 0.9 });
  const side = crateTexture();
  const box = new THREE.BoxGeometry(CRATE_W, CRATE_H, CRATE_W);
  box.translate(0, CRATE_H / 2, 0);

  const stacks = new Map();
  const pickables = [];
  const bounds = new THREE.Box3();
  const groundPts = [];

  for (const f of geojson.features) {
    const id = f.properties.psgc10;
    const flat = rings(f.geometry).map((r) => r.map(P));
    const shapes = flat.map((r) => new THREE.Shape(r.map(([x, y]) => new THREE.Vector2(x, y))));
    const geo = new THREE.ExtrudeGeometry(shapes, { depth: PLATE_H, bevelEnabled: false });
    geo.rotateX(-Math.PI / 2);
    const plate = new THREE.Mesh(geo, plateMat);
    plate.receiveShadow = true;
    plate.userData.id = id;
    scene.add(plate, new THREE.LineSegments(new THREE.EdgesGeometry(geo, 20), edgeMat));
    pickables.push(plate);
    geo.computeBoundingBox();
    bounds.union(geo.boundingBox);
    flat.flat().forEach(([x, y]) => groundPts.push(new THREE.Vector3(x, 0, -y)));

    // flood water inside this barangay's own outline, with a hard waterline; depth set per replay week
    const slab = new THREE.Mesh(geo, waterMat);
    slab.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 20), waterEdge));
    slab.position.y = PLATE_H + 0.02; // clear of the plate top so a dry slab never z-fights it
    slab.visible = false;
    slab.scale.y = 0.001;
    slab.renderOrder = 2;
    scene.add(slab);

    const biggest = flat.reduce((a, b) => (b.length > a.length ? b : a));
    const [cx, cy] = centroid(biggest);
    const sideMat = new THREE.MeshLambertMaterial({ map: side });
    const lidMat = new THREE.MeshLambertMaterial({ color: STANDBY });
    const group = new THREE.Group();
    group.position.set(cx, PLATE_H, -cy);
    const crates = [];
    for (let i = 0; i < MAX_CRATES; i++) {
      const crate = new THREE.Mesh(box, [sideMat, sideMat, sideMat, sideMat, sideMat, sideMat]);
      crate.position.y = i * CRATE_H;
      crate.scale.y = 0.0001;
      crate.visible = false;
      crate.castShadow = true;
      crate.userData.id = id;
      group.add(crate);
      crates.push(crate);
      pickables.push(crate);
    }
    scene.add(group);
    stacks.set(id, { id, group, crates, sideMat, lidMat, slab, hazard: 1, n: 1, tier: 'monitor', dim: { t: 0 } });
  }

  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());

  // low dawn sun from the bay side, so stacks throw contact shadows across the concrete
  const sun = new THREE.DirectionalLight('#fff1d9', 1.5);
  sun.position.set(center.x - 40, 50, center.z + 30);
  sun.target.position.copy(center);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const r = Math.max(size.x, size.z) * 0.75;
  Object.assign(sun.shadow.camera, { left: -r, right: r, top: r, bottom: -r, near: 1, far: 200 });
  sun.shadow.bias = -0.0005;
  scene.add(sun, sun.target);

  // looking along the strip: azimuth puts north-west (Tanza) to the right
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -500, 500);
  const az = THREE.MathUtils.degToRad(142), el = THREE.MathUtils.degToRad(44);
  camera.position.set(center.x + Math.sin(az) * Math.cos(el) * 100, Math.sin(el) * 100, center.z + Math.cos(az) * Math.cos(el) * 100);
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(center);
  controls.enableDamping = !reduce;
  controls.enablePan = false;
  controls.minZoom = 0.8;
  controls.maxZoom = 3;
  controls.minPolarAngle = THREE.MathUtils.degToRad(30);
  controls.maxPolarAngle = THREE.MathUtils.degToRad(66);
  controls.minAzimuthAngle = az - 0.6;
  controls.maxAzimuthAngle = az + 0.6;

  // frame the ground outline plus the current stack tops and label room, so the strip fills the stage
  function fit() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.updateMatrixWorld();
    const inv = camera.matrixWorldInverse;
    const tops = [...stacks.values()].map((s) => s.group.position.clone().setY(PLATE_H + (s.n + 1.6) * CRATE_H));
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const p of [...groundPts, ...tops]) {
      const q = p.clone().applyMatrix4(inv);
      minX = Math.min(minX, q.x); maxX = Math.max(maxX, q.x); minY = Math.min(minY, q.y); maxY = Math.max(maxY, q.y);
    }
    const pad = 1.04, cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    let hw = ((maxX - minX) / 2) * pad, hh = ((maxY - minY) / 2) * pad;
    if (hw / hh > w / h) hh = hw / (w / h); else hw = hh * (w / h);
    Object.assign(camera, { left: cx - hw, right: cx + hw, top: cy + hh, bottom: cy - hh, zoom: 1 });
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(fit).observe(canvas);

  // act-now labels and place names as DOM, projected every frame
  const labels = [];
  function label(text, anchor, cls, rank) {
    const el = document.createElement('span');
    el.className = cls;
    if (rank) el.innerHTML = `<b>${rank}</b><span></span>`;
    (rank ? el.querySelector('span') : el).textContent = text;
    labelsEl.append(el);
    // leaders live in their own layer under every label box, so a leader never crosses another label's text
    const ld = cls === 'lb' ? labelsEl.insertBefore(Object.assign(document.createElement('i'), { className: 'ld' }), labelsEl.firstChild) : null;
    labels.push({ el, anchor, ld });
    return el;
  }
  const at = (id, dx, dz) => { const g = stacks.get(id)?.group.position; return g && new THREE.Vector3(g.x + dx, 0, g.z + dz); };
  const bay = at('1380900013', -30, 0); // west of Tangos South: Manila Bay
  const malabon = at('1380900010', 10, 2); // east of San Jose: Malabon
  if (bay) label('Manila Bay', bay, 'place');
  if (malabon) label('Malabon', malabon, 'place');

  const v = new THREE.Vector3();
  function placeLabels() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    const placed = labels.map((l) => {
      v.copy(typeof l.anchor === 'function' ? l.anchor() : l.anchor).project(camera);
      return { ...l, x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h };
    });
    // close neighbours alternate leader height and side so no leader crosses another label
    let prevX = -Infinity, k = 0;
    for (const p of placed.filter((q) => q.el.classList.contains('lb')).sort((a, b) => a.x - b.x)) {
      k = p.x - prevX < 150 ? k + 1 : 0;
      prevX = p.x;
      p.dy = 26 + (k % 2) * 34;
      p.el.style.setProperty('--dy', `${p.dy}px`);
      p.el.classList.toggle('flip', k % 2 === 1);
    }
    for (const p of placed) {
      p.el.style.translate = `${p.x}px ${p.y}px`;
      if (p.ld) { p.ld.style.translate = `${p.x}px ${p.y - p.dy}px`; p.ld.style.height = `${p.dy}px`; }
    }
  }

  let selected = null;
  let alert = false;
  const lidColor = (s) => new THREE.Color(alert ? TIER[s.tier] : STANDBY);
  function paint(s) {
    s.sideMat.color.copy(new THREE.Color('#ffffff').lerp(DIM, s.dim.t));
    s.lidMat.color.copy(lidColor(s).lerp(DIM, s.dim.t));
  }
  function setDim(s, on) {
    gsap.to(s.dim, { t: on ? 1 : 0, duration: reduce ? 0 : 0.4, ease: 'expo.out', onUpdate: () => paint(s) });
  }
  function refreshLabels() {
    for (const l of labels) {
      if (!l.el.classList.contains('lb')) continue;
      l.el.hidden = l.ld.hidden = !alert;
      const dim = Boolean(selected) && l.el.dataset.id !== selected;
      l.el.classList.toggle('dim', dim);
      l.ld.classList.toggle('dim', dim);
    }
  }

  function select(id) {
    selected = id === selected ? null : id;
    for (const s of stacks.values()) {
      const lift = selected === s.id;
      gsap.to(s.group.position, { y: PLATE_H + (lift ? 1.4 : 0), duration: reduce ? 0 : 0.6, ease: 'expo.out' });
      setDim(s, Boolean(selected) && !lift);
    }
    refreshLabels();
    onSelect?.(selected);
  }

  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
  let downAt = null;
  const hit = (e) => {
    const rect = canvas.getBoundingClientRect();
    ptr.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    ray.setFromCamera(ptr, camera);
    return ray.intersectObjects(pickables, false).find((i) => i.object.visible)?.object.userData.id ?? null;
  };
  canvas.addEventListener('pointermove', (e) => canvas.classList.toggle('hover', Boolean(hit(e))));
  canvas.addEventListener('pointerdown', (e) => { downAt = [e.clientX, e.clientY]; });
  canvas.addEventListener('pointerup', (e) => {
    if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 5) return; // a drag rotated the view
    const id = hit(e);
    if (id) select(id);
  });

  gsap.ticker.add(() => {
    controls.update();
    renderer.render(scene, camera);
    placeLabels();
  });

  return {
    setIndex(rows, { intro = false } = {}) {
      labels.filter((l) => l.el.classList.contains('lb')).forEach((l) => { l.el.remove(); l.ld.remove(); labels.splice(labels.indexOf(l), 1); });
      [...rows].sort((a, b) => a.rank - b.rank).forEach((row, order) => {
        const s = stacks.get(row.psgc10);
        if (!s) return;
        s.tier = row.tier;
        s.hazard = row.hazard;
        paint(s);
        const n = Math.max(1, Math.min(MAX_CRATES, Math.round(row.score)));
        s.crates.forEach((c, i) => {
          const on = i < n;
          c.material = [s.sideMat, s.sideMat, i === n - 1 ? s.lidMat : s.sideMat, s.sideMat, s.sideMat, s.sideMat];
          if (on) c.visible = true;
          gsap.to(c.scale, {
            y: on ? 1 : 0.0001, duration: reduce ? 0 : 0.7, ease: 'expo.out',
            delay: reduce ? 0 : (intro ? order * 0.05 : 0) + i * 0.04,
            onComplete: () => { c.visible = on; },
          });
        });
        s.n = n;
        if (row.tier === 'act_now') {
          const el = label(row.name, () => s.group.position.clone().setY(s.group.position.y + s.n * CRATE_H + 0.9), 'lb', row.rank);
          el.dataset.id = row.psgc10;
        }
      });
      refreshLabels();
      fit();
    },
    // the index is a standing priority; tier colours and act-now labels show only while the week is on alert
    setAlert(on) {
      if (on === alert) return;
      alert = on;
      for (const s of stacks.values()) {
        const from = s.lidMat.color.clone();
        const to = lidColor(s).lerp(DIM, s.dim.t);
        const t = { k: 0 };
        gsap.to(t, { k: 1, duration: reduce ? 0 : 0.5, ease: 'expo.out', onUpdate: () => s.lidMat.color.copy(from.clone().lerp(to, t.k)) });
      }
      refreshLabels();
    },
    // level 0..1 for the city; each barangay floods in proportion to its hazard component (1..10)
    setWater(level) {
      for (const s of stacks.values()) {
        const depth = level * 6 * (s.hazard / 10);
        if (depth > 0.02) s.slab.visible = true;
        gsap.to(s.slab.scale, { y: Math.max(0.001, depth), duration: reduce ? 0 : 1.4, ease: 'expo.out', onComplete: () => { s.slab.visible = depth > 0.02; } });
      }
    },
    select,
    get selected() { return selected; },
  };
}
