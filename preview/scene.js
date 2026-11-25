import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

export default function attach(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0xc5c0b8, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 100);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.autoRotate = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  controls.autoRotateSpeed = 0.85;

  scene.add(new THREE.AmbientLight(0xfff6ea, 0.55));
  const key = new THREE.DirectionalLight(0xfff8f0, 2.6);
  key.position.set(3.2, 6.4, 4.2);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xd5def2, 0.65);
  fill.position.set(-4.2, 2.4, -2.5);
  scene.add(fill);

  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(1, 64),
    new THREE.MeshStandardMaterial({ color: 0xb7b1a8, roughness: 1, metalness: 0 }),
  );
  ground.rotation.x = -Math.PI / 2;
  scene.add(ground);

  const loader = new GLTFLoader();
  let current = null;

  function resize() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) {
      return;
    }
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  new ResizeObserver(resize).observe(canvas.parentElement);
  resize();

  function frame(object) {
    const box = new THREE.Box3().setFromObject(object);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const radius = Math.max(size.length() * 0.5, 0.001);
    const fov = (camera.fov * Math.PI) / 180;
    const distance = (radius / Math.sin(fov / 2)) * 1.08;
    const direction = new THREE.Vector3(0.62, 0.4, 0.78).normalize();
    camera.position.copy(center).addScaledVector(direction, distance);
    camera.near = Math.max(distance / 80, 0.01);
    camera.far = distance * 20;
    camera.updateProjectionMatrix();
    controls.target.copy(center);
    controls.update();
    ground.scale.setScalar(Math.max(Math.max(size.x, size.z) * 0.78, 0.25));
    ground.position.y = box.min.y;
  }

  function disposeCurrent() {
    if (!current) {
      return;
    }
    scene.remove(current);
    current.traverse((node) => {
      if (!node.isMesh) {
        return;
      }
      node.geometry.dispose();
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      for (const material of materials) {
        material.dispose();
      }
    });
    current = null;
  }

  async function load(url, flat) {
    const gltf = await loader.loadAsync(url);
    disposeCurrent();
    current = gltf.scene;
    current.traverse((node) => {
      if (!node.isMesh) {
        return;
      }
      node.material.flatShading = flat;
      node.material.needsUpdate = true;
    });
    scene.add(current);
    frame(current);
  }

  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
  });

  return { load };
}
