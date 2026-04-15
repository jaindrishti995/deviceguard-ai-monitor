const BASE = "http://localhost:5000";

export const fetchPredict   = () => fetch(`${BASE}/predict`).then(r => r.json());
export const fetchHistory   = (n=50) => fetch(`${BASE}/history?n=${n}`).then(r => r.json());
export const postTestAlert  = () => fetch(`${BASE}/test-alert`, { method: "POST" }).then(r => r.json());
export const fetchHealth    = () => fetch(`${BASE}/health`).then(r => r.json());