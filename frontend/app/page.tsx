import styles from "./page.module.css";
import { fetchHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  try {
    const [live, ready] = await Promise.all([
      fetchHealth("/health/live"),
      fetchHealth("/health/ready"),
    ]);
    return (
      <main className={styles.page}>
        <section className={styles.card}>
          <p className={styles.eyebrow}>Phase 00 · Local bootstrap</p>
          <h1>EGX AI Portfolio Manager</h1>
          <p className={styles.intro}>API status is available from the local FastAPI service.</p>
          <dl className={styles.status}>
            <div><dt>Status</dt><dd>{live.status}</dd></div>
            <div><dt>Service</dt><dd>{live.service}</dd></div>
            <div><dt>Version</dt><dd>{live.version}</dd></div>
            <div><dt>Timestamp</dt><dd>{live.timestamp}</dd></div>
            <div><dt>Readiness</dt><dd>{ready.status}</dd></div>
          </dl>
          <h2>Checks</h2>
          <pre>{JSON.stringify(ready.checks, null, 2)}</pre>
        </section>
      </main>
    );
  } catch {
    return (
      <main className={styles.page}>
        <section className={styles.card} role="alert">
          <p className={styles.eyebrow}>Phase 00 · Local bootstrap</p>
          <h1>EGX AI Portfolio Manager</h1>
          <p className={styles.unavailable}>API unavailable</p>
          <p className={styles.intro}>Start the backend with <code>make backend</code> and refresh.</p>
        </section>
      </main>
    );
  }
}
