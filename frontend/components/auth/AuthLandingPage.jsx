"use client";

import React, { useState, useEffect, useRef } from "react";
import {
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
  BarChart3,
  Calendar,
  MessageSquare,
  TrendingUp,
  Zap,
  Brain,
  Radio,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { signInUser, signUpUser } from "@/lib/api";

const CAPABILITIES = [
  {
    id: "forecast",
    icon: BarChart3,
    title: "Demand Forecasting",
    shortTitle: "Forecasting",
    desc: "Predictive time-series analytics for inventory optimization",
    liveDetail: "Holt-Winters double exponential smoothing forecasting 4-week sales velocities",
    colorHex: "#60a5fa",
    color: "text-blue-400",
    border: "border-blue-500/40",
    bg: "bg-blue-500/10",
    glow: "rgba(96,165,250,0.5)",
    pathEnd: { x: 25, y: 18 },
  },
  {
    id: "copilot",
    icon: MessageSquare,
    title: "AI Sales Copilot",
    shortTitle: "Sales Copilot",
    desc: "Real-time conversational commerce intelligence",
    liveDetail: "Live retail reasoning with dynamic inventory grounding & margin solvers",
    colorHex: "#34d399",
    color: "text-emerald-400",
    border: "border-emerald-500/40",
    bg: "bg-emerald-500/10",
    glow: "rgba(52,211,153,0.5)",
    pathEnd: { x: 75, y: 18 },
  },
  {
    id: "events",
    icon: Calendar,
    title: "Event Discovery",
    shortTitle: "Event Discovery",
    desc: "Worldwide live AI-powered market trend detection",
    liveDetail: "Google Vertex AI live search uncovering regional festive surges & trends",
    colorHex: "#fbbf24",
    color: "text-amber-400",
    border: "border-amber-500/40",
    bg: "bg-amber-500/10",
    glow: "rgba(251,191,36,0.5)",
    pathEnd: { x: 25, y: 82 },
  },
  {
    id: "capital",
    icon: TrendingUp,
    title: "Capital Intelligence",
    shortTitle: "Capital ROI",
    desc: "ROI predictor with interactive what-if simulations",
    liveDetail: "Live store capital profit simulator, dead-capital tracker & liquidity models",
    colorHex: "#c084fc",
    color: "text-purple-400",
    border: "border-purple-500/40",
    bg: "bg-purple-500/10",
    glow: "rgba(192,132,252,0.5)",
    pathEnd: { x: 75, y: 82 },
  },
];

const BRAND_LETTERS = "PromoMind".split("");
const AI_LETTERS = "AI".split("");

export function AuthLandingPage({ onUserAuthenticated }) {
  const [phase, setPhase] = useState("splash"); // "splash" | "auth" | "success"
  const [activeCap, setActiveCap] = useState(null); // null = nothing selected initially
  const [authMode, setAuthMode] = useState("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [brainBurst, setBrainBurst] = useState(false);
  const successProfileRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(() => setPhase("auth"), 3200);
    return () => clearTimeout(timer);
  }, []);

  function handleCapSelect(index) {
    // If already active, toggle off to null; otherwise activate selected index
    setActiveCap((prev) => (prev === index ? null : index));
  }

  function handleBrainClick() {
    setBrainBurst(true);
    setTimeout(() => setBrainBurst(false), 900);
    setActiveCap((prev) => (prev === null ? 0 : (prev + 1) % CAPABILITIES.length));
  }

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
      const res = await signInUser({ email: email.trim(), password });
      if (res && res.user) {
        if (typeof window !== "undefined") {
          localStorage.setItem("promomind_user", JSON.stringify(res.user));
          localStorage.setItem("promomind_logged_in", "true");
          if (res.active_store_id) localStorage.setItem("promomind_store_id", res.active_store_id);
          if (res.profile) {
            localStorage.setItem("promomind_store_name", res.profile.store_name || "");
            localStorage.setItem("promomind_owner_name", res.profile.owner_name || "");
            localStorage.setItem("promomind_city", res.profile.city || "");
            localStorage.setItem("promomind_region", res.profile.region || "");
            localStorage.setItem("promomind_phone", res.profile.phone || "");
          }
        }
        successProfileRef.current = res.profile;
        setSuccessMsg(`Welcome back, ${res.user.full_name}!`);
        setPhase("success");
        setTimeout(() => {
          if (onUserAuthenticated) onUserAuthenticated(res.user, res.profile);
        }, 1800);
      }
    } catch (err) {
      setErrorMsg(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSignUp(e) {
    if (e) e.preventDefault();
    if (!fullName.trim()) { setErrorMsg("Please enter your full name."); return; }
    if (!email.trim() || !email.includes("@")) { setErrorMsg("Please enter a valid email."); return; }
    if (!password || password.length < 4) { setErrorMsg("Password must be at least 4 characters."); return; }

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
          if (res.active_store_id) localStorage.setItem("promomind_store_id", res.active_store_id);
          if (res.profile) {
            localStorage.setItem("promomind_store_name", res.profile.store_name || "");
            localStorage.setItem("promomind_owner_name", res.profile.owner_name || "");
            localStorage.setItem("promomind_city", res.profile.city || "");
            localStorage.setItem("promomind_region", res.profile.region || "");
          }
        }
        successProfileRef.current = res.profile;
        setSuccessMsg(`Account created! Welcome, ${res.user.full_name}.`);
        setPhase("success");
        setTimeout(() => {
          if (onUserAuthenticated) onUserAuthenticated(res.user, res.profile);
        }, 1800);
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

  const currCap = activeCap !== null ? CAPABILITIES[activeCap] : null;
  const brainColor = currCap ? currCap.colorHex : "#94a3b8";
  const brainGlow = currCap ? currCap.glow : "rgba(255,255,255,0.06)";

  return (
    <div className="fixed inset-0 z-[100] bg-background overflow-y-auto">
      <style jsx>{`
        /* ── SPLASH LETTER ANIMATIONS ── */
        @keyframes letterDrop {
          0%   { opacity: 0; transform: translateY(-50px) rotate(-12deg) scale(0.5); filter: blur(6px); }
          60%  { opacity: 1; transform: translateY(4px) rotate(1deg) scale(1.05); filter: blur(0); }
          80%  { transform: translateY(-2px) rotate(-0.5deg) scale(0.98); }
          100% { opacity: 1; transform: translateY(0) rotate(0) scale(1); filter: blur(0); }
        }
        @keyframes letterSlideIn {
          0%   { opacity: 0; transform: translateX(30px) scale(0.7); filter: blur(4px); }
          70%  { opacity: 1; transform: translateX(-2px) scale(1.03); filter: blur(0); }
          100% { opacity: 1; transform: translateX(0) scale(1); filter: blur(0); }
        }
        @keyframes taglineFadeInSmooth {
          0%   { opacity: 0; }
          100% { opacity: 1; }
        }
        @keyframes logoPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(255,255,255,0.08); transform: scale(1); }
          50%      { box-shadow: 0 0 50px 12px rgba(255,255,255,0.05); transform: scale(1.03); }
        }
        @keyframes dotBounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.3; }
          40%            { transform: translateY(-6px); opacity: 1; }
        }

        /* ── AUTH PHASE ── */
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(28px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-20px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        /* ── NEURAL PULSE TRAVEL ANIMATION ── */
        @keyframes flowBeam {
          from { stroke-dashoffset: 24; }
          to   { stroke-dashoffset: 0; }
        }
        @keyframes pulseRing {
          0%   { transform: scale(0.95); opacity: 0.8; }
          50%  { transform: scale(1.15); opacity: 0.3; }
          100% { transform: scale(0.95); opacity: 0.8; }
        }
        @keyframes orbitRotate {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }

        /* ── SUCCESS ── */
        @keyframes successZoom {
          0%   { opacity: 0; transform: scale(0.6); }
          50%  { opacity: 1; transform: scale(1.08); }
          100% { opacity: 1; transform: scale(1); }
        }
        @keyframes successRing {
          0%   { transform: scale(0.8); opacity: 0; box-shadow: 0 0 0 0 rgba(74,222,128,0.4); }
          50%  { transform: scale(1); opacity: 1; box-shadow: 0 0 0 16px rgba(74,222,128,0); }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes successText {
          0%   { opacity: 0; transform: translateY(12px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes screenFadeOut {
          0%   { opacity: 1; transform: scale(1); }
          100% { opacity: 0; transform: scale(1.04); filter: blur(4px); }
        }
        @keyframes progressFill {
          from { width: 0; }
          to   { width: 100%; }
        }

        @keyframes gradientShift {
          0%   { background-position: 0% 50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }

        .splash-letter { display: inline-block; opacity: 0; animation: letterDrop 0.6s cubic-bezier(0.34,1.56,0.64,1) forwards; }
        .ai-letter     { display: inline-block; opacity: 0; animation: letterSlideIn 0.5s cubic-bezier(0.34,1.56,0.64,1) forwards; }
        .splash-tagline {
          opacity: 0;
          animation: taglineFadeInSmooth 0.8s ease-out 2.0s forwards;
          will-change: opacity;
        }
        .splash-logo   { animation: logoPulse 3s ease-in-out infinite; }
        .loading-dot   { animation: dotBounce 1.2s ease-in-out infinite; }

        .auth-fadeInUp  { opacity: 0; animation: fadeInUp 0.7s ease-out forwards; }
        .auth-slideDown { opacity: 0; animation: slideDown 0.5s ease-out forwards; }

        .beam-flow {
          stroke-dasharray: 6 3;
          animation: flowBeam 0.7s linear infinite;
        }

        .orbit-rotate {
          animation: orbitRotate 18s linear infinite;
        }

        .success-icon  { animation: successZoom 0.6s cubic-bezier(0.34,1.56,0.64,1) forwards; }
        .success-ring  { animation: successRing 1s ease-out forwards; }
        .success-text  { opacity: 0; animation: successText 0.5s ease-out 0.4s forwards; }
        .success-sub   { opacity: 0; animation: successText 0.5s ease-out 0.7s forwards; }
        .success-fade  { animation: screenFadeOut 0.6s ease-in 1.2s forwards; }
        .progress-bar  { animation: progressFill 1.2s ease-out 0.5s forwards; width: 0; }

        .gradient-bg {
          background: linear-gradient(135deg, hsl(var(--background)), hsl(var(--muted)), hsl(var(--background)));
          background-size: 400% 400%;
          animation: gradientShift 12s ease infinite;
        }

        /* ── TOGGLE GLOWS ── */
        .tab-glow-active {
          box-shadow: 0 0 16px 2px rgba(255, 255, 255, 0.18), 0 0 3px 1px rgba(255, 255, 255, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.25);
          border: 1px solid rgba(255, 255, 255, 0.3);
        }
      `}</style>

      <div className={`gradient-bg min-h-screen flex flex-col items-center justify-center px-4 py-8 relative ${phase === "success" ? "success-fade" : ""}`}>
        <div className="absolute inset-0 pointer-events-none opacity-[0.02]"
          style={{ backgroundImage: "radial-gradient(circle, hsl(var(--foreground)) 1px, transparent 1px)", backgroundSize: "32px 32px" }} />

        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* ▶  SPLASH — Letter Assembly (Fixed Zero Vertical Shift Tagline) */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        {phase === "splash" && (
          <div className="flex flex-col items-center gap-8">
            <div className="splash-logo h-20 w-20 rounded-2xl bg-foreground text-background flex items-center justify-center text-3xl font-bold tracking-tight shadow-2xl">
              PM
            </div>
            <div className="text-center">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight font-heading">
                {BRAND_LETTERS.map((char, i) => (
                  <span key={`b-${i}`} className="splash-letter text-foreground"
                    style={{ animationDelay: `${300 + i * 90}ms` }}>{char}</span>
                ))}
                <span className="inline-block w-3 sm:w-4" />
                {AI_LETTERS.map((char, i) => (
                  <span key={`a-${i}`} className="ai-letter text-muted-foreground font-medium"
                    style={{ animationDelay: `${300 + BRAND_LETTERS.length * 90 + 200 + i * 120}ms` }}>{char}</span>
                ))}
              </h1>

              {/* Fixed: Pure opacity fade-in with steady layout, no wrapping jumps */}
              <div className="mt-4 min-h-[32px] flex items-center justify-center">
                <p className="splash-tagline text-muted-foreground text-base sm:text-lg max-w-lg mx-auto leading-normal tracking-wide whitespace-normal sm:whitespace-nowrap">
                  AI Demand &amp; Profit Optimization for Retail &amp; Commerce
                </p>
              </div>
            </div>

            <div className="flex gap-2.5 mt-2">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-2 w-2 rounded-full bg-foreground/30 loading-dot"
                  style={{ animationDelay: `${2400 + i * 180}ms` }} />
              ))}
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* ▶  AUTH — AI Brain Centerpiece with Neural Paths to 4 Buttons    */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        {phase === "auth" && (
          <div className="w-full max-w-5xl flex flex-col lg:flex-row items-center gap-10 lg:gap-14 relative z-10">

            {/* ── Left: Interactive Neural Brain Hub ── */}
            <div className="flex-1 w-full auth-fadeInUp">
              {/* Brand Header */}
              <div className="flex items-center gap-3 justify-center lg:justify-start mb-6">
                <div className="h-11 w-11 rounded-xl bg-foreground text-background flex items-center justify-center text-lg font-bold shadow-lg">
                  PM
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-heading">
                    PromoMind <span className="text-muted-foreground font-medium">AI</span>
                  </h1>
                  <p className="text-[11px] text-muted-foreground tracking-wide uppercase font-semibold">
                    AI Demand &amp; Profit Optimization for Retail &amp; Commerce
                  </p>
                </div>
              </div>

              {/* ── Centralized Brain + Surrounding 4 Capability Buttons Cluster ── */}
              <div className="relative w-full max-w-lg mx-auto rounded-2xl border border-border/60 bg-card/40 backdrop-blur-md p-4 sm:p-5 overflow-hidden shadow-xl">

                {/* SVG Neural Conduits Canvas Overlay (Connecting Center to 4 Corners) */}
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none z-0"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                >
                  <defs>
                    <radialGradient id="brainCoreGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor={brainColor} stopOpacity={currCap ? "0.3" : "0.06"} />
                      <stop offset="100%" stopColor={brainColor} stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  {/* Ambient background glow from brain */}
                  <circle cx="50" cy="50" r="28" fill="url(#brainCoreGlow)" />

                  {/* 4 Inactive baseline conduits (Subtle resting tracks) */}
                  <line x1="50" y1="50" x2="25" y2="20" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" className="text-border/30" />
                  <line x1="50" y1="50" x2="75" y2="20" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" className="text-border/30" />
                  <line x1="50" y1="50" x2="25" y2="80" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" className="text-border/30" />
                  <line x1="50" y1="50" x2="75" y2="80" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" className="text-border/30" />

                  {/* ACTIVE BEAM — ONLY DRAWN WHEN USER CLICKS A BUTTON OR BRAIN */}
                  {CAPABILITIES.map((cap, i) => {
                    const isActive = activeCap === i || brainBurst;
                    if (!isActive) return null;
                    return (
                      <g key={cap.id}>
                        {/* Outer Glow Line */}
                        <line
                          x1="50"
                          y1="50"
                          x2={cap.pathEnd.x}
                          y2={cap.pathEnd.y}
                          stroke={cap.colorHex}
                          strokeWidth="4"
                          strokeOpacity="0.4"
                          vectorEffect="non-scaling-stroke"
                          style={{ filter: `drop-shadow(0 0 6px ${cap.colorHex})` }}
                        />
                        {/* Core Animated Laser Beam */}
                        <line
                          x1="50"
                          y1="50"
                          x2={cap.pathEnd.x}
                          y2={cap.pathEnd.y}
                          stroke={cap.colorHex}
                          strokeWidth="2.5"
                          vectorEffect="non-scaling-stroke"
                          className="beam-flow"
                          style={{ filter: `drop-shadow(0 0 3px #ffffff)` }}
                        />
                        {/* Traveling Synapse Pulse Dot */}
                        <circle
                          cx={cap.pathEnd.x}
                          cy={cap.pathEnd.y}
                          r="3"
                          fill="#ffffff"
                          stroke={cap.colorHex}
                          strokeWidth="1.5"
                          vectorEffect="non-scaling-stroke"
                          style={{ filter: `drop-shadow(0 0 5px ${cap.colorHex})` }}
                        />
                      </g>
                    );
                  })}
                </svg>

                {/* ── ROW 1: TOP 2 BUTTONS ── */}
                <div className="grid grid-cols-2 gap-3 sm:gap-4 relative z-10">
                  {/* Button 0: Demand Forecasting */}
                  <button
                    type="button"
                    onClick={() => handleCapSelect(0)}
                    className={`relative p-3 sm:p-3.5 rounded-xl border text-left transition-all duration-300 backdrop-blur-sm cursor-pointer group ${
                      activeCap === 0
                        ? "bg-blue-500/15 border-blue-400 scale-[1.02] shadow-lg"
                        : "bg-card/70 border-border hover:border-blue-400/50 hover:bg-muted/40"
                    }`}
                    style={activeCap === 0 ? { boxShadow: `0 0 20px 2px ${CAPABILITIES[0].glow}` } : {}}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${activeCap === 0 ? "bg-blue-500 text-white shadow-md" : "bg-muted text-muted-foreground group-hover:text-foreground"}`}>
                        <BarChart3 className="h-4 w-4" />
                      </div>
                      {activeCap === 0 && (
                        <span className="flex h-2 w-2 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-bold text-foreground">Demand Forecasting</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5 line-clamp-1">Predictive time-series</div>
                  </button>

                  {/* Button 1: AI Sales Copilot */}
                  <button
                    type="button"
                    onClick={() => handleCapSelect(1)}
                    className={`relative p-3 sm:p-3.5 rounded-xl border text-left transition-all duration-300 backdrop-blur-sm cursor-pointer group ${
                      activeCap === 1
                        ? "bg-emerald-500/15 border-emerald-400 scale-[1.02] shadow-lg"
                        : "bg-card/70 border-border hover:border-emerald-400/50 hover:bg-muted/40"
                    }`}
                    style={activeCap === 1 ? { boxShadow: `0 0 20px 2px ${CAPABILITIES[1].glow}` } : {}}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${activeCap === 1 ? "bg-emerald-500 text-white shadow-md" : "bg-muted text-muted-foreground group-hover:text-foreground"}`}>
                        <MessageSquare className="h-4 w-4" />
                      </div>
                      {activeCap === 1 && (
                        <span className="flex h-2 w-2 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-bold text-foreground">AI Sales Copilot</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5 line-clamp-1">Conversational checkout</div>
                  </button>
                </div>

                {/* ── ROW 2: CENTER BRAIN ENGINE ── */}
                <div className="relative flex items-center justify-center my-3 sm:my-4 z-20">
                  <button
                    type="button"
                    onClick={handleBrainClick}
                    title="Click to cycle neural engine"
                    className="group relative flex flex-col items-center justify-center cursor-pointer focus:outline-none transition-transform duration-200 active:scale-95"
                  >
                    {/* Orbiting dashed ring */}
                    <div className="orbit-rotate absolute h-24 w-24 sm:h-28 sm:w-28 rounded-full border border-dashed border-foreground/15 pointer-events-none" />

                    {/* Outer Pulsing Aura */}
                    <div
                      className="absolute h-18 w-18 sm:h-20 sm:w-20 rounded-full transition-all duration-500 pointer-events-none"
                      style={{
                        boxShadow: `0 0 32px 8px ${brainGlow}`,
                        opacity: brainBurst ? 1 : 0.8,
                      }}
                    />

                    {/* Central Brain Node */}
                    <div
                      className="relative h-14 w-14 sm:h-16 sm:w-16 rounded-full bg-card border-2 flex flex-col items-center justify-center shadow-xl transition-all duration-300"
                      style={{
                        borderColor: brainColor,
                        boxShadow: currCap
                          ? `0 0 16px 3px ${currCap.glow}, inset 0 0 12px 2px ${currCap.glow}`
                          : "0 0 12px 1px rgba(255,255,255,0.06)",
                      }}
                    >
                      <Brain
                        className="h-6 w-6 sm:h-7 sm:w-7 transition-colors duration-300"
                        style={{ color: brainColor }}
                      />
                      <span className="text-[8px] font-black uppercase tracking-widest text-foreground mt-0.5">
                        AI Core
                      </span>
                    </div>

                    {/* Hint badge */}
                    <span className="text-[9px] font-semibold text-muted-foreground mt-1.5 opacity-70 group-hover:opacity-100 transition-opacity">
                      {currCap ? "Click Core to Cycle" : "Click Any Button"}
                    </span>
                  </button>
                </div>

                {/* ── ROW 3: BOTTOM 2 BUTTONS ── */}
                <div className="grid grid-cols-2 gap-3 sm:gap-4 relative z-10">
                  {/* Button 2: Event Discovery */}
                  <button
                    type="button"
                    onClick={() => handleCapSelect(2)}
                    className={`relative p-3 sm:p-3.5 rounded-xl border text-left transition-all duration-300 backdrop-blur-sm cursor-pointer group ${
                      activeCap === 2
                        ? "bg-amber-500/15 border-amber-400 scale-[1.02] shadow-lg"
                        : "bg-card/70 border-border hover:border-amber-400/50 hover:bg-muted/40"
                    }`}
                    style={activeCap === 2 ? { boxShadow: `0 0 20px 2px ${CAPABILITIES[2].glow}` } : {}}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${activeCap === 2 ? "bg-amber-500 text-white shadow-md" : "bg-muted text-muted-foreground group-hover:text-foreground"}`}>
                        <Calendar className="h-4 w-4" />
                      </div>
                      {activeCap === 2 && (
                        <span className="flex h-2 w-2 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-bold text-foreground">Event Discovery</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5 line-clamp-1">Worldwide festival trends</div>
                  </button>

                  {/* Button 3: Capital Intelligence */}
                  <button
                    type="button"
                    onClick={() => handleCapSelect(3)}
                    className={`relative p-3 sm:p-3.5 rounded-xl border text-left transition-all duration-300 backdrop-blur-sm cursor-pointer group ${
                      activeCap === 3
                        ? "bg-purple-500/15 border-purple-400 scale-[1.02] shadow-lg"
                        : "bg-card/70 border-border hover:border-purple-400/50 hover:bg-muted/40"
                    }`}
                    style={activeCap === 3 ? { boxShadow: `0 0 20px 2px ${CAPABILITIES[3].glow}` } : {}}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${activeCap === 3 ? "bg-purple-500 text-white shadow-md" : "bg-muted text-muted-foreground group-hover:text-foreground"}`}>
                        <TrendingUp className="h-4 w-4" />
                      </div>
                      {activeCap === 3 && (
                        <span className="flex h-2 w-2 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-bold text-foreground">Capital Intelligence</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5 line-clamp-1">ROI & dead-capital models</div>
                  </button>
                </div>

                {/* ── Active Capability Detail Capsule or Idle Hint ── */}
                {currCap ? (
                  <div
                    className="mt-4 p-2.5 rounded-xl border transition-all duration-300 flex items-center justify-between gap-2.5 animate-fadeIn"
                    style={{
                      backgroundColor: `${currCap.colorHex}10`,
                      borderColor: `${currCap.colorHex}40`,
                    }}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className="h-2 w-2 rounded-full shrink-0 animate-ping"
                        style={{ backgroundColor: currCap.colorHex }}
                      />
                      <div className="text-[11px] text-foreground leading-snug">
                        <strong style={{ color: currCap.colorHex }}>{currCap.title}:</strong>{" "}
                        <span className="text-muted-foreground">{currCap.liveDetail}</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setActiveCap(null)}
                      className="text-[10px] text-muted-foreground hover:text-foreground shrink-0 px-1.5 py-0.5 rounded border border-border/40 hover:bg-muted/50 transition-colors cursor-pointer"
                      title="Deselect"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <div className="mt-4 p-2.5 rounded-xl border border-dashed border-border/60 bg-muted/20 flex items-center justify-center gap-2 text-[11px] text-muted-foreground animate-fadeIn">
                    <Sparkles className="h-3.5 w-3.5 text-muted-foreground/70 animate-pulse" />
                    <span>Click any capability button or the AI Core to illuminate its neural pathway</span>
                  </div>
                )}

              </div>

              {/* Powered By Footer */}
              <div className="hidden lg:flex items-center justify-center lg:justify-start gap-2 mt-5 text-[11px] text-muted-foreground/60">
                <Zap className="h-3.5 w-3.5 text-amber-500" />
                <span>Powered by Google Cloud · Vertex AI · Gemini 2.5 Flash</span>
              </div>
            </div>

            {/* ── Right: Auth Form with Glowing Active Toggle ── */}
            <div className="w-full max-w-md auth-slideDown" style={{ animationDelay: "150ms" }}>
              <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 shadow-2xl">
                <div className="mb-6 text-center">
                  <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-foreground text-background font-bold text-lg shadow-md lg:hidden">
                    PM
                  </div>
                  <h2 className="text-lg font-bold tracking-tight text-foreground font-heading">
                    {authMode === "signin" ? "Welcome Back" : "Create Your Account"}
                  </h2>
                  <p className="text-xs text-muted-foreground mt-1">
                    {authMode === "signin" ? "Sign in to access your retail dashboard" : "Set up your account to get started"}
                  </p>
                </div>

                {/* ── GLOWING TOGGLE BUTTONS ── */}
                <div className="grid grid-cols-2 gap-1.5 rounded-xl bg-muted/80 p-1.5 mb-5 border border-border/40">
                  <button
                    type="button"
                    onClick={() => { setAuthMode("signin"); setErrorMsg(""); }}
                    className={`flex items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold transition-all duration-300 cursor-pointer ${
                      authMode === "signin"
                        ? "bg-card text-foreground tab-glow-active"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <LogIn className={`h-3.5 w-3.5 transition-all duration-300 ${authMode === "signin" ? "text-foreground drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]" : ""}`} />
                    Sign In
                  </button>
                  <button
                    type="button"
                    onClick={() => { setAuthMode("signup"); setErrorMsg(""); }}
                    className={`flex items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold transition-all duration-300 cursor-pointer ${
                      authMode === "signup"
                        ? "bg-card text-foreground tab-glow-active"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <UserPlus className={`h-3.5 w-3.5 transition-all duration-300 ${authMode === "signup" ? "text-foreground drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]" : ""}`} />
                    Sign Up
                  </button>
                </div>

                {/* Status Alerts */}
                {errorMsg && (
                  <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" /><span>{errorMsg}</span>
                  </div>
                )}
                {successMsg && phase === "auth" && (
                  <div className="mb-4 flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="h-4 w-4 shrink-0" /><span>{successMsg}</span>
                  </div>
                )}

                {/* ── Sign In Form ── */}
                {authMode === "signin" && (
                  <form onSubmit={handleSignIn} className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-foreground mb-1.5">Email Address</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="name@company.com"
                          className="pl-9 text-xs"
                          required
                          autoFocus
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-medium text-foreground">Password</label>
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
                    <Button type="submit" disabled={submitting} className="w-full text-xs font-semibold h-10 gap-2 mt-2">
                      {submitting ? <span>Signing in...</span> : <><LogIn className="h-4 w-4" /> Sign In</>}
                    </Button>
                  </form>
                )}

                {/* ── Sign Up Form ── */}
                {authMode === "signup" && (
                  <form onSubmit={handleSignUp} className="space-y-3.5">
                    <div>
                      <label className="block text-xs font-medium text-foreground mb-1">Full Name</label>
                      <div className="relative">
                        <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          type="text"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          placeholder="Your full name"
                          className="pl-9 text-xs"
                          required
                          autoFocus
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-foreground mb-1">Email Address</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="you@company.com"
                          className="pl-9 text-xs"
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-foreground mb-1">Phone <span className="text-muted-foreground font-normal">(Optional)</span></label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          type="tel"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="+1 (555) 000-0000"
                          className="pl-9 text-xs"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-foreground mb-1">Password</label>
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
                      <span>Store configuration and branches can be added inside your <strong>Profile</strong> screen after signing in.</span>
                    </div>
                    <Button type="submit" disabled={submitting} className="w-full text-xs font-semibold h-10 gap-2 mt-1">
                      {submitting ? <span>Creating Account...</span> : <><UserPlus className="h-4 w-4" /> Create Account</>}
                    </Button>
                  </form>
                )}
              </div>

              {/* Mobile Powered by Badge */}
              <div className="lg:hidden flex items-center justify-center gap-2 mt-5 text-[11px] text-muted-foreground/60">
                <Zap className="h-3 w-3 text-amber-500" />
                <span>Powered by Google Cloud · Vertex AI · Gemini 2.5 Flash</span>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* ▶  SUCCESS — Animated Welcome Transition                       */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        {phase === "success" && (
          <div className="flex flex-col items-center gap-5 text-center">
            <div className="relative">
              <div className="success-ring h-20 w-20 rounded-full border-2 border-emerald-400/40 flex items-center justify-center">
                <div className="success-icon h-16 w-16 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle2 className="h-9 w-9 text-emerald-400" />
                </div>
              </div>
            </div>
            <div>
              <h2 className="success-text text-2xl sm:text-3xl font-bold text-foreground font-heading">
                {successMsg || "Welcome!"}
              </h2>
              <p className="success-sub text-sm text-muted-foreground mt-2">
                Setting up your dashboard...
              </p>
            </div>
            <div className="success-sub w-48 h-1 bg-muted rounded-full overflow-hidden mt-2">
              <div className="progress-bar h-full bg-emerald-400 rounded-full" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
