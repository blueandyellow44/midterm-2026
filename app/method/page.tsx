import type { Metadata } from 'next';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { method, derived } from '@/lib/data';
import { PageTitle } from '@/components/UI';
export const metadata:Metadata={title:'Method and limitations',description:'The release-frozen polling method, classification evidence, formulas, source coverage, deferred work and confounding limits.'};
export default function Method(){return <><PageTitle kicker={['stage2a','stage2b','stage2c'].every(s=>derived.stage_status?.[s]==='PASSED')?'Method · documented heuristic':'Method · draft until Stage 2 passes'} title="Show the workings."><p>This is the method note frozen with the displayed release, including its source gaps, Deferred section and confounding statements.</p></PageTitle><div className="method-document"><Markdown remarkPlugins={[remarkGfm]} components={{a:({href,children})=><a href={href} target={href?.startsWith('http')?'_blank':undefined} rel={href?.startsWith('http')?'noopener noreferrer':undefined}>{children}</a>,table:({children})=><div className="method-table"><table>{children}</table></div>}}>{method}</Markdown></div></>}
