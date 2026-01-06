import React, { useEffect, useMemo, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

function App() {
  const API = process.env.REACT_APP_API_URL;
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch(`${API}/api/dashboard`)
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, [API]);

  const chartData = useMemo(() => {
    if (!data) return null;

    const histLabels = data.history.map((x) => x.date);
    const histActual = data.history.map((x) => x.actual);

    const fcLabels = data.forecast.map((x) => x.date);
    const fcPreds = data.forecast.map((x) => x.pred);

    // รวม label history + future
    const labels = [...histLabels, ...fcLabels];

    // เส้น Actual: มีเฉพาะใน history ส่วน forecast เป็น null
    const actualSeries = [...histActual, ...new Array(fcLabels.length).fill(null)];

    // เส้น Forecast: ใส่ null ในช่วง history แล้วค่อยมีค่าในช่วงอนาคต
    const forecastSeries = [...new Array(histLabels.length).fill(null), ...fcPreds];

    return {
      labels,
      datasets: [
        { label: "Actual", data: actualSeries },
        { label: "Forecast", data: forecastSeries }
      ]
    };
  }, [data]);

  if (err) return <div style={{ padding: 16 }}>Error: {err}</div>;
  if (!data) return <div style={{ padding: 16 }}>Loading...</div>;

  return (
    <div style={{ padding: 16, fontFamily: "sans-serif", maxWidth: 1100, margin: "0 auto" }}>
      <h2>Gold Forecast Dashboard (ARIMA)</h2>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 12 }}>
        <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12, minWidth: 220 }}>
          <div><b>Target</b></div>
          <div>{data.target}</div>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12, minWidth: 220 }}>
          <div><b>Latest Date</b></div>
          <div>{data.latest.date}</div>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12, minWidth: 220 }}>
          <div><b>Latest Actual</b></div>
          <div>{data.latest.actual}</div>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12, minWidth: 220 }}>
          <div><b>Model</b></div>
          <div>ARIMA({data.model.order.join(",")})</div>
        </div>
      </div>

      <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 12 }}>
        <h3 style={{ marginTop: 0 }}>Actual vs Forecast</h3>
        <Line data={chartData} />
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Forecast (next {data.forecast.length} days)</h3>
        <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 600 }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #eee", padding: 8 }}>Date</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #eee", padding: 8 }}>Pred</th>
            </tr>
          </thead>
          <tbody>
            {data.forecast.map((x, i) => (
              <tr key={i}>
                <td style={{ padding: 8, borderBottom: "1px solid #f5f5f5" }}>{x.date}</td>
                <td style={{ padding: 8, textAlign: "right", borderBottom: "1px solid #f5f5f5" }}>{x.pred}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
