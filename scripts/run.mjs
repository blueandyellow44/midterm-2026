import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
const state=JSON.parse(readFileSync('/Users/maxsheahan/Second Brain V2/Resources/methods/midterm-2026/run-state.json','utf8'));
if(process.env.RESUME_FROM!=='stageW')throw new Error('This code-stage runner requires RESUME_FROM=stageW; data stages resume from the saved prompt and run-state.');
if(process.env.ANALYTICAL_AS_OF!==state.analytical_as_of)throw new Error('ANALYTICAL_AS_OF must match run-state; create a new analytical release before changing the cutoff.');
const r=spawnSync('npm',['run','build:cloudflare'],{stdio:'inherit'});
if(r.error)throw r.error;
if(r.status)process.exit(r.status);
console.log('Production build ready. Serve with npm run preview, then perform the required real-Chrome checks and record local_handoff before deployment.');
