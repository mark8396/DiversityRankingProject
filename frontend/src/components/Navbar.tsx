"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./Navbar.module.css";

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <span className={styles.brandIcon}>🦅</span>
          <span className={styles.brandText}>Bird Diversity Ranking</span>
        </div>
        <nav className={styles.nav} aria-label="Main navigation">
          <Link
            href="/"
            className={`${styles.link} ${pathname === "/" ? styles.active : ""}`}
          >
            Search
          </Link>
          <Link
            href="/leaderboard"
            className={`${styles.link} ${pathname === "/leaderboard" ? styles.active : ""}`}
          >
            Leaderboard
          </Link>
        </nav>
      </div>
    </header>
  );
}
