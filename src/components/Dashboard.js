import React, { useState } from "react";
import "./Dashboard.css";

export default function Dashboard({sendMetrics}){

const [metrics,setMetrics]=useState({
cpu:"",
ram:"",
disk:"",
fan:"",
temperature:"",
dust:"",
battery:"",
humidity:""
})

const handleChange=(e)=>{

const updated={
...metrics,
[e.target.name]:e.target.value
}

setMetrics(updated)

sendMetrics(updated)

}

return(

<div className="dashboard">

<div className="metric-card">
<h3>CPU Usage</h3>
<input name="cpu" placeholder="Enter %" onChange={handleChange}/>
</div>

<div className="metric-card">
<h3>RAM Usage</h3>
<input name="ram" placeholder="Enter %" onChange={handleChange}/>
</div>

<div className="metric-card">
<h3>Disk Usage</h3>
<input name="disk" placeholder="Enter %" onChange={handleChange}/>
</div>

<div className="metric-card">
<h3>Fan Speed</h3>
<input name="fan" placeholder="RPM" onChange={handleChange}/>
</div>

<div className="metric-card">
<h3>Temperature</h3>
<input name="temperature" placeholder="°C" onChange={handleChange}/>
</div>

<div className="metric-card">
<h3>Dust Level</h3>
<input name="dust" placeholder="%" onChange={handleChange}/>
</div>

<div className="metric-card">
<h3>Battery Health</h3>
<input name="battery" placeholder="%" onChange={handleChange}/>
</div>

<div className="metric-card">
<h3>Humidity</h3>
<input name="humidity" placeholder="%" onChange={handleChange}/>
</div>

</div>

)

}


