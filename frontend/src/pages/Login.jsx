import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AuthService, UsersService } from "../client";

export default function Login() {
	const [loggedIn, setLoggedIn] = useState(null);

	useEffect(() => {
		let mounted = true;
		UsersService.currentUserApiV1UsersMeGet()
			.then(() => mounted && setLoggedIn(true))
			.catch(() => mounted && setLoggedIn(false));
		return () => {
			mounted = false;
		};
	}, []);

	const handleLogin = async () => {
		const res =
			await AuthService.oauthGoogleCookieOauthAuthorizeApiV1AuthGoogleAuthorizeGet();
		if (!res?.authorization_url)
			throw new Error("authorization_url not returned by backend");
		window.location.assign(res.authorization_url);
	};

	return (
		<div>
			<h1>Login</h1>
			{loggedIn === null ? (
				<p>Checking your session…</p>
			) : loggedIn ? (
				<p>
					You are already logged in. Go to <Link to="/">Home</Link>.
				</p>
			) : (
				<button type="button" onClick={handleLogin}>
					Login with Google
				</button>
			)}
		</div>
	);
}
