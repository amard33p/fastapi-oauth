import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AuthService, UsersService } from "../client";

export default function Login() {
	const [loggedIn, setLoggedIn] = useState(null);
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState("");
	const navigate = useNavigate();
	const location = useLocation();
	const from = location.state?.from?.pathname || "/";

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

	const handleUsernameLogin = async (e) => {
		e.preventDefault();
		setSubmitting(true);
		setError("");
		try {
			await AuthService.cookieLoginApiV1AuthCookieLoginPost({
				formData: {
					username: email,
					password,
				},
			});
			navigate(from, { replace: true });
		} catch (err) {
			setError(
				err?.message ||
					"Login failed. Please check your credentials and try again.",
			);
		} finally {
			setSubmitting(false);
		}
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
				<>
					<form onSubmit={handleUsernameLogin} style={{ marginBottom: 16 }}>
						<div style={{ marginBottom: 8 }}>
							<label>
								Email
								<input
									type="email"
									value={email}
									onChange={(e) => setEmail(e.target.value)}
									required
									style={{ marginLeft: 8 }}
								/>
							</label>
						</div>
						<div style={{ marginBottom: 8 }}>
							<label>
								Password
								<input
									type="password"
									value={password}
									onChange={(e) => setPassword(e.target.value)}
									required
									style={{ marginLeft: 8 }}
								/>
							</label>
						</div>
						{error && (
							<div style={{ color: "#b00", marginBottom: 8 }}>{error}</div>
						)}
						<button type="submit" disabled={submitting}>
							{submitting ? "Signing in…" : "Sign in"}
						</button>
					</form>

					<div style={{ margin: "8px 0" }}>— or —</div>

					<button type="button" onClick={handleLogin}>
						Continue with Google
					</button>
				</>
			)}
		</div>
	);
}
