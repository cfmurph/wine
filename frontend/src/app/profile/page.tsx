"use client";

import { useState } from "react";
import { User, LogIn, UserPlus, LogOut } from "lucide-react";
import { login, logout, register } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function ProfilePage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(
    typeof window !== "undefined" && !!localStorage.getItem("access_token")
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      if (mode === "login") {
        await login(email, password);
        setIsLoggedIn(true);
        setSuccess("Logged in successfully.");
      } else {
        await register(email, username, password);
        setSuccess("Account created. Please log in.");
        setMode("login");
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Something went wrong.");
    }
  };

  const handleLogout = () => {
    logout();
    setIsLoggedIn(false);
    setSuccess("Logged out.");
  };

  if (isLoggedIn) {
    return (
      <div className="max-w-sm mx-auto space-y-6 py-8">
        <div className="text-center space-y-2">
          <div className="w-16 h-16 rounded-full bg-wine-100 flex items-center justify-center mx-auto">
            <User className="h-8 w-8 text-wine-700" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Your Profile</h1>
          <p className="text-gray-500 text-sm">You are logged in.</p>
          {success && <p className="text-green-600 text-sm">{success}</p>}
        </div>
        <Button variant="danger" className="w-full" onClick={handleLogout}>
          <LogOut className="h-4 w-4" />
          Log out
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto py-8">
      <Card className="p-8 space-y-6">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-wine-100 flex items-center justify-center mx-auto mb-4">
            <User className="h-8 w-8 text-wine-700" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {mode === "login" ? "Welcome back" : "Create account"}
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
          />
          {mode === "register" && (
            <Input
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="wineenthusiast"
            />
          )}
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••"
          />

          {error && <p className="text-sm text-red-600">{error}</p>}
          {success && <p className="text-sm text-green-600">{success}</p>}

          <Button type="submit" className="w-full" size="lg">
            {mode === "login" ? (
              <>
                <LogIn className="h-4 w-4" /> Log in
              </>
            ) : (
              <>
                <UserPlus className="h-4 w-4" /> Create account
              </>
            )}
          </Button>
        </form>

        <div className="text-center text-sm text-gray-500">
          {mode === "login" ? (
            <>
              No account?{" "}
              <button
                onClick={() => setMode("register")}
                className="text-wine-700 hover:underline font-medium"
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => setMode("login")}
                className="text-wine-700 hover:underline font-medium"
              >
                Log in
              </button>
            </>
          )}
        </div>
      </Card>
    </div>
  );
}
