"use client";

import { Component, useEffect, useState, type FormEvent } from "react";
import {
  ApiError,
  getMe,
  hasToken,
  login,
  logout,
  setUnauthorizedHandler,
} from "./api";
import { RoleUIFactory } from "./factories";
import type { ProfilePage, Role, Workspace } from "./products";
import { useHash } from "./shared/useHash";

type AppUIState = {
  phase: "loading" | "login" | "ready";
  message: string;
};

export class AppUI extends Component<object, AppUIState> {
  private factory: RoleUIFactory | null = null;

  state: AppUIState = { phase: "loading", message: "" };

  componentDidMount() {
    setUnauthorizedHandler(() =>
      this.showLogin("Сесія завершилася. Увійдіть знову."),
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

  start(role: Role) {
    this.factory = RoleUIFactory.forRole(role);
    this.setState({ phase: "ready", message: "" });
  }

  private showLogin(message = "") {
    this.factory = null;
    this.setState({ phase: "login", message });
  }

  private loadUser = () =>
    getMe()
      .then((user) => this.start(user.role))
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
    const { phase, message } = this.state;

    if (phase === "loading") return <p className="loading">Завантаження...</p>;
    if (phase === "login" || !this.factory) {
      return <LoginForm message={message} onLoggedIn={this.loadUser} />;
    }

    return (
      <>
        <header className="topbar">
          <span className="brand">Автопарк</span>
          {this.factory.createMenu().render()}
          <div className="topbar-actions">
            <button type="button" onClick={this.signOut}>
              Вийти
            </button>
          </div>
        </header>
        <Screen
          profile={this.factory.createProfilePage()}
          workspace={this.factory.createWorkspace()}
        />
      </>
    );
  }
}

function Screen({
  profile,
  workspace,
}: {
  profile: ProfilePage;
  workspace: Workspace;
}) {
  const hash = useHash();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [hash]);

  return (
    <main>{hash === "profile" ? profile.render() : workspace.render()}</main>
  );
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
      <h1>Автопарк</h1>
      <form onSubmit={submit}>
        <label>
          Ім’я користувача
          <input name="username" autoComplete="username" required />
        </label>
        <label>
          Пароль
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
          Увійти
        </button>
      </form>
    </main>
  );
}
