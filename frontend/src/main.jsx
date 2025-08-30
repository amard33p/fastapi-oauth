import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";

import { OpenAPI } from "./client";

OpenAPI.BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
OpenAPI.WITH_CREDENTIALS = true;

createRoot(document.getElementById("root")).render(
	<React.StrictMode>
		<BrowserRouter>
			<App />
		</BrowserRouter>
	</React.StrictMode>,
);
