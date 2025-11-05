// ✅ Updated to use your live backend by default
const API =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://ai-project-host-5.onrender.com";

export async function uploadAudio(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API}/e2e`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) throw new Error("upload failed");
  return res.json();
}
