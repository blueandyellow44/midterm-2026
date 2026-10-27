// Public rendering of the release-frozen method note. The sealed bundle keeps the note exactly as released;
// this strips vault navigation and workstation paths that mean nothing to a reader of the public site.
// Formatting only: no number, table or claim is changed. toPublicNote throws if a vault artifact survives.
const RELATED_HEADING=/\n## Related\n[\s\S]*$/;
const LEAK_PATTERNS:[RegExp,string][]=[
 [/\[\[[A-Za-z][^\]\n]*\]\]/,'wikilink'],
 [/~\/[A-Za-z]/,'home-directory path'],
 [/Resources\/methods/,'vault path'],
 [/Prompt revision/,'prompt-revision line'],
 [/Second Brain/,'vault name'],
];
export function toPublicNote(note:string):string{
 let out=note.replace(/^---[\s\S]*?---\s*/,'');
 out=out.replace(RELATED_HEADING,'\n');
 out=out.replace(/ Hub: \[\[[^\]]*\]\]\./g,'');
 out=out.replace(/ Prompt revision [0-9]{4}-[0-9]{2}-[0-9]{2}[a-z]?\./g,'');
 out=out.replace(/read from a release bundle under `Resources\/methods\/midterm-2026\/releases\/`/g,'read from the sealed release bundle');
 out=out.replace(/`~\/midterm-2026\/([^`]+)`/g,'`$1`');
 out=out.replace(/`~\/litmus-meter`/g,'The LITMUS meter');
 out=out.replace(/\| undefined (?=\|)/g,'| NA ');
 out=out.replace(/\[\[[^\]|]*\|([^\]]+)\]\]/g,'$1');
 out=out.replace(/\[\[([^\]]+)\]\]/g,(_m,p:string)=>p.split('/').pop()??p);
 for(const [re,label] of LEAK_PATTERNS){const m=re.exec(out);if(m){const at=out.lastIndexOf('\n',m.index)+1;throw new Error(`Public method note still carries a ${label}: ${out.slice(at,at+160)}`);}}
 return out;
}
export function assertNoVaultLeak(html:string,route:string):void{
 for(const [re,label] of LEAK_PATTERNS){if(re.test(html))throw new Error(`Vault ${label} in emitted HTML: ${route}`);}
}
