import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";

// Import components directly to avoid lazy loading issues
import AdminDashboard from "@/pages/AdminDashboard";
import DealerPortal from "@/pages/DealerPortal";
import TestAuth from "@/pages/TestAuth";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <ErrorBoundary>
      <Switch>
        <Route path="/" component={() => <DealerPortal />} />
        <Route path="/admin" component={() => <AdminDashboard />} />
        <Route path="/dealer-portal" component={() => <DealerPortal />} />
        <Route path="/test-auth" component={() => <TestAuth />} />
        <Route component={() => <NotFound />} />
      </Switch>
    </ErrorBoundary>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;