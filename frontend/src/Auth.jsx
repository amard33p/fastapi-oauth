import React, { useEffect, useState } from "react";
import { AuthService, UsersService } from "./client";

export default function Auth() {
	const [user, setUser] = useState(null);

	useEffect(() => {
		const checkUser = async () => {
			try {
				const userData = await UsersService.currentUserApiV1UsersMeGet();
				setUser(userData);
			} catch (error) {
				setUser(null);
			}
		};

		checkUser();
	}, []);

	const handleLogin = async () => {
		const res =
			await AuthService.oauthGoogleCookieOauthAuthorizeApiV1AuthGoogleAuthorizeGet();
		if (!res?.authorization_url)
			throw new Error("authorization_url not returned");
		window.location.assign(res.authorization_url);
	};

	const handleLogout = async () => {
		try {
			await AuthService.cookieOauthLogoutApiV1AuthCookieLogoutPost();
		} catch (_) {
			// ignore
		}
		window.location.assign("/login");
	};

	return (
		<div>
			{user ? (
				<>
					<p>Welcome, {user.email}!</p>
					<button type="button" onClick={handleLogout}>
						Logout
					</button>
				</>
			) : (
				<button type="button" onClick={handleLogin}>
					Login with Google
				</button>
			)}
		</div>
	);
}
