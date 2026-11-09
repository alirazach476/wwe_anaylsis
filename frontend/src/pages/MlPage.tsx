import { useEffect, useState } from "react";
import { api } from "../api";

export default function MlPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.ml().then(setData);
  }, []);

  if (!data) return <p className="empty">Loading ML registry…</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div className="panel">
        <h3>Machine Learning</h3>
        <p className="muted" style={{ marginTop: 0 }}>
          {data.disclaimer || "Booking-pattern / estimation experiments only."}
        </p>
      </div>
      <div className="panel">
        <h3>Experiment registry</h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Metrics</th>
              </tr>
            </thead>
            <tbody>
              {(data.experiments || []).map((e: any) => (
                <tr key={e.experiment}>
                  <td>{e.experiment}</td>
                  <td>
                    <code style={{ fontSize: "0.8rem", color: "#c5c6c8" }}>
                      {JSON.stringify(
                        Object.fromEntries(
                          Object.entries(e).filter(([k]) => !["experiment", "feature_importance", "disclaimer"].includes(k))
                        )
                      )}
                    </code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!data.experiments?.length && <div className="empty">No experiments registered yet.</div>}
        <p className="muted" style={{ marginTop: 12 }}>
          Limitations: time-aware splits where possible; no athletic causation claims; scripted outcomes.
        </p>
      </div>
    </div>
  );
}
