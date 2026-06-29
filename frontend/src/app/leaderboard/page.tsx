"use client";

import { useState, useCallback } from "react";
import LeaderboardTable from "@/components/LeaderboardTable";
import type { LeaderboardRow } from "@/types";
import styles from "./page.module.css";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export default function LeaderboardPage() {
  const [townsText, setTownsText] = useState(
    "Skibbereen, Ireland\nBantry, Ireland\nSchull, Ireland\nKinsale, Ireland\nClonakilty, Ireland"
  );
  const [backDays, setBackDays] = useState(30);
  const [rows, setRows] = useState<LeaderboardRow[]>([]);
  const [resultBack, setResultBack] = useState(30);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const handleBuild = useCallback(async () => {
    const towns = townsText
      .split("\n")
      .map((t) => t.trim())
      .filter(Boolean);
    if (!towns.length) return;

    setLoading(true);
    setRows([]);
    setError("");
    setStatus(`Looking up ${towns.length} location${towns.length === 1 ? "" : "s"}… this may take a moment.`);

    try {
      const res = await fetch(`${API}/api/leaderboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ towns, back: backDays }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Failed to build leaderboard.");
        setStatus("");
        return;
      }
      setRows(data.leaderboard);
      setResultBack(data.back_days);
      setStatus("");
    } catch {
      setError("Network error. Please try again.");
      setStatus("");
    } finally {
      setLoading(false);
    }
  }, [townsText, backDays]);

  return (
    <>
      <section className={styles.card}>
        <h2 className={styles.heading}>Location Leaderboard</h2>
        <p className={styles.description}>
          Enter one town or village per line. The leaderboard ranks each location by the number of
          unique bird species recorded on eBird within its boundary.
        </p>

        <textarea
          className={styles.textarea}
          rows={7}
          value={townsText}
          onChange={(e) => setTownsText(e.target.value)}
          placeholder={"Skibbereen, Ireland\nBantry, Ireland\nKinsale, Ireland"}
        />

        <div className={styles.controls}>
          <div className={styles.backRow}>
            <label htmlFor="lb-back" className={styles.backLabel}>Days back:</label>
            <input
              id="lb-back"
              type="number"
              className={styles.backInput}
              value={backDays}
              min={1}
              max={30}
              onChange={(e) => setBackDays(Number(e.target.value))}
            />
          </div>
          <button className={styles.btn} onClick={handleBuild} disabled={loading}>
            {loading ? "Building…" : "Build Leaderboard"}
          </button>
        </div>

        {status && <p className={styles.status}>{status}</p>}
        {error && <p className={styles.errorMsg}>{error}</p>}
      </section>

      {rows.length > 0 && (
        <section className={styles.card}>
          <LeaderboardTable rows={rows} backDays={resultBack} />
        </section>
      )}
    </>
  );
}
