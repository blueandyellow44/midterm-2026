import type { Metadata } from 'next';
import '@fontsource-variable/manrope';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/barlow-condensed/700.css';
import '@fontsource/barlow-condensed/800.css';
import './globals.css';
import { Header,Footer,initialPreferences } from '@/components/UI';
export const metadata:Metadata={metadataBase:new URL('https://midtermundertow.com'),title:{default:'Undertow · 2026 midterm field notes',template:'%s · Undertow'},description:'Nineteen 2026 Senate and governor races: the polls, and where last fall’s polling miss, campaign money and early voting say they are wrong. Every figure tied to a verified release.',openGraph:{title:'Undertow · 2026',description:'Where the 2026 polls are likely wrong, and by how much.',images:[{url:'/og.png',width:1200,height:630,alt:'Undertow, 2026 midterm field notes'}]},icons:{icon:[{url:'/favicon.svg',type:'image/svg+xml'},{url:'/favicon.png',type:'image/png'}],apple:[{url:'/apple-touch-icon.png',sizes:'180x180'}]}};
export const dynamic='error';
export default function Layout({children}:{children:React.ReactNode}) {return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{__html:initialPreferences}}/></head><body className="bg-paper text-ink dark:bg-night dark:text-chalk"><a className="skip-link" href="#main">Skip to content</a><Header/><main id="main" tabIndex={-1} className="shell py-10 sm:py-14">{children}</main><Footer/></body></html>}
