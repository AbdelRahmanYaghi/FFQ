const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getParticipants() {
  const r = await fetch(`${BASE}/participants`);
  if (!r.ok) throw new Error('Failed to load participants');
  return r.json();
}

export async function getParticipant(uid) {
  const r = await fetch(`${BASE}/participants/${encodeURIComponent(uid)}`);
  if (!r.ok) throw new Error('Failed to load participant');
  return r.json();
}

export async function saveParticipant(uid, rows) {
  const r = await fetch(`${BASE}/participants/${encodeURIComponent(uid)}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rows }),
  });
  if (!r.ok) throw new Error('Failed to save');
  return r.json();
}

export async function deleteParticipant(uid) {
  const r = await fetch(`${BASE}/participants/${encodeURIComponent(uid)}`, { method: 'DELETE' });
  if (!r.ok) throw new Error('Failed to delete');
  return r.json();
}

export function downloadUrl(uid) {
  return `${BASE}/participants/${encodeURIComponent(uid)}/download`;
}
