import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { useEffect, useRef, useState } from 'react';

export function GltfGarage({ file, accent }: { file: string; accent: string }) {
  const host = useRef<HTMLDivElement>(null); const [status, setStatus] = useState('Loading showroom model...');
  useEffect(() => { const node = host.current; if (!node) return; const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(40, 1, .1, 100); camera.position.set(5.5, 3.1, 6.5); const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.domElement.style.cssText = 'display:block;width:100%;height:100%;touch-action:none'; node.appendChild(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement); controls.target.set(0, .7, 0); controls.enableDamping = true; controls.enablePan = false; controls.minDistance = 3.2; controls.maxDistance = 11; controls.minPolarAngle = .45; controls.maxPolarAngle = 1.45;
    scene.add(new THREE.HemisphereLight(0xeaf6ff, 0x0c101b, 3.4)); const key = new THREE.DirectionalLight(0xffffff, 4); key.position.set(5, 7, 4); scene.add(key); const accentLight = new THREE.PointLight(new THREE.Color(accent), 34, 13); accentLight.position.set(-3, 2.5, 2); scene.add(accentLight);
    const floor = new THREE.Mesh(new THREE.CircleGeometry(4.9, 64), new THREE.MeshStandardMaterial({ color: 0x111c2c, metalness: .7, roughness: .3 })); floor.rotation.x = -Math.PI / 2; scene.add(floor); const grid = new THREE.GridHelper(9, 18, 0x4d6585, 0x23334d); grid.position.y = .012; scene.add(grid);
    const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder); let model: THREE.Object3D | null = null; loader.load(file, gltf => { model = gltf.scene; const box = new THREE.Box3().setFromObject(model); const size = box.getSize(new THREE.Vector3()); const scale = 4.1 / Math.max(size.x, size.y, size.z, .001); model.scale.setScalar(scale); const centered = new THREE.Box3().setFromObject(model); const center = centered.getCenter(new THREE.Vector3()); model.position.sub(center); const grounded = new THREE.Box3().setFromObject(model); model.position.y -= grounded.min.y; scene.add(model); setStatus('Drag to inspect · scroll to zoom'); }, undefined, () => setStatus('This garage asset could not be loaded.'));
    let frame = 0; const draw = () => { frame = requestAnimationFrame(draw); const width = Math.max(node.clientWidth, 1); const height = Math.max(node.clientHeight, 1); renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix(); if (model) model.rotation.y += .003; controls.update(); renderer.render(scene, camera); }; draw(); return () => { cancelAnimationFrame(frame); controls.dispose(); renderer.dispose(); node.replaceChildren(); };
  }, [accent, file]);
  return <div className="gltf-garage" ref={host}><span>{status}</span></div>;
}
