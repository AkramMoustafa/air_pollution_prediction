"use client";

import { useRef, useEffect, useState } from "react";
import Map, { Source, Layer } from "react-map-gl/mapbox";
import type { MapRef } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import { getLocations, getSensorData } from "./api/client";

export default function PremiumMap() {
  const [geoData, setGeoData] = useState<any>(null);
  const [selectedPoint, setSelectedPoint] = useState<any>(null);
  const mapRef = useRef<MapRef>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getLocations();

        const geojson = {
          type: "FeatureCollection",
          features: res.data.map((s: any) => ({
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [s.lon, s.lat],
            },
            properties: {
              lat: s.lat,
              lon: s.lon,
            },
          })),
        };

        setGeoData(geojson);
      } catch (err) {
        console.error("❌ API ERROR:", err);
      }
    };

    fetchData();
  }, []);

  return (
    
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      
      {/* RIGHT PANEL */}
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: "300px",
          height: "100%",
          background: "#111827",
          color: "white",
          padding: "20px",
          zIndex: 10,
        }}
      >
        <h2>Location Info</h2>
    {loading && <p>Loading sensor data...</p>}
        {!selectedPoint && <p>Click anywhere on the map</p>}
        {selectedPoint && (
          <>
            <p><strong>Latitude:</strong> {selectedPoint.lat}</p>
            <p><strong>Longitude:</strong> {selectedPoint.lng}</p>
            <p><strong>Data Points:</strong> {selectedPoint.count}</p>

            {/* show sample sensor data */}
            {selectedPoint.data?.slice(0, 5).map((d: any, i: number) => (
              <div key={i} style={{ marginBottom: "10px" }}>
                <p><strong>{d.parameter}</strong>: {d.value}</p>
                <p style={{ fontSize: "12px", color: "#9ca3af" }}>
                  {d.datetime}
                </p>
              </div>
            ))}
          </>
        )}
      </div>

      {/* MAP */}
      <Map
        ref={mapRef}
        mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
        initialViewState={{ latitude: 20, longitude: 0, zoom: 2 }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/mapbox/navigation-night-v1"
        interactiveLayerIds={["points"]} // 🔥 THIS FIXES IT
       onClick={async (e) => {
          let lng: number, lat: number;

          const feature = e.features?.[0];

          if (feature && feature.geometry?.type === "Point") {
            [lng, lat] = (feature.geometry as any).coordinates;
          } else {
            // 👇 fallback → ANYWHERE on map works
            ({ lng, lat } = e.lngLat);
          }

          // ✅ THIS WILL ALWAYS RUN NOW
          mapRef.current?.flyTo({
            center: [lng, lat],
            zoom: 8,
            duration: 1000,
          });

          setLoading(true);

          try {
            const res = await getSensorData(lat, lng);

            setSelectedPoint({
              lat,
              lng,
              count: res.count,
              data: res.data,
            });

          } catch (err) {
            console.error("❌ Fetch error:", err);
          } finally {
            setLoading(false);
          }
        }}
      >
        {geoData && (
          <Source id="sensors" type="geojson" data={geoData}>
            <Layer
              id="points"
              type="circle"
              paint={{
                "circle-radius": 3,
                "circle-color": "#22c55e",
              }}
            />
          </Source>
        )}
      </Map>
    </div>
  );
}