"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import styles from "./Map.module.css";

interface Props {
  bbox: [number, number, number, number] | null;
}

export default function Map({ bbox }: Props) {
  const mapRef = useRef<ReturnType<typeof import("leaflet")["map"]> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rectRef = useRef<ReturnType<typeof import("leaflet")["rectangle"]> | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    import("leaflet").then((L) => {
      const m = L.map(containerRef.current!).setView([53.5, -8], 6);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 18,
      }).addTo(m);
      mapRef.current = m;
    });
  }, []);

  useEffect(() => {
    if (!mapRef.current || !bbox) return;

    import("leaflet").then((L) => {
      if (rectRef.current) mapRef.current!.removeLayer(rectRef.current);
      const bounds: [[number, number], [number, number]] = [
        [bbox[0], bbox[2]],
        [bbox[1], bbox[3]],
      ];
      rectRef.current = L.rectangle(bounds, {
        color: "#61752d",
        weight: 2,
        fillOpacity: 0.12,
      }).addTo(mapRef.current!);
      mapRef.current!.fitBounds(bounds, { padding: [20, 20] });
    });
  }, [bbox]);

  return <div ref={containerRef} className={styles.map} />;
}
