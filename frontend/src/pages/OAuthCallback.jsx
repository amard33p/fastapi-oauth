import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UsersService } from "../client";

export default function OAuthCallback() {
	const navigate = useNavigate();
	const [status, setStatus] = useState("Processing login...");

	useEffect(() => {
		const run = async () => {
			try {
				// After backend OAuth callback, we should already have a cookie session.
				await UsersService.currentUserUsersMeGet();
				navigate("/", { replace: true });
			} catch (e) {
				setStatus(`Login failed or session not found. ${e?.message || e}`);
			}
		};
		run();
	}, [navigate]);

	return (
		<div>
			<h1>OAuth Callback</h1>
			<p>{status}</p>
		</div>
	);
}
