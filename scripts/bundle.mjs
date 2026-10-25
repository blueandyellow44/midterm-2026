import { readFileSync, readdirSync, lstatSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { parse } from 'csv-parse/sync';

export const allowedFiles = new Set(['polls.csv','pollsters.csv','exclusions.csv','heat.csv','coverage.csv','backtest-2025.csv','midterm-2026-poll-weighting.md','derived.json','predictions.csv','results.csv']);
export const supportedSchemas = { polls:['1.2'], pollsters:['1.0'], exclusions:['1.0'], heat:['1.0'], coverage:['1.0'], backtest:['1.2'], predictions:['1.0'], results:['1.0'] };
export const sha256 = value => createHash('sha256').update(value).digest('hex');
/** @returns {Record<string,string>[]} */
export function readCsv(text, required = []) {
  if (typeof text !== 'string' || !text.trim()) throw new Error('CSV input is empty');
  const rows = parse(text, { columns: headers => {
    if (new Set(headers).size !== headers.length) throw new Error('Duplicate CSV columns');
    for (const col of required) if (!headers.includes(col)) throw new Error(`Missing CSV column: ${col}`);
    return headers;
  }, bom: true, skip_empty_lines: true, relax_column_count: false });
  return rows;
}
export function validateBundle(directory) {
  const manifestBytes = readFileSync(join(directory,'manifest.json'));
  const m = JSON.parse(manifestBytes);
  if (m.bundle_schema !== '1.0' || !m.release_id || !m.analytical_as_of) throw new Error('Unsupported or missing manifest identity');
  for (const [key, versions] of Object.entries(supportedSchemas)) {
    if (!versions.includes(m.csv_schemas?.[key])) throw new Error(`Unsupported CSV schema: ${key}`);
  }
  if (Object.keys(m.csv_schemas).some(k=>!(k in supportedSchemas))) throw new Error('Unknown CSV schema');
  if (!Array.isArray(m.files) || !m.files.length) throw new Error('Empty manifest file list');
  const names = m.files.map(f=>f.path);
  if (new Set(names).size !== names.length) throw new Error('Duplicate manifest paths');
  const expected = new Set(['manifest.json',...names]);
  for (const name of readdirSync(directory)) {
    if (!expected.has(name) || !lstatSync(join(directory,name)).isFile()) throw new Error(`Unexpected bundle entry: ${name}`);
  }
  for (const entry of m.files) {
    if (!allowedFiles.has(entry.path)) throw new Error(`Forbidden bundle file: ${entry.path}`);
    const p=join(directory,entry.path);
    if (!lstatSync(p).isFile() || lstatSync(p).isSymbolicLink()) throw new Error('Bundle links prohibited');
    const bytes=readFileSync(p);
    if (sha256(bytes)!==entry.sha256 || bytes.length!==entry.bytes) throw new Error(`Bundle integrity mismatch: ${entry.path}`);
    if (entry.path.endsWith('.csv')) {
      const required=entry.path==='polls.csv'?['estimate_id','race','selected','recall_weighted']:entry.path==='pollsters.csv'?['pollster_id','method_id']:[];
      if (readCsv(bytes.toString('utf8'),required).length!==entry.rows) throw new Error(`CSV row count mismatch: ${entry.path}`);
    }
  }
  for (const name of ['derived.json','polls.csv','pollsters.csv','heat.csv','coverage.csv','exclusions.csv','midterm-2026-poll-weighting.md']) if (!names.includes(name)) throw new Error(`Required bundle file missing: ${name}`);
  const d=JSON.parse(readFileSync(join(directory,'derived.json'),'utf8'));
  if (d.derived_schema!=='1.0' || d.release_id!==m.release_id || d.analytical_as_of!==m.analytical_as_of || d.calc_version!==m.calc_version.commit) throw new Error('Mixed derived/manifest identity');
  if (!d.stage2c_passed && Object.values(d.races).some(r=>r.weighted_margin!==null)) throw new Error('Premature weighted margin');
  return { manifest:m, derived:d, manifestHash:sha256(manifestBytes) };
}
