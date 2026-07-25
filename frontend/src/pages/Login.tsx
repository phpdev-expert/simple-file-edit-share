import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { ApiError } from "../api";

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
        <div className="login-kicker">Collaborative Docs</div>
        <h1>
          Ajaia <em>Docs</em>
        </h1>
        <p className="muted small">A calm place to write, share, and ship together.</p>

        <div className="field">
          <label className="label">Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoFocus />
        </div>
        <div className="field">
          <label className="label">Password</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
        </div>

        {error && <div className="error">{error}</div>}

        <button className="primary" style={{ width: "100%", marginTop: "0.5rem" }} disabled={busy}>
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
