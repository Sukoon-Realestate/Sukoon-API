#!/usr/bin/env node
import fs from 'node:fs';
import RAPIER from '@dimforge/rapier3d-compat';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// Runs in a bounded worker subprocess. Input and file paths never reach logs.
try {
  await RAPIER.init();
  const bytes = fs.readFileSync(process.argv[2]);
  const { spawns } = JSON.parse(fs.readFileSync(0, 'utf8'));
  const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  const world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(node => {
    if (!(node instanceof THREE.Mesh)) return;
    const geometry = node.geometry.clone().applyMatrix4(node.matrixWorld);
    const position = geometry.getAttribute('position');
    const vertices = new Float32Array(position.count * 3);
    for (let i = 0; i < position.count; i++) vertices.set([position.getX(i), position.getY(i), position.getZ(i)], i * 3);
    const indices = geometry.index ? Uint32Array.from(geometry.index.array) : Uint32Array.from({ length: position.count }, (_, i) => i);
    world.createCollider(RAPIER.ColliderDesc.trimesh(vertices, indices)); geometry.dispose();
  });
  world.step();
  for (const spawn of spawns) {
    const [x, y, z] = spawn.foot_position_m;
    let intersects = false;
    world.intersectionsWithShape({ x, y: y + .875 + .02, z }, { x: 0, y: 0, z: 0, w: 1 }, new RAPIER.Capsule(.625, .25), () => { intersects = true; return false; });
    if (intersects) throw new Error('spawn_obstructed');
    const ground = world.castRayAndGetNormal(new RAPIER.Ray({ x, y: y + .2, z }, { x: 0, y: -1, z: 0 }), .3, true);
    if (!ground || Math.abs(ground.timeOfImpact - .2) > .06 || ground.normal.y < .7) throw new Error('spawn_ungrounded');
  }
  world.free(); process.stdout.write(JSON.stringify({ valid_spawns: spawns.length }));
} catch (error) {
  process.stderr.write(['spawn_obstructed', 'spawn_ungrounded'].includes(error.message) ? error.message : 'collision_validation_failed');
  process.exitCode = 1;
}
