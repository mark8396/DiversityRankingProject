"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import styles from "./Map.module.css";

interface Props {
  bbox: [number, number, number, number] | null;
  geojson: Record<string, unknown> | null;
}

const LAYER_STYLE = { color: "#61752d", weight: 2, fillOpacity: 0.12 };

export default function Map({ bbox, geojson }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<ReturnType<typeof import("leaflet")["map"]> | null>(null);
  const layerRef = useRef<ReturnType<typeof import("leaflet")["rectangle"]> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    import("leaflet").then((L) => {
      // Initialise map once
      if (!mapRef.current) {
        const m = L.map(containerRef.current!).setView([53.5, -8], 6);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "&copy; OpenStreetMap contributors",
          maxZoom: 18,
        }).addTo(m);
        mapRef.current = m;
      }

      // Remove previous layer
      if (layerRef.current) {
        mapRef.current!.removeLayer(layerRef.current);
        layerRef.current = null;
      }

      if (!bbox) return;

      if (geojson) {
        const layer = L.geoJSON(geojson as Parameters<typeof L.geoJSON>[0], { style: LAYER_STYLE });
        layer.addTo(mapRef.current!);
        layerRef.current = layer as unknown as typeof layerRef.current;
        mapRef.current!.fitBounds(layer.getBounds(), { padding: [20, 20] });
      } else {
        const bounds: [[number, number], [number, number]] = [
          [bbox[0], bbox[2]],
          [bbox[1], bbox[3]],
        ];
        const rect = L.rectangle(bounds, LAYER_STYLE);
        rect.addTo(mapRef.current!);
        layerRef.current = rect;
        mapRef.current!.fitBounds(bounds, { padding: [20, 20] });
      }
    });
  }, [bbox, geojson]);

  return <div ref={containerRef} className={styles.map} />;
}
