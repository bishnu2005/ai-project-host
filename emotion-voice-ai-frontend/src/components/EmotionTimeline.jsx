export default function EmotionTimeline({segments=[]}){
  return (
    <div style={{display:"flex", gap:4}}>
      {segments.map((s,i)=>(
        <div key={i} title={`${s.start}-${s.end}`} style={{height:16, background:"#999", width: Math.max(2,(s.end-s.start)*20)}} />
      ))}
    </div>
  );
}
