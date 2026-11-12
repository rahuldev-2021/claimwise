import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./auth/AuthProvider";
import { ThemeProvider } from "./components/ThemeProvider";
import { RouteErrorBoundary } from "./components/RouteErrorBoundary";
import { AppRoutes } from "./routes";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <AuthProvider>
            <RouteErrorBoundary>
              <AppRoutes />
            </RouteErrorBoundary>
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
