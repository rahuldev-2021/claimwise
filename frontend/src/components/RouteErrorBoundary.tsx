import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class RouteErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("CLAIMWISE route error", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-base px-4 text-center">
          <h1 className="text-lg font-semibold text-text">Something went wrong</h1>
          <p className="max-w-md text-[13px] text-text-muted">{this.state.error.message}</p>
          {this.state.error.stack ? (
            <pre className="max-h-40 max-w-lg overflow-auto rounded border border-border bg-base-deep p-2 text-left text-[10px] text-text-faint">
              {this.state.error.stack.split("\n").slice(0, 8).join("\n")}
            </pre>
          ) : null}
          <Link to="/" className="text-[13px] font-medium text-primary hover:underline">
            Back to home
          </Link>
        </div>
      );
    }
    return this.props.children;
  }
}
