import type { NextConfig } from 'next';
const config: NextConfig = { output: 'standalone', trailingSlash: true, poweredByHeader: false, images: { unoptimized: true } };
export default config;
