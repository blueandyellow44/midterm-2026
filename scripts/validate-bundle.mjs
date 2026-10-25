import { validateBundle } from './bundle.mjs';
const b=validateBundle(new URL('../data/',import.meta.url).pathname);
console.log(`Verified ${b.manifest.release_id}; manifest ${b.manifestHash}`);
