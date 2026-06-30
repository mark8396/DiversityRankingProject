"use client";

import { useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import SpeciesResult from "@/components/SpeciesResult";
import type { PlaceResult, SpeciesResult as SpeciesResultType } from "@/types";
import styles from "./page.module.css";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [place, setPlace] = useState<PlaceResult | null>(null);
  const [speciesResult, setSpeciesResult] = useState<SpeciesResultType | null>(null);
  const [backDays, setBackDays] = useState(30);
  const [searchStatus, setSearchStatus] = useState("");
  const [searchError, setSearchError] = useState(false);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingSpecies, setLoadingSpecies] = useState(false);
  const [speciesError, setSpeciesError] = useState("");

  const handleSearch = useCallback(async () => {
    const q = query.trim();
    if (!q) return;
    setLoadingSearch(true);
    setSearchStatus("Searching…");
    setSearchError(false);
    setPlace(null);
    setSpeciesResult(null);
    setSpeciesError("");

    try {
      const res = await fetch(`${API}/api/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (!res.ok) {
        setSearchStatus(data.error ?? "Not found.");
        setSearchError(true);
        return;
      }
      setPlace(data);
      setSearchStatus(`Found: ${data.display_name}`);
    } catch {
      setSearchStatus("Network error. Please try again.");
      setSearchError(true);
    } finally {
      setLoadingSearch(false);
    }
  }, [query]);

  const handleSpecies = useCallback(async () => {
    if (!place) return;
    setLoadingSpecies(true);
    setSpeciesResult(null);
    setSpeciesError("");

    try {
      const res = await fetch(
        `${API}/api/species?q=${encodeURIComponent(query.trim())}&back=${backDays}`
      );
      const data = await res.json();
      if (!res.ok) {
        setSpeciesError(data.error ?? "Failed to fetch species.");
        return;
      }
      setSpeciesResult(data);
    } catch {
      setSpeciesError("Network error. Please try again.");
    } finally {
      setLoadingSpecies(false);
    }
  }, [place, query, backDays]);

  return (
    <>
      <section className={styles.card}>
        <h2 className={styles.heading}>Search a Location</h2>
        <div className={styles.row}>
          <input
            type="text"
            className={styles.input}
            placeholder="e.g. Skibbereen, Ireland"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            autoComplete="off"
          />
          <button
            className={styles.btn}
            onClick={handleSearch}
            disabled={loadingSearch || !query.trim()}
          >
            {loadingSearch ? "Searching…" : "Search"}
          </button>
        </div>

        {searchStatus && (
          <p className={`${styles.status} ${searchError ? styles.statusError : ""}`}>
            {searchStatus}
          </p>
        )}

        <Map bbox={place?.bbox ?? null} geojson={place?.geojson ?? null} />

        <div className={styles.backRow}>
          <label htmlFor="back-days" className={styles.backLabel}>Days back:</label>
          <input
            id="back-days"
            type="number"
            className={styles.backInput}
            value={backDays}
            min={1}
            max={30}
            onChange={(e) => setBackDays(Number(e.target.value))}
          />
          <button
            className={styles.btn}
            onClick={handleSpecies}
            disabled={!place || loadingSpecies}
          >
            {loadingSpecies ? "Fetching…" : "Get Species Count"}
          </button>
        </div>

        {speciesError && <p className={styles.statusError}>{speciesError}</p>}
        {speciesResult && <SpeciesResult result={speciesResult} />}
      </section>
    </>
  );
}
