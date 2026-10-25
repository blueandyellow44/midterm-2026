'use client';
import { useEffect, useState } from 'react';
export function Controls() {
 const [view,setView]=useState('desktop');const [dark,setDark]=useState(false);
 useEffect(()=>{setView(document.documentElement.dataset.view||'desktop');setDark(document.documentElement.classList.contains('dark'));document.documentElement.dataset.hydrated='true';},[]);
 function choose(next:string) {setView(next);document.documentElement.dataset.view=next;try{localStorage.setItem('ew-view',next);}catch{/* Preference remains usable when storage is disabled. */}}
 function theme() {const next=!dark;setDark(next);document.documentElement.classList.toggle('dark',next);try{localStorage.setItem('ew-theme',next?'dark':'light');}catch{/* Session preference still works. */}}
 return <div className="flex flex-wrap items-center gap-2" aria-label="Display preferences"><div className="view-switch flex" role="group" aria-label="Site version"><button type="button" aria-pressed={view==='desktop'} onClick={()=>choose('desktop')}>Desktop site</button><button type="button" aria-pressed={view==='mobile'} onClick={()=>choose('mobile')}>Mobile site</button></div><button className="theme-button" type="button" aria-pressed={dark} onClick={theme}>{dark?'Light mode':'Dark mode'}</button></div>;
}
