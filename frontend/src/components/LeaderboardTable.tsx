import type { LeaderboardRow } from "@/types";
import styles from "./LeaderboardTable.module.css";

interface Props {
  rows: LeaderboardRow[];
  backDays: number;
}

const MEDALS = ["🥇", "🥈", "🥉"];

export default function LeaderboardTable({ rows, backDays }: Props) {
  return (
    <div className={styles.wrapper}>
      <p className={styles.subtitle}>
        Species recorded in the last {backDays} day{backDays === 1 ? "" : "s"}
      </p>
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.thRank}>#</th>
              <th>Location</th>
              <th className={styles.thCount}>Species</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.town}
                className={`${styles.row} ${styles[`rank${row.rank}`] ?? ""}`}
              >
                <td className={styles.rankCell}>
                  {MEDALS[row.rank - 1] ?? row.rank}
                </td>
                <td className={styles.locationCell}>
                  {row.display_name || row.town}
                </td>
                <td className={styles.countCell}>
                  {row.error ? (
                    <span className={styles.error}>{row.error}</span>
                  ) : (
                    <strong>{row.species_count}</strong>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
