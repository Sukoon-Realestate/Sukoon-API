#!/usr/bin/env node
const fs = require('node:fs');
const validator = require('gltf-validator');
(async () => {
  const result = await validator.validateBytes(new Uint8Array(fs.readFileSync(process.argv[2])), {
    maxIssues: 100, externalResourceFunction: () => Promise.reject(new Error('External resources forbidden')),
  });
  process.stdout.write(JSON.stringify({ errors: result.issues.numErrors, warnings: result.issues.numWarnings }));
  process.exitCode = result.issues.numErrors ? 1 : 0;
})().catch(() => { process.stderr.write('GLB validation failed'); process.exitCode = 1; });
