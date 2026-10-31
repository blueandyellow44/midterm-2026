import { readFileSync, mkdtempSync, cpSync, renameSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { allowedFiles, validateBundle } from './bundle.mjs';
const id=process.argv[2];
if (!id || !/^[A-Za-z0-9_-]+$/.test(id)) throw new Error('Invalid release ID');
const source=join('/Users/maxsheahan/Second Brain V2/Resources/methods/midterm-2026/releases',id);
const m=JSON.parse(readFileSync(join(source,'manifest.json'),'utf8'));
if (m.release_id!==id || !Array.isArray(m.files)) throw new Error('Release identity mismatch');
const temp=mkdtempSync(resolve('.bundle-'));
try {
  for (const entry of m.files) {
    if (!allowedFiles.has(entry.path)) throw new Error(`File outside public allowlist: ${entry.path}`);
    cpSync(join(source,entry.path),join(temp,entry.path),{dereference:false,errorOnExist:true,force:false});
  }
  cpSync(join(source,'manifest.json'),join(temp,'manifest.json'));
  validateBundle(temp);
  // Stage 3 (audit 2026-10-31): once the site carries a frozen release (predictions.csv), a release without one cannot
  // replace it, so a refresh after the freeze cannot change what gets graded. Override only with --unfreeze, on Max's word.
  if (existsSync(join('data','predictions.csv')) && !existsSync(join(temp,'predictions.csv')) && !process.argv.includes('--unfreeze')) throw new Error('data/ carries a frozen release (predictions.csv); refusing to replace it with an unfrozen one (pass --unfreeze only on Max\'s word)');
  if (existsSync('data')) { mkdirSync('.backups',{recursive:true});renameSync('data',join('.backups',`data-${Date.now()}`)); }
  renameSync(temp,'data');
  console.log(`Synced and verified ${id}`);
} catch(error) { rmSync(temp,{recursive:true,force:true});throw error; }
