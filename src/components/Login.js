import React from "react";
import "./Login.css";

export default function Login({onLogin}){

return(

<div className="login-container">

<div className="login-card">

<h1 className="login-logo">DeviceGuard</h1>

<p className="login-tag">
AI Powered Device Security
</p>

<input type="text" placeholder="Full Name"/>

<input type="email" placeholder="Email Address"/>

<input type="password" placeholder="Password"/>

<button className="login-btn" onClick={onLogin}>
Login
</button>

</div>

</div>

)

}