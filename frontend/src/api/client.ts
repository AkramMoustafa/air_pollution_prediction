const BASE_URL = import.meta.env.VITE_API_URL;

export async function getLocations(limit?: number) {
  let url = `${BASE_URL}/locations`;

  if (limit !== undefined) {
    url += `?limit=${limit}`;
  }

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}