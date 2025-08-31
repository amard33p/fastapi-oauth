import React, { useState } from "react";
import Auth from "../Auth.jsx";
import { DefaultService } from "../client";

export default function Home() {
	const [message, setMessage] = useState("");

	const callProtected = async () => {
		try {
			const data =
				await DefaultService.authenticatedRouteApiV1AuthenticatedRouteGet();
			setMessage(typeof data === "string" ? data : JSON.stringify(data));
		} catch (e) {
			setMessage(String(e));
		}
	};

	return (
		<div>
			<h1>Home</h1>
			<Auth />
			<div style={{ marginTop: 16 }}>
				<button type="button" onClick={callProtected}>
					Call /authenticated-route
				</button>
				{message && (
					<pre style={{ background: "#f7f7f7", padding: 12, marginTop: 12 }}>
						{message}
					</pre>
				)}
			</div>
		</div>
	);
}
