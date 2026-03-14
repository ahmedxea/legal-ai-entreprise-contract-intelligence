"use client"

import type React from "react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { config } from "@/lib/config"
import { apiClient, Contract, DashboardStats } from "@/lib/api-client"
import { 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  BarChart3, 
  Scale, 
  ShieldCheck, 
  Sparkles,
  Upload,
  X,
  Loader2,
  ScanSearch,
  Eye,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { GlowCard } from "@/components/ui/glow-card"
import { StatCard } from "@/components/stat-card"

const MAX_FILE_SIZE_MB = 50
const ALLOWED_EXTENSIONS = [".pdf", ".docx"]

type FileStatus = "pending" | "uploading" | "success" | "extracting" | "analyzing" | "analyzed" | "error"

interface UploadedFile {
  id: string
  file: File
  name: string
  size: string
  status: FileStatus
  contractId?: string
  errorMessage?: string
}

function getUploadDate(contract: Contract) {
  return contract.uploaded_at ?? contract.upload_date ?? new Date().toISOString()
}

function getExtractedData(contract: Contract) {
  return contract.extracted_data ?? contract.analysis?.entities ?? contract.analysis?.extracted_data ?? {}
}

function getGoverningLaw(contract: Contract) {
  return getExtractedData(contract).governing_law || "Unclassified"
}

export default function DashboardPage() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [backendStatus, setBackendStatus] = useState<"online" | "offline">("offline")

  // Upload state
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  /* ── Upload Helpers ── */

  const humanSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const validateFile = (file: File): string | null => {
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type "${ext}". Only PDF and DOCX files are accepted.`
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return `File is too large (${humanSize(file.size)}). Maximum size is ${MAX_FILE_SIZE_MB} MB.`
    }
    if (file.size === 0) {
      return "File is empty."
    }
    return null
  }

  /* ── Upload a single file ── */

  const uploadFile = useCallback(
    async (entry: UploadedFile) => {
      setFiles((prev) =>
        prev.map((f) => (f.id === entry.id ? { ...f, status: "uploading" as FileStatus } : f))
      )

      try {
        const formData = new FormData()
        formData.append("file", entry.file)

        const params = new URLSearchParams({ language: "en" })

        const res = await fetch(`${config.apiUrl}/api/contracts/upload?${params}`, {
          method: "POST",
          credentials: "include",
          body: formData,
        })

        if (!res.ok) {
          const body = await res.json().catch(() => ({ detail: "Upload failed" }))
          const detail = body.detail
          const message =
            typeof detail === "string"
              ? detail
              : Array.isArray(detail)
              ? detail.map((d: any) => d.msg ?? JSON.stringify(d)).join("; ")
              : `Upload failed (${res.status})`
          throw new Error(message)
        }

        const data = await res.json()
        const contractId: string = data.contract_id

        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id
              ? { ...f, status: "extracting" as FileStatus, contractId }
              : f
          )
        )

        // Phase 1 → wait for text extraction to complete
        await apiClient.pollContractStatus(contractId, ["extracted", "analyzed"], 3000, 200)

        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id ? { ...f, status: "analyzing" as FileStatus } : f
          )
        )

        // Phase 2 → trigger AI analysis
        await apiClient.analyzeContract(contractId)

        // Poll until analysis is done
        await apiClient.pollContractStatus(contractId, ["analyzed"], 3000, 200)

        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id ? { ...f, status: "analyzed" as FileStatus } : f
          )
        )

        // Refresh dashboard data
        loadDashboardData()
      } catch (err: any) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id
              ? { ...f, status: "error" as FileStatus, errorMessage: err.message }
              : f
          )
        )
      }
    },
    []
  )

  /* ── Add files (from input or drag) ── */

  const addFiles = useCallback(
    (incoming: File[]) => {
      const newEntries: UploadedFile[] = incoming.map((file) => {
        const validationError = validateFile(file)
        return {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          file,
          name: file.name,
          size: humanSize(file.size),
          status: validationError ? ("error" as FileStatus) : ("pending" as FileStatus),
          errorMessage: validationError ?? undefined,
        }
      })

      setFiles((prev) => [...prev, ...newEntries])

      // Auto-upload valid files
      newEntries
        .filter((e) => e.status === "pending")
        .forEach((e) => uploadFile(e))
    },
    [uploadFile]
  )

  /* ── Drag & drop handlers ── */

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }
  const onDragLeave = () => setIsDragging(false)
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    addFiles(Array.from(e.dataTransfer.files))
  }

  /* ── File input handler ── */

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files))
      e.target.value = "" // allow re-selecting same file
    }
  }

  /* ── Remove file from list ── */

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  /* ── Status badge renderer ── */

  const StatusBadge = ({ file }: { file: UploadedFile }) => {
    switch (file.status) {
      case "pending":
        return (
          <span className="text-xs text-muted-foreground font-medium">Queued</span>
        )
      case "uploading":
        return (
          <span className="flex items-center gap-1.5 text-primary text-xs font-medium">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Uploading…
          </span>
        )
      case "success":
      case "extracting":
        return (
          <span className="flex items-center gap-1.5 text-blue-500 text-xs font-medium">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Extracting…
          </span>
        )
      case "analyzing":
        return (
          <span className="flex items-center gap-1.5 text-violet-500 text-xs font-medium">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Analysing…
          </span>
        )
      case "analyzed":
        return (
          <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
            <Sparkles className="h-3.5 w-3.5" />
            Analysed
          </span>
        )
      case "error":
        return (
          <span className="flex items-center gap-1.5 text-destructive text-xs font-medium">
            <AlertTriangle className="h-3.5 w-3.5" />
            Failed
          </span>
        )
    }
  }

  useEffect(() => {
    loadDashboardData()
    checkBackendHealth()
  }, [])

  async function checkBackendHealth() {
    try {
      await apiClient.healthCheck()
      setBackendStatus("online")
    } catch {
      setBackendStatus("offline")
    }
  }

  async function loadDashboardData() {
    try {
      setLoading(true)
      const [contractsData, statsData] = await Promise.all([
        apiClient.getContracts(),
        apiClient.getDashboardStats().catch(() => null),
      ])
      setContracts(contractsData)
      setStats(statsData)
    } catch (error) {
      console.error("Failed to load dashboard data:", error)
    } finally {
      setLoading(false)
    }
  }

  const analyzedContracts = useMemo(
    () => contracts.filter((contract) => contract.status === "analyzed" || contract.status === "completed"),
    [contracts],
  )

  const priorityContracts = useMemo(
    () =>
      [...analyzedContracts]
        .sort((a, b) => (b.analysis?.overall_risk_score ?? 0) - (a.analysis?.overall_risk_score ?? 0))
        .slice(0, 3),
    [analyzedContracts],
  )

  const jurisdictionBreakdown = useMemo(() => {
    const counts = analyzedContracts.reduce<Record<string, number>>((acc, contract) => {
      const law = getGoverningLaw(contract)
      acc[law] = (acc[law] ?? 0) + 1
      return acc
    }, {})

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
  }, [analyzedContracts])

  const clauseWatchlist = useMemo(() => {
    const counts = analyzedContracts.reduce<Record<string, number>>((acc, contract) => {
      for (const clause of contract.analysis?.missing_clauses ?? []) {
        acc[clause] = (acc[clause] ?? 0) + 1
      }
      return acc
    }, {})

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
  }, [analyzedContracts])

  // Calculate stats if not available from backend
  const displayStats = stats || {
    total_contracts: contracts.length,
    analyzed_contracts: contracts.filter(c => c.status === "analyzed" || c.status === "completed").length,
    pending_contracts: contracts.filter(c => c.status === "uploaded" || c.status === "processing" || c.status === "extracting").length,
    high_risks: contracts.reduce((acc, c) => {
      const risks = c.analysis?.risks?.filter(r => r.severity === "high" || r.severity === "critical").length || 0
      return acc + risks
    }, 0),
    average_risk_score: 0,
    compliance_score: 0,
  }

  const statCards = [
    {
      title: "Total Contracts",
      value: displayStats.total_contracts,
      icon: FileText,
      color: "primary",
      note: "documents tracked",
    },
    {
      title: "Analyzed",
      value: displayStats.analyzed_contracts,
      icon: CheckCircle,
      color: "success",
      note: "intelligence runs complete",
    },
    {
      title: "Pending",
      value: displayStats.pending_contracts,
      icon: Clock,
      color: "warning",
      note: "still in the pipeline",
    },
    {
      title: "High-Risk Findings",
      value: displayStats.high_risks,
      icon: AlertTriangle,
      color: "danger",
      note: "need legal review",
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-10rem)]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Contract Intelligence Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Upload contracts for AI-powered analysis, or review your existing portfolio below.
          </p>
        </div>

        {/* Drop zone */}
        <GlowCard
          glowColor={isDragging ? "primary" : undefined}
          className={`relative cursor-pointer transition-all duration-300 ${
            isDragging ? "scale-[1.02]" : ""
          }`}
        >
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className={`rounded-xl border-2 border-dashed p-10 text-center transition-all duration-300 ${
              isDragging
                ? "border-primary bg-primary/10"
                : "border-border/50 hover:border-primary/40"
            }`}
          >
            <div className="flex flex-col items-center gap-4">
              <div className={`flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 transition-transform duration-300 ${isDragging ? "scale-110 rotate-6" : ""}`}>
                <Upload className={`h-7 w-7 text-primary transition-transform duration-300 ${isDragging ? "scale-125" : ""}`} />
              </div>

              <div>
                <p className="text-base font-semibold mb-1">
                  {isDragging ? "Drop your files here" : "Drag & drop files here"}
                </p>
                <p className="text-sm text-muted-foreground">
                  or{" "}
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="text-primary font-medium underline underline-offset-2 hover:text-primary/80 transition-colors"
                  >
                    browse from your device
                  </button>
                </p>
                <div className="flex items-center justify-center gap-4 mt-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <FileText className="h-3.5 w-3.5" />
                    PDF, DOCX
                  </span>
                  <span className="text-border">•</span>
                  <span>Max {MAX_FILE_SIZE_MB} MB</span>
                </div>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                multiple
                accept=".pdf,.docx"
                onChange={onFileInput}
              />
            </div>
          </div>
        </GlowCard>

        {/* File list */}
        {files.length > 0 && (
          <div className="rounded-xl border bg-card/50 backdrop-blur-sm overflow-hidden">
            <div className="flex items-center justify-between border-b bg-muted/30 px-6 py-3.5">
              <h2 className="text-sm font-semibold">
                Uploads <span className="text-muted-foreground">({files.filter((f) => f.status === "analyzed").length}/{files.length} completed)</span>
              </h2>
              {files.length > 0 && (
                <button
                  onClick={() => setFiles([])}
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors font-medium"
                >
                  Clear all
                </button>
              )}
            </div>

            <div className="divide-y">
              {files.map((file, idx) => (
                <div
                  key={file.id}
                  className="flex items-center gap-4 px-6 py-4 hover:bg-accent/20 transition-all duration-200 group"
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  {/* Icon */}
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-secondary/10 group-hover:scale-110 transition-transform duration-200">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>

                  {/* Name + size */}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {file.size}
                      {file.contractId && (
                        <span className="ml-2 inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          ID: {file.contractId.slice(0, 8)}…
                        </span>
                      )}
                      {file.errorMessage && (
                        <span className="ml-2 text-destructive">{file.errorMessage}</span>
                      )}
                    </p>
                  </div>

                  {/* Status */}
                  <StatusBadge file={file} />

                  {/* View Preview shortcut after analysis */}
                  {file.status === "analyzed" && file.contractId && (
                    <Link href={`/contracts/detail?id=${file.contractId}`}>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-xs gap-1.5 shrink-0 hover:scale-105 transition-transform"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        View
                      </Button>
                    </Link>
                  )}

                  {/* Remove */}
                  <button
                    onClick={() => removeFile(file.id)}
                    className="text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100"
                    title="Remove"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feature cards - Hidden for now */}
        {false && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                icon: ScanSearch,
                title: "Smart Extraction",
                desc: "Automatically extract key terms, dates, parties, and obligations from your contracts.",
              },
              {
                icon: ShieldCheck,
                title: "Risk Detection",
                desc: "Identify potential risks, unfavorable terms, and compliance issues in real-time.",
              },
              {
                icon: Scale,
                title: "Compliance Check",
                desc: "Ensure your contracts meet regulatory requirements and industry standards.",
              },
            ].map((card, idx) => (
              <GlowCard
                key={card.title}
                glowColor="primary"
                className="group"
              >
                <div className="p-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 mb-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
                    <card.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-sm font-semibold mb-2">{card.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{card.desc}</p>
                </div>
              </GlowCard>
            ))}
          </div>
        )}
      </div>

      {/* Backend Status Banner */}
      {backendStatus === "offline" && (
        <div className="enterprise-card p-4 border-l-4 border-destructive bg-destructive/5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Backend Offline</p>
              <p className="text-sm text-muted-foreground">
                The backend API is unreachable. Check your connection or server status.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, idx) => (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value.toString()}
            icon={stat.icon}
            note={stat.note}
            color={stat.color as "primary" | "success" | "warning" | "danger"}
            delay={idx * 100}
          />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 enterprise-card p-6 space-y-5">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" /> Portfolio Intelligence Brief
              </h2>
              <p className="text-sm text-muted-foreground mt-2 max-w-3xl leading-relaxed">
                Lexra has processed {displayStats.analyzed_contracts} of {displayStats.total_contracts} contracts.
                The portfolio is running at an average risk score of {displayStats.average_risk_score || 0}/10 with a
                compliance health of {displayStats.compliance_score || 0}%. {jurisdictionBreakdown.length > 0 ? ` Governing law has been detected across ${jurisdictionBreakdown.length} jurisdiction${jurisdictionBreakdown.length > 1 ? "s" : ""}.` : " Jurisdiction will appear here once analysis completes."}
              </p>
            </div>
            <div>
              <Link href="/risk" className="btn-enterprise-secondary text-sm inline-flex">
                Review Risks
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <GlowCard glowColor="primary" className="p-5 group">
              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2 font-semibold">Average Risk</p>
              <p className="text-3xl font-bold group-hover:text-primary transition-colors">{displayStats.average_risk_score || 0}<span className="text-xl text-muted-foreground">/10</span></p>
              <p className="text-xs text-muted-foreground mt-2">Portfolio-wide legal exposure signal</p>
            </GlowCard>
            <GlowCard glowColor="success" className="p-5 group">
              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2 font-semibold">Compliance Health</p>
              <p className="text-3xl font-bold group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">{displayStats.compliance_score || 0}<span className="text-xl text-muted-foreground">%</span></p>
              <p className="text-xs text-muted-foreground mt-2">Risk findings & missing clauses</p>
            </GlowCard>
            <GlowCard glowColor="primary" className="p-5 group">
              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2 font-semibold">Jurisdictions</p>
              <p className="text-3xl font-bold group-hover:text-primary transition-colors">{jurisdictionBreakdown.length}</p>
              <p className="text-xs text-muted-foreground mt-2">Auto-detected governing law</p>
            </GlowCard>
          </div>
        </div>

        <div className="enterprise-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Scale className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Jurisdiction Coverage</h3>
          </div>
          {jurisdictionBreakdown.length === 0 ? (
            <p className="text-sm text-muted-foreground">No governing law detected yet.</p>
          ) : (
            <div className="space-y-3">
              {jurisdictionBreakdown.map(([law, count], idx) => (
                <div 
                  key={law} 
                  className="flex items-center justify-between rounded-xl border border-border bg-background/50 px-4 py-3 hover:bg-accent/20 hover:border-primary/30 transition-all duration-200 group"
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  <div>
                    <p className="text-sm font-semibold group-hover:text-primary transition-colors">{law}</p>
                    <p className="text-xs text-muted-foreground">auto-detected from contracts</p>
                  </div>
                  <Badge variant="outline" className="font-semibold">{count}</Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Contracts & Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Contracts List */}
        <div className="lg:col-span-2 enterprise-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Recent Contracts</h2>
            <Link href="/contracts" className="text-sm text-primary hover:underline">
              View All
            </Link>
          </div>

          {contracts.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
              <p className="text-muted-foreground">No contracts yet</p>
              <button
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                className="btn-enterprise mt-4 inline-block"
              >
                Upload Your First Contract
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {contracts.slice(0, 5).map((contract, idx) => (
                <Link
                  key={contract.id}
                  href={`/contracts/detail?id=${contract.id}`}
                  className="group flex items-center justify-between p-4 rounded-xl border border-border hover:border-primary/40 hover:bg-accent/20 hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/10 to-secondary/10 group-hover:scale-110 transition-transform duration-200">
                      <FileText className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate group-hover:text-primary transition-colors">{contract.filename}</p>
                      <div className="flex items-center gap-2 flex-wrap mt-1.5">
                        <Badge variant="outline" className="text-[11px]">
                          <Scale className="w-3 h-3 mr-1" />
                          {getGoverningLaw(contract)}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(getUploadDate(contract)).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {typeof contract.analysis?.overall_risk_score === "number" && (
                      <div className="text-right">
                        <p className="text-sm font-semibold">{contract.analysis.overall_risk_score.toFixed(1)}/10</p>
                        <p className="text-[11px] text-muted-foreground">risk score</p>
                      </div>
                    )}
                    {contract.status === "analyzed" && (
                      <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20">Analyzed</Badge>
                    )}
                    {contract.status === "completed" && (
                      <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20">Analyzed</Badge>
                    )}
                    {contract.status === "processing" && (
                      <Badge className="bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20">Processing</Badge>
                    )}
                    {contract.status === "extracting" && (
                      <Badge className="bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20">Extracting</Badge>
                    )}
                    {contract.status === "uploaded" && (
                      <Badge variant="outline" className="text-xs">Pending</Badge>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Priority & Watchlist */}
        <div className="space-y-6">
          <div className="enterprise-card p-6">
            <h3 className="font-semibold mb-4">Priority Review Queue</h3>
            {priorityContracts.length === 0 ? (
              <p className="text-sm text-muted-foreground">No analyzed contracts yet.</p>
            ) : (
              <div className="space-y-3">
                {priorityContracts.map((contract) => (
                  <Link
                    key={contract.id}
                    href={`/contracts/detail?id=${contract.id}`}
                    className="block rounded-lg border border-border p-3 hover:border-accent transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{contract.filename}</p>
                        <p className="text-xs text-muted-foreground mt-1">{getGoverningLaw(contract)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-destructive">
                          {(contract.analysis?.overall_risk_score ?? 0).toFixed(1)}/10
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          {(contract.analysis?.missing_clauses ?? []).length} gaps
                        </p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="enterprise-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-primary" />
              <h3 className="font-semibold">Missing Clause Watchlist</h3>
            </div>
            {clauseWatchlist.length === 0 ? (
              <p className="text-sm text-muted-foreground">No clause gaps detected yet.</p>
            ) : (
              <div className="space-y-3">
                {clauseWatchlist.map(([clause, count]) => (
                  <div key={clause} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
                    <div>
                      <p className="text-sm font-medium capitalize">{clause.replace(/_/g, " ")}</p>
                      <p className="text-xs text-muted-foreground">missing across reviewed contracts</p>
                    </div>
                    <Badge variant="outline">{count}</Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
