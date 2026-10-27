'use client';
import { useEffect, useState } from 'react';
export function Controls() {
 const [dark,setDark]=useState(false);
 useEffect(()=>{setDark(document.documentElement.classList.contains('dark'));document.documentElement.dataset.hydrated='true';},[]);
 function theme() {const next=!dark;setDark(next);document.documentElement.classList.toggle('dark',next);try{localStorage.setItem('ew-theme',next?'dark':'light');}catch{/* Session preference still works. */}}
 return <div className="flex flex-wrap items-center gap-2" aria-label="Display preferences"><button className="theme-button" type="button" aria-pressed={dark} onClick={theme}>{dark?'Light mode':'Dark mode'}</button></div>;
}
