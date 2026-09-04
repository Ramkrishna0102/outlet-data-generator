/** @jsxRuntime classic */
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
// The stylesheet is processed by the frontend bundler and has no TypeScript declarations.
// @ts-expect-error -- side-effect CSS import
import "./style.css";

declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elementName: string]: any;
    }
  }
}

const columns = ["Outlet ID", "Outlet Name", "Latitude", "Longitude", "Distributor ID", "Distributor Name", "Beat ID", "Beat Name", "Employee ID", "Employee Name", "Address", "City", "State", "Revenue", "Visit Frequency"];
const initial = { location: "Lucknow", radius_km: 30, distributors: 5, beats_per_distributor: 5, employees_per_distributor: 3, outlets_per_distributor: 100, min_distance_m: 100 };
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [form, setForm] = useState<any>(initial);
  const [selected, setSelected] = useState(columns);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const update = (key: string, value: string) => setForm({ ...form, [key]: key === "location" ? value : Number(value) });
  const generate = async () => {
    setLoading(true);
    const response = await fetch(`${API_BASE_URL}/api/generation/preview`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, columns: selected }) });
    setResult(await response.json()); setLoading(false);
  };
  const download = async () => {
    const response = await fetch(`${API_BASE_URL}/api/export/excel`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, columns: selected }) });
    const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "Generated_Data.xlsx"; link.click(); URL.revokeObjectURL(url);
  };
  return <main><header><p className="eyebrow">Ro-Vibe Dashboard</p><h1>Input file  generator</h1><p className="sub">Create realistic distributor, beat, employee, and outlet data in seconds.</p></header>
    <section className="card"><h2>Generation settings</h2><div className="grid">{([["location","Location"],["radius_km","Radius (KM)"],["distributors","Distributors"],["beats_per_distributor","Beats per distributor"],["employees_per_distributor","Employees per distributor"],["outlets_per_distributor","Outlets per distributor"],["min_distance_m","Minimum distance (M)"]] as [string, string][]).map(([key,label]) => <label key={key}>{label}{key === "location" ? <select value={form[key]} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => update(key,e.target.value)}><option>Lucknow</option><option>Delhi</option><option>Mumbai</option><option>Noida</option></select> : <input type="number" min="1" value={form[key]} onChange={(e: React.ChangeEvent<HTMLInputElement>) => update(key,e.target.value)} />}</label>)}</div>
      <h3>Output columns</h3><div className="checks">{columns.map(column => <label className="check" key={column}><input type="checkbox" checked={selected.includes(column)} onChange={e => setSelected(e.target.checked ? [...selected,column] : selected.filter((item:string) => item !== column))}/>{column}</label>)}</div><button onClick={generate} disabled={loading || !selected.length}>{loading ? "Generating..." : "Generate preview"}</button></section>
    {result?.statistics && <section className="card"><div className="stats">{Object.entries(result.statistics).map(([key,value]) => <div className="stat" key={key}><strong>{String(value)}</strong><span>{key.replaceAll("_"," ")}</span></div>)}</div><div className="table-wrap"><table><thead><tr>{selected.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.records.map((row:any,index:number) => <tr key={index}>{selected.map(column => <td key={column}>{row[column]}</td>)}</tr>)}</tbody></table></div><button className="secondary" onClick={download}>Download Generated_Data.xlsx</button></section>}</main>;
}
createRoot(document.getElementById("root")!).render(<App />);
