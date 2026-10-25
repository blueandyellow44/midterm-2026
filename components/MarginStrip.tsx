export function MarginStrip({value}:{value:number|null}) {
 if(value===null||!Number.isFinite(value))return null;
 const position=32+(Math.max(-30,Math.min(30,value))+30)/60*336;
 return <svg className="margin-strip" viewBox="0 0 400 54" role="img" aria-label={`Polling margin: ${value>0?'Democrat':value<0?'Republican':'even'}${value===0?'':` leads by ${Math.abs(value).toFixed(1)} percentage points`}. Scale runs from a 30-point Republican lead to a 30-point Democratic lead.`}><title>Polling margin, not win probability</title><line x1="32" x2="200" y1="18" y2="18" className="margin-r-track"/><line x1="200" x2="368" y1="18" y2="18" className="margin-d-track"/><line x1="200" x2="200" y1="9" y2="27" className="margin-zero"/><circle cx={position} cy="18" r="6" className={value>=0?'party-d-fill':'party-r-fill'}/><text x="32" y="47">R lead</text><text x="200" y="47" textAnchor="middle">Even</text><text x="368" y="47" textAnchor="end">D lead</text></svg>;
}
