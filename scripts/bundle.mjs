import { readFileSync, readdirSync, lstatSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { parse } from 'csv-parse/sync';

export const allowedFiles = new Set(['polls.csv','pollsters.csv','exclusions.csv','heat.csv','coverage.csv','backtest-2025.csv','midterm-2026-poll-weighting.md','derived.json','predictions.csv','results.csv','spending.csv','fundamentals.csv','spend-history.csv','state-poll-error.csv','poll-error-history.csv','early-vote.csv','recent-misses.csv','early-vote-history.csv','house-races.csv','seats.csv','generic-ballot.csv']);
export const supportedSchemas = { polls:['1.2'], pollsters:['1.0'], exclusions:['1.0'], heat:['1.0'], coverage:['1.0'], backtest:['1.2'], predictions:['1.0','1.1'], results:['1.0'], spending:['1.0'], fundamentals:['1.0'], spend_history:['1.0'], state_poll_error:['1.0'], poll_error_history:['1.0'], early_vote:['1.0'], recent_misses:['1.0'], early_vote_history:['1.0'], house_races:['1.0'], seats:['1.0'], generic_ballot:['1.0'] };
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
  // Schemas added after a release was sealed are optional, so earlier immutable releases stay valid.
  const optional = new Set(['house_races','seats','generic_ballot']);
  for (const [key, versions] of Object.entries(supportedSchemas)) {
    if (optional.has(key) && m.csv_schemas?.[key] === undefined) continue;
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
  if (d.stage2c_passed && (m.stage_status.stage2c!=='PASSED' || Object.values(d.races).some(r=>r.retained_count>0 && !Number.isFinite(r.weighted_margin)))) throw new Error('Missing or unpassed weighted margin');
  // Older sealed releases remain readable. New public-read releases must be complete.
  if (Object.values(d.races).some(r=>r.polling_read!==undefined)) {
    const estimates=new Map(d.estimates.map(e=>[e.estimate_id,e]));
    for (const r of Object.values(d.races)) {
      const read=r.polling_read;
      if (!read || !['WEIGHTED_AVERAGE','LATEST_POLL','UNAVAILABLE'].includes(read.kind)) throw new Error('Missing or unknown public polling read');
      if (read.kind==='UNAVAILABLE') {
        if (read.margin!==null || read.poll_count!==0) throw new Error('Unavailable public read has a value');
      } else if (!Number.isFinite(read.margin) || !Number.isInteger(read.age_days) || read.age_days<0) throw new Error('Invalid public polling read');
      if (read.kind==='WEIGHTED_AVERAGE' && (read.margin!==r.weighted_margin || read.poll_count!==r.retained_count)) throw new Error('Public average disagrees with calculator');
      if (read.kind==='LATEST_POLL') {
        const e=estimates.get(read.latest_poll?.estimate_id);
        if (r.weighted_margin!==null || read.poll_count!==1 || !e || !e.flags.principal || e.quarantined || e.primary_verified!=='YES' || e.window!=='BOTH' || !['NA','FIRST','FINAL'].includes(e.round) || e.race!==r.race || e.margin!==read.margin || e.source_url!==read.latest_poll.source_url || e.pop!==read.stratum?.pop || e.round!==read.stratum?.round || e.denominator_class!==read.stratum?.denominator_class || e.field_end!==read.field_end) throw new Error('Unverified or inconsistent latest-poll read');
      }
    }
  }
  // The signal-adjusted reading is optional (older releases lack it) but must be internally consistent when present.
  if (d.signals) {
    for (const [race,s] of Object.entries(d.signals.per_race ?? {})) {
      const read=d.races[race]?.polling_read;
      if (!read) throw new Error(`Signal reading for an unknown race: ${race}`);
      if (s.polling_margin!==read.margin) throw new Error(`Signal reading starts from a different polling number: ${race}`);
      if (s.adjusted_margin===null) { if (read.margin!==null) throw new Error(`Signal reading missing: ${race}`); continue; }
      if (!Number.isFinite(s.adjusted_margin) || Math.abs(s.adjusted_margin-(read.margin+s.delta_total))>0.001 || Math.abs(s.delta_total-(s.delta_spending+s.delta_rhetoric+(s.delta_polling_error??0)+(s.delta_early_vote??0)+(s.delta_partisan??0)))>0.001) throw new Error(`Signal arithmetic inconsistent: ${race}`);
      if (!['ALIGNED','OPPOSED','SPENDING_ONLY','RHETORIC_ONLY','NO_SIGNAL','WITNESS'].includes(s.alignment)) throw new Error(`Unknown signal alignment: ${race}`);
      if (s.alignment==='NO_SIGNAL' && Math.abs(s.delta_total-(s.delta_polling_error??0)-(s.delta_early_vote??0)-(s.delta_partisan??0))>0.001) throw new Error(`No-signal race was adjusted: ${race}`);
    }
  }
  // The full-chamber projection is optional (older releases lack it); when present every seat has a side or is marked undecided,
  // projections equal their stated parts, readings equal the signal reading, and the counts add up to the chamber.
  if (d.chambers) {
    const nat=Number(d.signals?.rules?.poll_error_toward_d);
    for (const [ch,c] of Object.entries(d.chambers.chambers)) {
      if (c.items.length!==c.seats || !{SEN:100,GOV:50,HOUSE:435}[ch] || c.seats!=={SEN:100,GOV:50,HOUSE:435}[ch]) throw new Error(`Chamber ${ch} seat count wrong`);
      let dd=0, rr=0, un=0;
      for (const i of c.items) {
        if (!['not_up','reading','projection','rated'].includes(i.kind)) throw new Error(`Unknown seat kind: ${i.seat}`);
        if (i.kind==='reading') { if (!i.graded) throw new Error(`Seat reading not graded: ${i.seat}`); const s=d.signals?.per_race?.[i.race]; if (d.signals && (!s || s.adjusted_margin!==i.undertow)) throw new Error(`Seat reading disagrees with the signal reading: ${i.seat}`); }
        if (i.kind==='projection') { const p=i.parts; if (i.graded || Math.abs(i.undertow-(i.base+p.national_lean+p.state_adjustment+p.spending+p.early_vote))>0.001 || (d.signals && Math.abs(p.national_lean-nat)>0.001)) throw new Error(`Projection arithmetic inconsistent: ${i.seat}`); }
        if (i.kind==='rated' && (i.undertow!==null || i.graded)) throw new Error(`Rated seat carries a number: ${i.seat}`);
        if (i.side==='D') dd++; else if (i.side==='R') rr++; else if (i.side===null) un++; else throw new Error(`Bad side: ${i.seat}`);
      }
      if (dd!==c.at_bet.D || rr!==c.at_bet.R || un!==c.at_bet.undecided || dd+rr+un!==c.seats) throw new Error(`Chamber ${ch} tally does not add up`);
    }
  }
  // Alternative models (Max, 2026-10-29): optional; when present each model carries a center for every seat up, its up-seat
  // counts match its centers, and its dial grid has one odds value per dial step for every chamber with a majority line.
  if (d.models) {
    const up=new Set(); for (const c of Object.values(d.chambers?.chambers||{})) for (const i of c.items) if (i.kind!=='not_up') up.add(i.race||i.seat);
    for (const [k,mo] of Object.entries(d.models.models)) {
      const ids=Object.keys(mo.centers||{});
      if (ids.length!==up.size || ids.some(id=>!up.has(id))) throw new Error(`Model ${k}: centers do not cover the seats up`);
      for (const [ch,c] of Object.entries(mo.up_at_default)) { let dd=0,rr=0,un=0; for (const cc of Object.values(d.chambers.chambers[ch].items.filter(i=>i.kind!=='not_up').map(i=>mo.centers[i.race||i.seat]))) { if (cc>=0.05) dd++; else if (cc<=-0.05) rr++; else un++; } if (dd!==c.D||rr!==c.R||un!==c.undecided) throw new Error(`Model ${k}: ${ch} counts disagree with centers`); }
      const g=mo.simulation?.dial; if (!g || !Array.isArray(g.values)) throw new Error(`Model ${k}: no dial grid`);
      for (const [ch,arr] of Object.entries(g.chambers)) if (arr.length!==g.values.length) throw new Error(`Model ${k}: ${ch} grid length`);
      if (typeof mo.default_dial!=='number' || !(mo.national_sd>0)) throw new Error(`Model ${k}: dial or spread missing`);
    }
  }
  return { manifest:m, derived:d, manifestHash:sha256(manifestBytes) };
}
