import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { ApiError } from "../api";
import { IconLogo } from "../components/icons";

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("alice@demo.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) navigate("/", { replace: true });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="center">
      <form className="login-card" onSubmit={onSubmit}>
        <div className="login-brand">
          <IconLogo size={26} />
          Ajaia<span className="brand-accent"> Docs</span>
        </div>
        <h1>Sign in</h1>
        <p className="muted">Welcome back — sign in to your workspace.</p>

        <div className="field">
          <label className="label">Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoFocus />
        </div>
        <div className="field">
          <label className="label">Password</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
        </div>

        {error && <div className="error">{error}</div>}

        <button className="btn-primary full" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>

        <div className="seed-hint">
          <strong>Demo accounts</strong> (password <code>password123</code>):
          <br />
          <code>alice@demo.com</code> · <code>bob@demo.com</code> · <code>carol@demo.com</code>
          <br />
          Alice shares a document with Bob so you can see the sharing flow.
        </div>
      </form>
    </div>
  );
}
