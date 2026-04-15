"use client";

import Map, { Marker, Popup } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import { useState } from "react";

/* ------------------ SENSOR DATA ------------------ */
const sensors = [
  { id: "101", lat: 43.601, lon: -84.774, pm25: 12, health: 95, name: "Michigan", country: "usa" },
  { id: "102", lat: 40.7128, lon: -74.0060, pm25: 28, health: 80, name: "New York", country: "usa" },

  { id: "201", lat: 48.8566, lon: 2.3522, pm25: 35, health: 75, name: "Paris", country: "france" },
  { id: "202", lat: 52.52, lon: 13.405, pm25: 40, health: 70, name: "Berlin", country: "germany" },
  { id: "203", lat: 51.5074, lon: -0.1278, pm25: 30, health: 85, name: "London", country: "uk" },

  { id: "301", lat: 30.0444, lon: 31.2357, pm25: 120, health: 60, name: "Cairo", country: "egypt" },
  { id: "302", lat: 31.2001, lon: 29.9187, pm25: 95, health: 65, name: "Alexandria", country: "egypt" },

  { id: "401", lat: 6.5244, lon: 3.3792, pm25: 150, health: 50, name: "Lagos", country: "nigeria" },
  { id: "402", lat: -1.2921, lon: 36.8219, pm25: 80, health: 55, name: "Nairobi", country: "kenya" },
];

/* ------------------ AQI LOGIC ------------------ */
function getAQILevel(pm25: number) {
  if (pm25 < 12) return "good";
  if (pm25 < 35) return "moderate";
  if (pm25 < 55) return "sensitive";
  if (pm25 < 150) return "unhealthy";
  return "hazardous";
}

/* ------------------ HUMAN EXPLANATION ------------------ */
function generateExplanation(prediction: number, sensorsUsed: any[]) {
  const level = getAQILevel(prediction);

  const topSensor = sensorsUsed.sort((a, b) => b.pm25 - a.pm25)[0];

  if (level === "good") {
    return `Air quality is currently good. Sensors in ${topSensor.name} show low pollution levels, indicating clean air with minimal health risk.`;
  }

  if (level === "moderate") {
    return `Air quality is moderate. Some sensors such as ${topSensor.name} are showing elevated particulate levels, which may affect sensitive individuals.`;
  }

  if (level === "sensitive") {
    return `Air quality may be unhealthy for sensitive groups. Areas like ${topSensor.name} are experiencing increased pollution, likely due to traffic, industrial activity, or weather conditions.`;
  }

  if (level === "unhealthy") {
    return `Air quality is unhealthy. Sensors in ${topSensor.name} report high PM2.5 levels, which could be driven by urban congestion, emissions, or environmental factors. Prolonged exposure may impact health.`;
  }

  return `Air quality is hazardous. Extremely high pollution levels detected, especially around ${topSensor.name}. Immediate precautions are strongly advised due to severe air conditions.`;
}

/* ------------------ PREDICTION ENGINE ------------------ */
function predictAirQuality(location: string) {
  const query = location.trim().toLowerCase();

  const matched = sensors.filter(
    (s) =>
      s.name.toLowerCase().includes(query) ||
      s.country.toLowerCase().includes(query)
  );

  if (matched.length === 0) {
    return {
      prediction: null,
      confidence: 0,
      explanation: "No sensors found. Try a country like Egypt or a city like Cairo.",
    };
  }

  let weightedSum = 0;
  let totalWeight = 0;

  matched.forEach((s) => {
    const weight = s.health / 100;
    weightedSum += s.pm25 * weight;
    totalWeight += weight;
  });

  const prediction = weightedSum / totalWeight;

  const avgHealth =
    matched.reduce((acc, s) => acc + s.health, 0) / matched.length;

  const variance =
    matched.reduce((acc, s) => acc + Math.pow(s.pm25 - prediction, 2), 0) /
    matched.length;

  const confidence = Math.max(0, Math.min(100, avgHealth - variance / 2));

  const explanationText = generateExplanation(prediction, matched);

  return {
    prediction: prediction.toFixed(2),
    confidence: confidence.toFixed(1),
    explanationText,
  };
}

/* ------------------ MAIN COMPONENT ------------------ */
export default function PremiumMap() {
  const [selected, setSelected] = useState<any>(null);
  const [location, setLocation] = useState("");
  const [prediction, setPrediction] = useState<any>(null);

  const handleCheck = () => {
    const result = predictAirQuality(location);
    setPrediction(result);
  };

  return (
    <div style={{ width: "100vw", height: "100vh" }}>

      {/* DASHBOARD */}
      <div
        style={{
          position: "absolute",
          top: 20,
          left: 20,
          zIndex: 10,
          width: 340,
          padding: 20,
          borderRadius: 20,
          background: "rgba(24,24,27,0.75)",
          backdropFilter: "blur(14px)",
          color: "white",
        }}
      >
        <h2>Air Intelligence</h2>

        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Enter city or country..."
          style={{ width: "100%", padding: 10, borderRadius: 10 }}
        />

        <button onClick={handleCheck} style={{ marginTop: 10, width: "100%" }}>
          Get Prediction
        </button>

        {prediction && (
          <div style={{ marginTop: 15 }}>
            {prediction.prediction ? (
              <>
                <p>
                  📊 {prediction.prediction} µg/m³ | Confidence {prediction.confidence}%
                </p>

                <p style={{ marginTop: 10, lineHeight: 1.5 }}>
                  {prediction.explanationText}
                </p>
              </>
            ) : (
              <p>{prediction.explanation}</p>
            )}
          </div>
        )}
      </div>

      {/* MAP */}
      <Map
        mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
        initialViewState={{ latitude: 20, longitude: 0, zoom: 2 }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/mapbox/navigation-night-v1"
      >
        {sensors.map((s) => (
          <Marker
            key={s.id}
            latitude={s.lat}
            longitude={s.lon}
            anchor="center"
            onClick={(e: any) => {
              e.originalEvent.stopPropagation();
              setSelected(s);
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: "#ef4444",
              }}
            />
          </Marker>
        ))}

        {selected && (
          <Popup
            latitude={selected.lat}
            longitude={selected.lon}
            onClose={() => setSelected(null)}
          >
            <div>
              <b>{selected.name}</b>
              <br />
              PM2.5: {selected.pm25}
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}