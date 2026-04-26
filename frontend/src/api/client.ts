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
export async function getSensorData(lat: number, lon: number) {
  const url = `${BASE_URL}/sensor-data?lat=${lat}&lon=${lon}`;

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
export async function getPrediction(lat: number, lon: number) {
  const url = `${BASE_URL}/predict?lat=${lat}&lon=${lon}`;

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}