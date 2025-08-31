import React, { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { UsersService } from "./client";
import Home from "./pages/Home";
import Login from "./pages/Login";
import OAuthCallback from "./pages/OAuthCallback";

function RequireAuth({ children }) {
	const [status, setStatus] = useState("loading");
	const location = useLocation();
	useEffect(() => {
		let mounted = true;
		UsersService.currentUserApiV1UsersMeGet()
			.then(() => mounted && setStatus("ok"))
			.catch(() => mounted && setStatus("noauth"));
		return () => {
			mounted = false;
		};
	}, []);
	if (status === "loading") return <div>Loading...</div>;
	if (status === "noauth")
		return <Navigate to="/login" replace state={{ from: location }} />;
	return children;
}

export default function App() {
	return (
		<div style={{ fontFamily: "system-ui, Arial", padding: 24 }}>
			<nav style={{ marginBottom: 20 }}>
				<Link to="/">Home</Link> | <Link to="/login">Login</Link>
			</nav>
			<Routes>
				<Route path="/login" element={<Login />} />
				<Route path="/oauth-callback" element={<OAuthCallback />} />
				<Route
					path="/"
					element={
						<RequireAuth>
							<Home />
						</RequireAuth>
					}
				/>
			</Routes>
		</div>
	);
}
