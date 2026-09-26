"use client";

import { useMemo, useState } from "react";

const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
const stages=[["planning","PLAN"],["searching","SEARCH"],["sources_found","EVIDENCE"],["verifying","VERIFY"],["contradictions","CONFLICT"],["followup_search","RECHECK"],["synthesizing","SYNTHESIZE"],["complete","COMPLETE"]];
const presets=["Compare leading open-source edge AI frameworks in 2026.","How is RISC-V changing AI accelerator design?","Investigate the current state of on-device multimodal AI."];

export default function Home(){
 const [question,setQuestion]=useState(""),[events,setEvents]=useState([]),[report,setReport]=useState(""),[running,setRunning]=useState(false),[error,setError]=useState(""),[sources,setSources]=useState(0),[conflicts,setConflicts]=useState(0);
 const active=useMemo(()=>{let n=-1;events.forEach(e=>{const i=stages.findIndex(s=>s[0]===e.type);if(i>=0)n=Math.max(n,i)});return n},[events]);
 async function launch(){
  if(!question.trim()||running)return; setRunning(true);setEvents([]);setReport("");setError("");setSources(0);setConflicts(0);
  try{
   const res=await fetch(API+"/api/research/stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:question.trim()})});
   if(!res.ok||!res.body)throw new Error("ScoutAI API returned HTTP "+res.status);
   const reader=res.body.getReader(),decoder=new TextDecoder();let buffer="";
   while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});const packets=buffer.split("\n\n");buffer=packets.pop()||"";
    for(const packet of packets){const line=packet.split("\n").find(x=>x.startsWith("data: "));if(!line)continue;const e=JSON.parse(line.slice(6));setEvents(x=>[...x,e]);if(e.type==="sources_found")setSources(e.data?.count||0);if(e.type==="contradictions")setConflicts(e.data?.count||0);if(e.type==="complete")setReport(e.data?.report||"");if(e.type==="error")setError(e.message||"Research failed.")}}
  }catch(e){setError(e.message||"Unable to connect to ScoutAI.")}finally{setRunning(false)}
 }
 return <main className="shell">
  <div className="scanline"/>
  <header className="topbar"><div className="brand"><div className="brandMark">S</div><div><div className="brandName">SCOUT<span>AI</span></div><div className="brandSub">AUTONOMOUS RESEARCH COMMAND</div></div></div><div className="status"><i/> SYSTEM ONLINE <b>v0.3</b></div></header>
  <section className="hero"><div className="eyebrow">◈ INTELLIGENCE CONSOLE / LIVE WEB RESEARCH</div><h1>Deploy a research <em>mission.</em></h1><p>ScoutAI plans, searches, verifies, challenges conflicting evidence, and synthesizes a cited intelligence report.</p>
   <div className="missionBox"><div className="missionHeader"><span>NEW RESEARCH MISSION</span><kbd>CTRL + ENTER</kbd></div>
    <textarea value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&(e.ctrlKey||e.metaKey))launch()}} placeholder="What do you want ScoutAI to investigate?" disabled={running}/>
    <div className="missionFooter"><div className="presets">{presets.map(p=><button key={p} onClick={()=>setQuestion(p)} disabled={running}>{p.slice(0,30)}…</button>)}</div><button className="launch" onClick={launch} disabled={running||!question.trim()}>{running?"SCOUTING...":"LAUNCH MISSION  ↗"}</button></div>
   </div>
  </section>
  {(running||events.length>0||report)&&<section className="consoleGrid"><div className="panel tracePanel"><div className="panelTitle"><span>LIVE TRACE</span><small>{running?"ACTIVE":"STANDBY"}</small></div>
   <div className="stageRail">{stages.map((s,i)=><div className={"stage "+(i<=active?"active ":"")+(i===active&&running?"current":"")} key={s[0]}><span>{String(i+1).padStart(2,"0")}</span>{s[1]}</div>)}</div>
   <div className="eventFeed">{events.length===0&&<div className="muted">Awaiting mission telemetry…</div>}{events.map((e,i)=><div className="event" key={(e.timestamp||"x")+i}><span className="eventDot"/><div><b>{e.message}</b><small>{e.timestamp?new Date(e.timestamp).toLocaleTimeString():""}</small>{e.data?.queries&&<code>{e.data.queries.join("  •  ")}</code>}</div></div>)}</div>
  </div><div className="sideStack"><div className="stats"><div><small>SOURCES</small><strong>{sources}</strong><span>COLLECTED</span></div><div><small>CONFLICTS</small><strong className={conflicts?"warning":""}>{conflicts}</strong><span>DETECTED</span></div><div><small>ENGINE</small><strong>GEMMA</strong><span>REASONING</span></div></div>
   <div className="panel protocol"><div className="panelTitle"><span>SCOUT PROTOCOL</span><small>ACTIVE</small></div>{["Plan independent research tasks","Retrieve live web evidence","Verify claims against sources","Challenge contradictions","Synthesize with citations"].map((x,i)=><div className="protocolLine" key={x}><b>{String(i+1).padStart(2,"0")}</b>{x}</div>)}</div>
  </div></section>}
  {error&&<div className="errorBox">⚠ {error}</div>}
  {report&&<section className="panel reportPanel"><div className="panelTitle"><span>INTELLIGENCE REPORT</span><small>MISSION COMPLETE</small></div><article className="report">{report}</article></section>}
  <footer><span>SCOUTAI // EVIDENCE BEFORE CONFIDENCE</span><span>SERPAPI × GEMMA</span></footer>
 </main>
}