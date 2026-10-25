import { mkdirSync,copyFileSync } from 'node:fs';
import { join,dirname } from 'node:path';
const root=join('.backups',new Date().toISOString().replaceAll(':','-'));
for(const file of process.argv.slice(2)){const target=join(root,file);mkdirSync(dirname(target),{recursive:true});copyFileSync(file,target);}
console.log(`Preserved ${process.argv.length-2} files in ${root}`);
