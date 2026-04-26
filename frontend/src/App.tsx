"use client";

import { useRef, useEffect, useState } from "react";
import Map, { Source, Layer } from "react-map-gl/mapbox";
import type { MapRef } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import AQIHeader from "./components/AQIHeader";
import AQIStaticBox from "./components/AQIInsightCard"
import { getLocations, getSensorData, getPrediction } from "./api/client";

export default function PremiumMap() {
  const [geoData, setGeoData] = useState<any>(null);
  const [selectedPoint, setSelectedPoint] = useState<any>(null);
  const mapRef = useRef<MapRef>(null);
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<any>(null);
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
    
   <div style={{ width: "100%",height: "100dvh", position: "relative", overflow: "hidden" }}>
      

      <AQIHeader />
    <AQIStaticBox
      selectedPoint={selectedPoint}
      prediction={prediction}
      loading={loading}
    />
      {/* MAP */}
      <Map
        ref={mapRef}
        mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
        initialViewState={{ latitude: 20, longitude: 0, zoom: 2 }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/mapbox/navigation-night-v1"
        interactiveLayerIds={["points"]} 
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
                
          setPrediction(null);  // <-- add this

          try {
        const [sensorRes, predictionRes] = await Promise.all([
          getSensorData(lat, lng),
          getPrediction(lat, lng),
        ]);

        setSelectedPoint({
          lat,
          lng,
          pm25: sensorRes.pm25,
         timestamp: sensorRes.datetime,
        });

        setPrediction(predictionRes);

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