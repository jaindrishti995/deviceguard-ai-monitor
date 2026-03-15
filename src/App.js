import React, { useState } from "react";
import Dashboard from "./components/Dashboard";
import Login from "./components/Login";
import "./App.css";
import { PieChart, Pie, Cell, Tooltip } from "recharts";

function App(){

const [loggedIn,setLoggedIn] = useState(false);
const [metrics,setMetrics] = useState({});
const [health,setHealth] = useState(null);
const [message,setMessage] = useState("");

const handleLogin = ()=>{
setLoggedIn(true);
};

const receiveMetrics = (data)=>{
setMetrics(data);
};

const startMonitoring = ()=>{

const values = Object.values(metrics).map(Number);

if(values.length===0) return;

const avg = values.reduce((a,b)=>a+b,0)/values.length;

const systemHealth = Math.max(0,100-avg);

setHealth(systemHealth);

if(systemHealth>70)
setMessage("Far away from degradation");

else if(systemHealth>40)
setMessage("Degradation will soon start");

else
setMessage("Degradation started");

};

if(!loggedIn){
return <Login onLogin={handleLogin}/>
}

const chartData = [
{ name:"Health", value:health||0 },
{ name:"Used", value:100-(health||0) }
];

const COLORS=["#60a5fa","#1e293b"];

return(

<div className="app">

<nav className="navbar">

<h2 className="logo">DeviceGuard</h2>

<ul>
<li>Products</li>
<li>Features</li>
<li>Analytics</li>
<li>AI Monitor</li>
</ul>

<button className="btn">Dashboard</button>

</nav>


<section className="hero">

<div className="hero-text">

<h1>
AI Powered <span>Device Monitoring</span>
</h1>

<p>
Monitor CPU, RAM, temperature and anomalies using AI powered insights.
</p>

<button className="hero-btn" onClick={startMonitoring}>
Start Monitoring
</button>

</div>


<div className="hero-card">

<div className="output-title">
AI Monitoring Output
</div>

<div className="output-box">

{health===null ?(

<p>Waiting for monitoring...</p>

):(

<>

<PieChart width={220} height={220}>
<Pie
data={chartData}
cx="50%"
cy="50%"
innerRadius={60}
outerRadius={80}
dataKey="value"
>

{chartData.map((entry,index)=>(
<Cell key={index} fill={COLORS[index]}/>
))}

</Pie>

<Tooltip/>

</PieChart>

<h3>{health.toFixed(1)}% System Health</h3>

{health<=40 ?(

<div className="alert-box">
⚠ CRITICAL: Degradation Started
</div>

):(

<p className="ai-message">{message}</p>

)}

</>

)}

</div>

</div>

</section>


<section>

<h2 className="section-title">System Dashboard</h2>

<Dashboard sendMetrics={receiveMetrics}/>

</section>

</div>

)

}

export default App;