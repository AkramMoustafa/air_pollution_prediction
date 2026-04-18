"use client";

import Map, { Source, Layer } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import { useEffect, useState } from "react";
import { getLocations } from "./api/client";

export default function PremiumMap() {
  const [geoData, setGeoData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getLocations(); // 🔥 ALL DATA

        const geojson = {
          type: "FeatureCollection",
          features: res.data.map((s: any) => ({
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [s.lon, s.lat],
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
    <div style={{ width: "100vw", height: "100vh" }}>
      <Map
        mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
        initialViewState={{ latitude: 20, longitude: 0, zoom: 2 }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/mapbox/navigation-night-v1"
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