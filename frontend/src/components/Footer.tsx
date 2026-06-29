import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <p>
          Location data &copy;{" "}
          <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">
            OpenStreetMap
          </a>{" "}
          contributors &nbsp;·&nbsp; Bird data from{" "}
          <a href="https://ebird.org" target="_blank" rel="noopener noreferrer">
            eBird
          </a>
          , Cornell Lab of Ornithology
        </p>
      </div>
    </footer>
  );
}
