const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010";

export async function uploadAudio(file){
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/e2e`, { method:"POST", body: form });
  if(!res.ok) throw new Error("upload failed");
  return res.json();
}
