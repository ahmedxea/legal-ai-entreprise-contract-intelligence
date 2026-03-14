"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState, useRef } from "react"
import { FileText, ArrowRight, Shield, Search, GitBranch, Zap, CheckCircle } from "lucide-react"
import { useAuth } from "@/lib/auth-context"

/* ─── tiny hook: element visible? ─── */
function useInView(threshold = 0.15) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true) }, { threshold })
    obs.observe(el)
    return () => obs.disconnect()
  }, [threshold])
  return { ref, visible }
}

function FadeIn({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const { ref, visible } = useInView()
  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(32px)",
        transition: `opacity 0.7s ease ${delay}ms, transform 0.7s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  )
}

export default function LandingPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()
  const [scrolled, setScrolled] = useState(false)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const heroRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.push("/home")
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 10)
    window.addEventListener("scroll", fn)
    return () => window.removeEventListener("scroll", fn)
  }, [])

  // Parallax glow follows cursor in hero
  useEffect(() => {
    const fn = (e: MouseEvent) => {
      const el = heroRef.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      if (e.clientY > rect.bottom) return
      setMousePos({ x: e.clientX, y: e.clientY })
    }
    window.addEventListener("mousemove", fn)
    return () => window.removeEventListener("mousemove", fn)
  }, [])

  return (
    <div className="min-h-screen bg-white overflow-x-hidden" style={{ fontFamily: "'Georgia', 'Times New Roman', serif" }}>

      {/* ── Navbar ── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 transition-all duration-500"
        style={{
          background: scrolled
            ? "rgba(255,255,255,0.7)"
            : "rgba(255,255,255,0.0)",
          backdropFilter: scrolled ? "blur(24px) saturate(180%)" : "blur(0px)",
          WebkitBackdropFilter: scrolled ? "blur(24px) saturate(180%)" : "blur(0px)",
          borderBottom: scrolled ? "1px solid rgba(0,122,255,0.15)" : "none",
          boxShadow: scrolled ? "0 4px 32px rgba(0,122,255,0.08)" : "none",
        }}
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{
                background: "linear-gradient(135deg, #007AFF, #00C6FF)",
                boxShadow: "0 4px 16px rgba(0,122,255,0.4)",
              }}
            >
              <FileText className="w-4 h-4 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight" style={{ fontFamily: "system-ui, sans-serif", color: scrolled ? "#0A1628" : "white" }}>Lexra</span>
          </div>

          <div />

          <div className="flex items-center gap-2" style={{ fontFamily: "system-ui, sans-serif" }}>
            <button
              onClick={() => router.push("/login")}
              className="text-sm font-medium px-4 py-2 rounded-lg transition-all duration-200"
              style={{ color: scrolled ? "#4B5563" : "rgba(255,255,255,0.7)" }}
            >
              Login
            </button>
            <button
              onClick={() => router.push("/login")}
              className="text-sm font-semibold px-5 py-2.5 rounded-xl transition-all duration-200 hover:scale-105"
              style={{
                background: scrolled ? "linear-gradient(135deg, #007AFF, #00C6FF)" : "rgba(255,255,255,0.15)",
                backdropFilter: scrolled ? "none" : "blur(12px)",
                border: scrolled ? "none" : "1px solid rgba(255,255,255,0.3)",
                color: "white",
                boxShadow: scrolled ? "0 4px 16px rgba(0,122,255,0.35)" : "0 4px 16px rgba(0,0,0,0.2)",
              }}
            >
              Request Demo
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section ref={heroRef} className="relative min-h-screen flex flex-col justify-end pb-28 pt-32 overflow-hidden" style={{ background: "#020B1B" }}>

        {/* Animated grid */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: "linear-gradient(rgba(0,122,255,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(0,122,255,0.07) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
            animation: "gridMove 20s linear infinite",
          }}
        />

        {/* Mouse-tracking glow */}
        <div
          className="absolute pointer-events-none"
          style={{
            width: 700,
            height: 700,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(0,122,255,0.18) 0%, transparent 65%)",
            left: mousePos.x - 350,
            top: mousePos.y - 350,
            transition: "left 0.4s ease, top 0.4s ease",
          }}
        />

        {/* Static ambient orbs */}
        <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(0,198,255,0.12) 0%, transparent 70%)", filter: "blur(40px)", animation: "float1 8s ease-in-out infinite" }} />
        <div className="absolute bottom-1/3 left-1/4 w-80 h-80 rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, rgba(0,122,255,0.1) 0%, transparent 70%)", filter: "blur(40px)", animation: "float2 10s ease-in-out infinite" }} />

        {/* Announcement pill */}
        <div className="absolute top-24 left-6 lg:left-10" style={{ animation: "fadeInDown 0.8s ease 0.2s both" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            background: "rgba(0,122,255,0.12)",
            border: "1px solid rgba(0,198,255,0.25)",
            backdropFilter: "blur(12px)",
            borderRadius: 999,
            padding: "6px 16px",
          }}>
            <span className="w-2 h-2 rounded-full bg-[#00C6FF] animate-pulse" />
            <span className="text-xs text-white/70 font-medium" style={{ fontFamily: "system-ui, sans-serif" }}>
              Powered by Phi-3 Mini — runs on your infrastructure
            </span>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 lg:px-10 relative z-10">
          <div style={{ animation: "fadeInUp 0.9s ease 0.1s both" }}>
            <h1 className="text-5xl sm:text-6xl lg:text-8xl font-bold text-white leading-[1.03] mb-8 max-w-5xl">
              Contract Intelligence<br />
              <span style={{ WebkitTextStroke: "1.5px rgba(0,198,255,0.6)", color: "transparent" }}>
                for the Enterprise
              </span>
            </h1>
          </div>
          <div style={{ animation: "fadeInUp 0.9s ease 0.25s both" }}>
            <p className="text-lg text-white/55 max-w-xl mb-10 leading-relaxed" style={{ fontFamily: "system-ui, sans-serif" }}>
              Extract insights, detect risks, and identify missing clauses from your contracts in minutes — securely, on your own infrastructure.
            </p>
          </div>
          <div className="flex flex-wrap gap-4" style={{ animation: "fadeInUp 0.9s ease 0.4s both", fontFamily: "system-ui, sans-serif" }}>
            <button
              onClick={() => router.push("/login")}
              className="text-sm font-semibold px-7 py-3.5 rounded-xl transition-all duration-200 hover:scale-105 hover:shadow-2xl"
              style={{ background: "white", color: "#0A1628", boxShadow: "0 4px 24px rgba(255,255,255,0.15)" }}
            >
              Request Demo
            </button>
            <button
              onClick={() => router.push("/login")}
              className="flex items-center gap-2 text-sm font-semibold px-7 py-3.5 rounded-xl transition-all duration-200 hover:scale-105"
              style={{
                background: "rgba(255,255,255,0.07)",
                border: "1px solid rgba(255,255,255,0.18)",
                backdropFilter: "blur(12px)",
                color: "white",
              }}
            >
              Sign in <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none" style={{ background: "linear-gradient(to bottom, transparent, #020B1B)" }} />
      </section>

      {/* ── Feature row 1 ── */}
      <section className="py-28 px-6 lg:px-10 bg-white">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
          <FadeIn delay={0}>
            <div className="inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full" style={{ background: "rgba(0,122,255,0.07)", border: "1px solid rgba(0,122,255,0.15)", fontFamily: "system-ui, sans-serif" }}>
              <div className="w-5 h-5 rounded-md flex items-center justify-center" style={{ background: "linear-gradient(135deg,#007AFF,#00C6FF)" }}>
                <Search className="w-3 h-3 text-white" />
              </div>
              <span className="text-xs font-semibold text-[#007AFF]">Lexra Assistant</span>
            </div>
            <h2 className="text-4xl lg:text-5xl font-bold text-[#0A1628] leading-tight mb-6">
              One AI agent for contract review, intelligence, and research
            </h2>
            <div className="space-y-1 mt-8" style={{ fontFamily: "system-ui, sans-serif" }}>
              {[
                { icon: FileText, title: "Extract & analyze contracts", body: "Automatically extract parties, dates, obligations, and financial terms from any PDF, DOCX, or scanned document." },
                { icon: Search, title: "Get answers to complex questions", body: "Ask questions across your contracts to surface risk, uncover insights, and understand clause patterns." },
                { icon: Shield, title: "Detect risks with confidence", body: "60+ rule-based checks across liability, confidentiality, IP, payment, and data protection clauses." },
              ].map(({ icon: Icon, title, body }, i) => (
                <div key={title} className="flex items-start gap-4 py-4 border-b border-gray-100 last:border-0 group cursor-default transition-all duration-200 rounded-xl px-3 hover:bg-blue-50/40">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 transition-all duration-200 group-hover:scale-110" style={{ background: "linear-gradient(135deg,#007AFF,#00C6FF)", boxShadow: "0 4px 12px rgba(0,122,255,0.25)" }}>
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-[#0A1628] mb-1">{title}</p>
                    <p className="text-sm text-[#6B7280] leading-relaxed">{body}</p>
                  </div>
                </div>
              ))}
            </div>
          </FadeIn>

          {/* Glassy mockup */}
          <FadeIn delay={150}>
            <div className="relative">
              {/* Glass card */}
              <div
                className="rounded-2xl overflow-hidden"
                style={{
                  background: "rgba(255,255,255,0.6)",
                  backdropFilter: "blur(20px)",
                  border: "1px solid rgba(0,122,255,0.12)",
                  boxShadow: "0 32px 64px rgba(0,122,255,0.12), 0 0 0 1px rgba(255,255,255,0.8) inset",
                }}
              >
                <div className="flex items-center gap-2 px-4 py-3 border-b" style={{ borderColor: "rgba(0,122,255,0.08)", background: "rgba(255,255,255,0.8)" }}>
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-400" />
                    <div className="w-3 h-3 rounded-full bg-yellow-400" />
                    <div className="w-3 h-3 rounded-full bg-green-400" />
                  </div>
                  <span className="text-xs text-gray-400 ml-2" style={{ fontFamily: "system-ui, sans-serif" }}>Service Agreement — Analysis</span>
                </div>
                <div className="grid grid-cols-2 divide-x" style={{ divideColor: "rgba(0,122,255,0.08)" }}>
                  <div className="p-5 text-xs leading-relaxed space-y-3 font-mono" style={{ borderRight: "1px solid rgba(0,122,255,0.08)" }}>
                    <p className="text-gray-400">4.2 Liability Cap.</p>
                    <p className="text-gray-600">Each party's total liability under this Agreement shall not exceed amounts paid in the twelve (12) months preceding the claim.</p>
                    <p className="text-[#0A1628] px-1.5 py-0.5 rounded" style={{ background: "rgba(251,191,36,0.2)" }}>4.3 Indemnification. Supplier shall indemnify and hold harmless Customer from any third-party claims...</p>
                    <p className="text-gray-400">5. TERM AND TERMINATION</p>
                    <p className="text-gray-600">5.1 This Agreement shall remain in effect for one (1) year...</p>
                  </div>
                  <div className="p-5 space-y-3" style={{ fontFamily: "system-ui, sans-serif", background: "rgba(248,250,255,0.8)" }}>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-6 h-6 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg,#007AFF,#00C6FF)" }}>
                        <FileText className="w-3 h-3 text-white" />
                      </div>
                      <span className="text-xs font-semibold text-[#007AFF]">Lexra Assistant</span>
                    </div>
                    {[
                      { bg: "rgba(239,68,68,0.06)", border: "rgba(239,68,68,0.15)", label: "⚠ High Risk", labelColor: "#DC2626", text: "Liability cap insufficient for enterprise scope.", textColor: "#EF4444" },
                      { bg: "rgba(245,158,11,0.06)", border: "rgba(245,158,11,0.15)", label: "Missing Clause", labelColor: "#D97706", text: "Force Majeure not detected.", textColor: "#F59E0B" },
                      { bg: "rgba(0,122,255,0.06)", border: "rgba(0,122,255,0.15)", label: "Generate Clause →", labelColor: "#007AFF", text: "AI can draft a jurisdiction-aware clause instantly.", textColor: "#3B82F6" },
                    ].map(({ bg, border, label, labelColor, text, textColor }) => (
                      <div key={label} className="rounded-xl p-3 transition-all duration-200 hover:scale-[1.02]" style={{ background: bg, border: `1px solid ${border}` }}>
                        <p className="text-xs font-semibold mb-1" style={{ color: labelColor }}>{label}</p>
                        <p className="text-xs" style={{ color: textColor }}>{text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Floating badge */}
              <div
                className="absolute -bottom-5 -right-5 flex items-center gap-3 px-4 py-3 rounded-2xl"
                style={{
                  background: "rgba(255,255,255,0.85)",
                  backdropFilter: "blur(16px)",
                  border: "1px solid rgba(0,122,255,0.12)",
                  boxShadow: "0 8px 32px rgba(0,122,255,0.15)",
                  fontFamily: "system-ui, sans-serif",
                  animation: "floatBadge 4s ease-in-out infinite",
                }}
              >
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#0A1628]">Analysis complete</p>
                  <p className="text-xs text-gray-400">3 risks · 2 gaps found</p>
                </div>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Gap analysis — dark liquid glass ── */}
      <section className="py-28 px-6 lg:px-10 overflow-hidden" style={{ background: "#020B1B" }}>
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
          {/* Glassy dark panel */}
          <FadeIn delay={0}>
            <div
              className="rounded-2xl overflow-hidden"
              style={{
                background: "rgba(10,31,68,0.5)",
                backdropFilter: "blur(32px)",
                border: "1px solid rgba(0,198,255,0.15)",
                boxShadow: "0 32px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
              }}
            >
              <div className="px-5 py-4 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                <span className="text-xs font-semibold text-white/30 uppercase tracking-widest" style={{ fontFamily: "system-ui, sans-serif" }}>Gap Analysis Report</span>
              </div>
              <div className="p-5 space-y-1" style={{ fontFamily: "system-ui, sans-serif" }}>
                {[
                  { label: "Governing Law", status: "present" },
                  { label: "Liability Cap", status: "present" },
                  { label: "Force Majeure", status: "missing" },
                  { label: "Data Protection", status: "missing" },
                  { label: "Indemnification", status: "present" },
                  { label: "Non-Compete", status: "review" },
                  { label: "IP Ownership", status: "present" },
                  { label: "Post-Termination", status: "review" },
                ].map(({ label, status }, i) => {
                  const cfg = status === "present"
                    ? { bg: "rgba(52,211,153,0.08)", border: "rgba(52,211,153,0.2)", color: "#34D399", text: "✓ Present" }
                    : status === "missing"
                    ? { bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.2)", color: "#F87171", text: "✗ Missing" }
                    : { bg: "rgba(251,191,36,0.08)", border: "rgba(251,191,36,0.2)", color: "#FBBf24", text: "⚠ Review" }
                  return (
                    <div
                      key={label}
                      className="flex items-center justify-between py-2.5 px-3 rounded-xl transition-all duration-200 hover:bg-white/5"
                      style={{ animationDelay: `${i * 80}ms`, animation: "fadeInLeft 0.5s ease both" }}
                    >
                      <span className="text-sm text-white/75">{label}</span>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full" style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, color: cfg.color }}>
                        {cfg.text}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={150}>
            <div className="inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full" style={{ background: "rgba(0,198,255,0.1)", border: "1px solid rgba(0,198,255,0.2)", fontFamily: "system-ui, sans-serif" }}>
              <GitBranch className="w-3.5 h-3.5 text-[#00C6FF]" />
              <span className="text-xs font-semibold text-[#00C6FF]">Gap Detection</span>
            </div>
            <h2 className="text-4xl lg:text-5xl font-bold text-white leading-tight mb-6">
              Know what's missing before you sign
            </h2>
            <p className="text-white/55 text-lg leading-relaxed mb-8" style={{ fontFamily: "system-ui, sans-serif" }}>
              Lexra automatically detects missing critical and recommended clauses across every contract — from Force Majeure to Data Protection.
            </p>
            <div className="space-y-3" style={{ fontFamily: "system-ui, sans-serif" }}>
              {["15 critical clause types checked automatically", "Jurisdiction-aware recommendations", "Generate missing clauses with one click"].map((point) => (
                <div key={point} className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "rgba(0,122,255,0.15)", border: "1px solid rgba(0,198,255,0.3)" }}>
                    <CheckCircle className="w-3 h-3 text-[#00C6FF]" />
                  </div>
                  <span className="text-sm text-white/65">{point}</span>
                </div>
              ))}
            </div>
            <button
              onClick={() => router.push("/login")}
              className="mt-10 flex items-center gap-2 text-sm font-semibold px-6 py-3 rounded-xl transition-all duration-200 hover:scale-105"
              style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.15)", backdropFilter: "blur(12px)", color: "white", fontFamily: "system-ui, sans-serif" }}
            >
              See it in action <ArrowRight className="w-4 h-4" />
            </button>
          </FadeIn>
        </div>
      </section>

      {/* ── Feature grid ── */}
      <section className="py-28 px-6 lg:px-10 bg-white">
        <div className="max-w-7xl mx-auto">
          <FadeIn>
            <div className="max-w-2xl mb-16">
              <h2 className="text-4xl lg:text-5xl font-bold text-[#0A1628] leading-tight mb-4">
                Everything your legal team needs
              </h2>
              <p className="text-[#6B7280] text-lg leading-relaxed" style={{ fontFamily: "system-ui, sans-serif" }}>
                One platform to upload, analyze, and act on every contract in your portfolio.
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-4">
            {[
              { icon: Search, title: "Intelligent extraction", body: "Parties, dates, financial terms, obligations, and governing law — extracted automatically from PDF, DOCX, or scanned images." },
              { icon: Shield, title: "Risk detection", body: "60+ deterministic rules across liability, confidentiality, payment, IP, and data protection. Every risk severity-scored." },
              { icon: GitBranch, title: "Gap analysis", body: "15 clause types checked. Know exactly what's absent from every agreement before it becomes a liability." },
              { icon: Zap, title: "AI clause generation", body: "Jurisdiction-aware, CUAD-aligned clauses generated on demand. Remediate gaps with AI-drafted language instantly." },
              { icon: FileText, title: "Multi-format support", body: "PDF, DOCX, TXT, or scanned documents. OCR handles image-based contracts with no manual pre-processing." },
              { icon: CheckCircle, title: "Secure by design", body: "Your contracts never leave your infrastructure. Runs on local Ollama — no data sent to third-party AI APIs." },
            ].map(({ icon: Icon, title, body }, i) => (
              <FadeIn key={title} delay={i * 60}>
                <div
                  className="group p-7 rounded-2xl h-full transition-all duration-300 cursor-default hover:-translate-y-1"
                  style={{
                    background: "rgba(255,255,255,0.7)",
                    border: "1px solid rgba(0,122,255,0.1)",
                    backdropFilter: "blur(12px)",
                    boxShadow: "0 4px 24px rgba(0,122,255,0.05)",
                  }}
                  onMouseEnter={e => (e.currentTarget.style.boxShadow = "0 16px 48px rgba(0,122,255,0.15), 0 0 0 1px rgba(0,122,255,0.15)")}
                  onMouseLeave={e => (e.currentTarget.style.boxShadow = "0 4px 24px rgba(0,122,255,0.05)")}
                >
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center mb-5 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3"
                    style={{ background: "linear-gradient(135deg,#007AFF,#00C6FF)", boxShadow: "0 6px 16px rgba(0,122,255,0.3)" }}
                  >
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-base font-bold text-[#0A1628] mb-2">{title}</h3>
                  <p className="text-sm text-[#6B7280] leading-relaxed" style={{ fontFamily: "system-ui, sans-serif" }}>{body}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-28 px-6 lg:px-10 text-center overflow-hidden relative" style={{ background: "#0A1F44" }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(0,198,255,0.15) 0%, transparent 60%)" }} />
        <FadeIn>
          <div className="max-w-3xl mx-auto relative z-10">
            <h2 className="text-4xl lg:text-5xl font-bold text-white leading-tight mb-6">
              Ready to transform your contract workflow?
            </h2>
            <p className="text-white/55 text-lg mb-10" style={{ fontFamily: "system-ui, sans-serif" }}>
              Upload your first contract and get a full AI analysis in minutes.
            </p>
            <div className="flex flex-wrap justify-center gap-4" style={{ fontFamily: "system-ui, sans-serif" }}>
              <button
                onClick={() => router.push("/login")}
                className="flex items-center gap-2 text-sm font-semibold px-8 py-4 rounded-xl transition-all duration-200 hover:scale-105"
                style={{ background: "linear-gradient(135deg,#007AFF,#00C6FF)", color: "white", boxShadow: "0 8px 32px rgba(0,122,255,0.4)" }}
              >
                Get started for free <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => router.push("/login")}
                className="text-sm font-semibold px-8 py-4 rounded-xl transition-all duration-200 hover:scale-105"
                style={{ background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.15)", backdropFilter: "blur(12px)", color: "white" }}
              >
                Sign in
              </button>
            </div>
          </div>
        </FadeIn>
      </section>

      {/* ── Footer ── */}
      <footer className="py-10 px-6 lg:px-10 border-t" style={{ background: "#020B1B", borderColor: "rgba(255,255,255,0.05)" }}>
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4" style={{ fontFamily: "system-ui, sans-serif" }}>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg,#007AFF,#00C6FF)" }}>
              <FileText className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-bold text-white">Lexra</span>
          </div>
          <p className="text-xs text-gray-600">© 2026 Lexra. Enterprise AI Contract Intelligence.</p>
          <div className="flex items-center gap-6">
            {["Privacy", "Terms", "Security"].map((item) => (
              <button key={item} className="text-xs text-gray-600 hover:text-gray-400 transition-colors">{item}</button>
            ))}
          </div>
        </div>
      </footer>

      {/* ── Global keyframes ── */}
      <style jsx global>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(40px); }
          to   { opacity: 1; transform: translateY(0);    }
        }
        @keyframes fadeInDown {
          from { opacity: 0; transform: translateY(-20px); }
          to   { opacity: 1; transform: translateY(0);     }
        }
        @keyframes fadeInLeft {
          from { opacity: 0; transform: translateX(-16px); }
          to   { opacity: 1; transform: translateX(0);     }
        }
        @keyframes float1 {
          0%, 100% { transform: translateY(0px) scale(1);    }
          50%       { transform: translateY(-30px) scale(1.05); }
        }
        @keyframes float2 {
          0%, 100% { transform: translateY(0px) scale(1);    }
          50%       { transform: translateY(20px) scale(0.97); }
        }
        @keyframes floatBadge {
          0%, 100% { transform: translateY(0px);  }
          50%       { transform: translateY(-6px); }
        }
        @keyframes gridMove {
          from { background-position: 0 0;    }
          to   { background-position: 64px 64px; }
        }
      `}</style>
    </div>
  )
}
