import { readFileSync } from 'node:fs';
import { expect,it } from 'vitest';
import { toPublicNote,assertNoVaultLeak } from '../lib/public-note';
const sample=`---\ncalc_owner: ~/midterm-2026/analysis/weight.py\n---\nEvery number in this note is computed by \`~/midterm-2026/analysis/weight.py\` and read from a release bundle under \`Resources/methods/midterm-2026/releases/\`; this note formats, it never recalculates. The tracker web app renders the same bundle. Hub: [[Projects/Midterm-2026/Midterm-2026|Midterm-2026]]. Prompt revision 2026-10-25b.\n\n**Scorer, pinned.** \`~/litmus-meter\` at the commit.\n\n| Race | D +2.0 |\n\n## Related\n\n- [[Projects/LITMUS/LITMUS|LITMUS]] (the meter)\n- [[Daily/2026-10-24]] (the audit)\n- \`~/midterm-2026\` (code)\n`;
it('strips vault links, workstation paths and the prompt-revision line without touching content',()=>{
 const out=toPublicNote(sample);
 expect(out).toContain('computed by `analysis/weight.py` and read from the sealed release bundle; this note formats, it never recalculates. The tracker web app renders the same bundle.');
 expect(out).toContain('**Scorer, pinned.** The LITMUS meter at the commit.');
 expect(out).toContain('| Race | D +2.0 |');
 expect(out).not.toMatch(/Related|LITMUS go|Daily|Hub:|Prompt revision|\[\[|~\/|Resources\/methods|calc_owner/);
});
it('converts a stray wikilink to its visible text instead of leaking the vault path',()=>{
 expect(toPublicNote('See [[Context/health|the health note]] and [[Daily/2026-10-24]].')).toBe('See the health note and 2026-10-24.');
});
it('refuses to publish a note that still carries a vault artifact',()=>{
 expect(()=>toPublicNote('Kept in the Second Brain vault.')).toThrow(/vault name/);
 expect(()=>assertNoVaultLeak('<p>[[Projects/X|X]]</p>','/method/')).toThrow(/wikilink.*\/method\//);
 expect(()=>assertNoVaultLeak('<p>clean</p>','/method/')).not.toThrow();
});
it('cleans the bundled release note end to end',()=>{
 const out=toPublicNote(readFileSync('data/midterm-2026-poll-weighting.md','utf8'));
 expect(out).toContain('One polling reading per race');
 expect(out).toContain('Stage 3 remains gated until November 2.');
 expect(out).not.toMatch(/\[\[|~\/|Prompt revision|Resources\/methods|## Related/);
});
it('does not mistake framework payload brackets for a vault link',()=>{
 expect(()=>assertNoVaultLeak('<script>self.__next_f.push([1,"8:[[\\"children\\",{}]]"])</script>','/')).not.toThrow();
});
