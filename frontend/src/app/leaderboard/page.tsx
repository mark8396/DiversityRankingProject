"use client";

import { useState, useCallback, useEffect } from "react";
import LeaderboardTable from "@/components/LeaderboardTable";
import type { LeaderboardRow } from "@/types";
import styles from "./page.module.css";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

const DAYS_OPTIONS = [1, 3, 7, 14, 30];

const IRELAND_TOP_60 = [
  "Dublin", "Belfast", "Cork", "Limerick", "Galway", "Derry",
  "Newtownabbey", "Bangor", "Waterford", "Lisburn", "Drogheda",
  "Dundalk", "Swords", "Navan", "Bray", "Ballymena", "Newtownards",
  "Lurgan", "Carrickfergus", "Ennis", "Newry", "Carlow", "Kilkenny",
  "Naas", "Tralee", "Antrim", "Coleraine", "Newbridge", "Balbriggan",
  "Portlaoise", "Athlone", "Mullingar", "Letterkenny", "Greystones",
  "Wexford", "Portadown", "Sligo", "Celbridge", "Omagh", "Larne",
  "Malahide", "Clonmel", "Carrigaline", "Banbridge", "Maynooth",
  "Leixlip", "Armagh", "Dungannon", "Ashbourne", "Laytown",
  "Tullamore", "Killarney", "Cobh", "Enniskillen", "Midleton",
  "Strabane", "Mallow", "Arklow", "Castlebar", "Wicklow",
];

export default function LeaderboardPage() {
  const [backDays, setBackDays] = useState(30);
  const [rows, setRows] = useState<LeaderboardRow[]>([]);
  const [resultBack, setResultBack] = useState(30);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadCache = useCallback(async (days: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/leaderboard/cached?back=${days}`);
      const data = await res.json();
      setRows(data.leaderboard ?? []);
      setResultBack(data.back_days ?? days);
      setUpdatedAt(data.updated_at ?? null);
    } catch {
      // silently leave rows empty on cache fetch failure
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCache(backDays);
  }, [backDays, loadCache]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/leaderboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ towns: IRELAND_TOP_60, back: backDays }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Failed to refresh leaderboard.");
        return;
      }
      setRows(data.leaderboard);
      setResultBack(data.back_days);
      setUpdatedAt(new Date().toISOString());
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setRefreshing(false);
    }
  }, [backDays]);

  const formattedDate = updatedAt
    ? new Date(updatedAt).toLocaleString("en-IE", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : null;

  return (
    <>
      <section className={styles.card}>
        <h2 className={styles.heading}>Ireland Bird Diversity Leaderboard</h2>
        <p className={styles.description}>
          Ranks the top 60 settlements on the island of Ireland by the number of unique bird
          species recorded on eBird within each settlement&apos;s boundary.
        </p>

        <div className={styles.controls}>
          <div className={styles.backRow}>
            <label htmlFor="lb-back" className={styles.backLabel}>Days back:</label>
            <select
              id="lb-back"
              className={styles.backSelect}
              value={backDays}
              onChange={(e) => setBackDays(Number(e.target.value))}
            >
              {DAYS_OPTIONS.map((d) => (
                <option key={d} value={d}>
                  {d} {d === 1 ? "day" : "days"}
                </option>
              ))}
            </select>
          </div>
          <button className={styles.btn} onClick={handleRefresh} disabled={refreshing || loading}>
            {refreshing ? "Refreshing… (this takes ~60 s)" : "Refresh Leaderboard"}
          </button>
        </div>

        {formattedDate && (
          <p className={styles.updatedAt}>Last updated: {formattedDate}</p>
        )}
        {error && <p className={styles.errorMsg}>{error}</p>}
      </section>

      {loading && !refreshing && (
        <section className={styles.card}>
          <p className={styles.status}>Loading cached results…</p>
        </section>
      )}

      {!loading && rows.length === 0 && !error && (
        <section className={styles.card}>
          <p className={styles.status}>
            No data yet for this time period. Click &ldquo;Refresh Leaderboard&rdquo; to fetch live results.
          </p>
        </section>
      )}

      {rows.length > 0 && (
        <section className={styles.card}>
          <LeaderboardTable rows={rows} backDays={resultBack} />
        </section>
      )}
    </>
  );
}
