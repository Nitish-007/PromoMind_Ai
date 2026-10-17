"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  User,
  Mail,
  Lock,
  LogIn,
  UserPlus,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Phone,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { signInUser, signUpUser } from "@/lib/api";

export function UserAuthModal({
  isOpen,
  onClose,
  onUserAuthenticated,
  initialMode = "signin", // "signin" | "signup"
}) {
  const [authMode, setAuthMode] = useState(initialMode); // "signin" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    if (isOpen) {
      setErrorMsg("");
      setSuccessMsg("");
      // Pre-fill last logged-in email if available
      if (typeof window !== "undefined") {
        const cachedUser = localStorage.getItem("promomind_user");
        if (cachedUser) {
          try {
            const u = JSON.parse(cachedUser);
            if (u.email && !email) setEmail(u.email);
          } catch (_) {}
        }
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  async function handleSignIn(e) {
    if (e) e.preventDefault();
    if (!email.trim() || !password) {
      setErrorMsg("Please enter both email and password.");
      return;
    }
    setSubmitting(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const res = await signInUser({
        email: email.trim(),
        password,
      });

      if (res && res.user) {
        if (typeof window !== "undefined") {
          localStorage.setItem("promomind_user", JSON.stringify(res.user));
          localStorage.setItem("promomind_logged_in", "true");
          if (res.active_store_id) {
            localStorage.setItem("promomind_store_id", res.active_store_id);
          }
          if (res.profile) {
            localStorage.setItem("promomind_store_name", res.profile.store_name || "");
            localStorage.setItem("promomind_owner_name", res.profile.owner_name || "");
            localStorage.setItem("promomind_city", res.profile.city || "");
            localStorage.setItem("promomind_region", res.profile.region || "");
            localStorage.setItem("promomind_phone", res.profile.phone || "");
          }
        }

        setSuccessMsg(`Welcome back, ${res.user.full_name}!`);
        setTimeout(() => {
          if (onUserAuthenticated) {
            onUserAuthenticated(res.user, res.profile);
          }
          onClose();
        }, 500);
      }
    } catch (err) {
      setErrorMsg(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSignUp(e) {
    if (e) e.preventDefault();
    if (!fullName.trim()) {
      setErrorMsg("Please enter your full name.");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setErrorMsg("Please enter a valid email address.");
      return;
    }
    if (!password || password.length < 4) {
      setErrorMsg("Password must be at least 4 characters.");
      return;
    }

    setSubmitting(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const res = await signUpUser({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        phone: phone.trim() || undefined,
      });

      if (res && res.user) {
        if (typeof window !== "undefined") {
          localStorage.setItem("promomind_user", JSON.stringify(res.user));
          localStorage.setItem("promomind_logged_in", "true");
          if (res.active_store_id) {
            localStorage.setItem("promomind_store_id", res.active_store_id);
          }
          if (res.profile) {
            localStorage.setItem("promomind_store_name", res.profile.store_name || "");
            localStorage.setItem("promomind_owner_name", res.profile.owner_name || "");
            localStorage.setItem("promomind_city", res.profile.city || "");
            localStorage.setItem("promomind_region", res.profile.region || "");
          }
        }

        setSuccessMsg(`Account created! Welcome, ${res.user.full_name}.`);
        setTimeout(() => {
          if (onUserAuthenticated) {
            onUserAuthenticated(res.user, res.profile);
          }
          onClose();
        }, 600);
      }
    } catch (err) {
      setErrorMsg(err.message || "Sign up failed. Please try a different email.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleQuickDemoLogin() {
    setEmail("admin@promomind.ai");
    setPassword("admin123");
    setErrorMsg("");
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl transition-all">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          title="Close"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Header */}
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-foreground text-background font-bold text-xl shadow-md">
            PM
          </div>
          <h2 className="text-xl font-bold tracking-tight text-foreground font-heading">
            {authMode === "signin" ? "Sign In to PromoMind AI" : "Create Retailer Account"}
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            {authMode === "signin"
              ? "Access your demand forecasts, AI copilot & store portfolio"
              : "Set up your user account; configure your stores anytime under Profile"}
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="grid grid-cols-2 gap-1 rounded-lg bg-muted p-1 mb-5">
          <button
            type="button"
            onClick={() => {
              setAuthMode("signin");
              setErrorMsg("");
            }}
            className={`flex items-center justify-center gap-1.5 rounded-md py-2 text-xs font-semibold transition-all ${
              authMode === "signin"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <LogIn className="h-3.5 w-3.5" />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setAuthMode("signup");
              setErrorMsg("");
            }}
            className={`flex items-center justify-center gap-1.5 rounded-md py-2 text-xs font-semibold transition-all ${
              authMode === "signup"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <UserPlus className="h-3.5 w-3.5" />
            Sign Up
          </button>
        </div>

        {/* Status Alerts */}
        {errorMsg && (
          <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Sign In Form */}
        {authMode === "signin" && (
          <form onSubmit={handleSignIn} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@retailer.com"
                  className="pl-9 text-xs"
                  required
                  autoFocus
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-foreground">
                  Password
                </label>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-9 text-xs"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full text-xs font-semibold h-10 gap-2 mt-2"
            >
              {submitting ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <LogIn className="h-4 w-4" />
                  Sign In
                </>
              )}
            </Button>
          </form>
        )}

        {/* Sign Up Form */}
        {authMode === "signup" && (
          <form onSubmit={handleSignUp} className="space-y-3.5">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ramesh Sharma"
                  className="pl-9 text-xs"
                  required
                  autoFocus
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ramesh@retailer.com"
                  className="pl-9 text-xs"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1">
                Phone Number <span className="text-muted-foreground font-normal">(Optional)</span>
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98450 12345"
                  className="pl-9 text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 4 characters"
                  className="pl-9 text-xs"
                  required
                />
              </div>
            </div>

            <div className="rounded-lg bg-muted/50 p-2.5 text-[11px] text-muted-foreground flex items-start gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0 text-foreground/70 mt-0.5" />
              <span>
                Store configuration (region, format, working capital) will be customized under your <strong>Profile</strong> tab after signing in.
              </span>
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full text-xs font-semibold h-10 gap-2 mt-1"
            >
              {submitting ? (
                <span>Creating Account...</span>
              ) : (
                <>
                  <UserPlus className="h-4 w-4" />
                  Create Account
                </>
              )}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}

// Backwards-compatible alias for any existing imports
export const LoginStoreModal = UserAuthModal;

