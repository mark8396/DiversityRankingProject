import type { SpeciesResult as SpeciesResultType } from "@/types";
import styles from "./SpeciesResult.module.css";

interface Props {
  result: SpeciesResultType;
}

export default function SpeciesResult({ result }: Props) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.count}>{result.species_count}</div>
      <div className={styles.label}>
        unique species recorded in the last {result.back_days} day{result.back_days === 1 ? "" : "s"}
      </div>
      <div className={styles.location}>{result.town}</div>

      {result.species_count > 0 && (
        <details className={styles.details}>
          <summary className={styles.summary}>
            Show all {result.species_count} species
          </summary>
          <div className={styles.grid}>
            {result.species_list.map((s) => (
              <div key={s.speciesCode} className={styles.item}>
                <span className={styles.comName}>{s.comName}</span>
                <span className={styles.sciName}>{s.sciName}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
