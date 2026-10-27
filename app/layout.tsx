import type { Metadata } from 'next';
import '@fontsource-variable/manrope';
import '@fontsource/ibm-plex-mono/400.css';
import './globals.css';
import { Header,Footer,initialPreferences } from '@/components/UI';
export const metadata:Metadata={metadataBase:new URL('https://midtermundertow.com'),title:{default:'Undertow · 2026 midterm field notes',template:'%s · Undertow'},description:'Nineteen 2026 Senate and governor races, a documented polling method, recall-vote classification and separate debate rhetoric readings. Every figure tied to a verified release.',openGraph:{title:'Undertow · 2026',description:'A clear record of polls, methods and campaign rhetoric.',images:[{url:'/og.png',width:1200,height:630,alt:'Undertow, 2026 midterm field notes'}]},icons:{icon:[{url:'/favicon.svg',type:'image/svg+xml'},{url:'/favicon.png',type:'image/png'}]}};
export const dynamic='error';
export default function Layout({children}:{children:React.ReactNode}) {return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{__html:initialPreferences}}/></head><body className="bg-paper text-ink dark:bg-night dark:text-chalk"><a className="skip-link" href="#main">Skip to content</a><Header/><main id="main" tabIndex={-1} className="shell py-10 sm:py-14">{children}</main><Footer/></body></html>}
