"use client";

import { Component, useState, type FormEvent } from "react";
import {
  ApiError,
  getMe,
  hasToken,
  login,
  logout,
  setUnauthorizedHandler,
  type CurrentUser,
} from "./api";

type AppUIState = {
  phase: "loading" | "login" | "ready";
  message: string;
  user: CurrentUser | null;
};

export class AppUI extends Component<object, AppUIState> {
  state: AppUIState = { phase: "loading", message: "", user: null };

  componentDidMount() {
    setUnauthorizedHandler(() =>
      this.showLogin("Your session has expired. Sign in again."),
    );
    if (hasToken()) {
      this.loadUser();
    } else {
      this.showLogin();
    }
  }

  componentWillUnmount() {
    setUnauthorizedHandler(null);
  }

  private showLogin(message = "") {
    this.setState({ phase: "login", message, user: null });
  }

  private loadUser = () =>
    getMe()
      .then((user) => this.setState({ phase: "ready", message: "", user }))
      .catch((error: Error) => {
        if (error instanceof ApiError && error.status === 401) return;
        this.showLogin(error.message);
      });

  private signOut = () => {
    logout();
    window.history.replaceState(null, "", window.location.pathname);
    this.showLogin();
  };

  render() {
    const { phase, message, user } = this.state;

    if (phase === "loading") return <p className="loading">Loading...</p>;
    if (phase === "login" || !user) {
      return <LoginForm message={message} onLoggedIn={this.loadUser} />;
    }

    return (
      <header className="topbar">
        <span className="brand">Fleet</span>
        <span>{user.username}</span>
        <div className="topbar-actions">
          <button type="button" className="link-button" onClick={this.signOut}>
            Sign out
          </button>
        </div>
      </header>
    );
  }
}

function LoginForm({
  message,
  onLoggedIn,
}: {
  message: string;
  onLoggedIn: () => Promise<void>;
}) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError("");
    setPending(true);
    login(String(form.get("username")), String(form.get("password")))
      .then(onLoggedIn)
      .catch((e: Error) => setError(e.message))
      .finally(() => setPending(false));
  };

  return (
    <main className="login">
      <h1>Fleet</h1>
      <form onSubmit={submit}>
        <label>
          Username
          <input name="username" autoComplete="username" required />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
        </label>
        {(error || message) && (
          <p className="error" role="alert">
            {error || message}
          </p>
        )}
        <button type="submit" disabled={pending}>
          Sign in
        </button>
      </form>
    </main>
  );
}
