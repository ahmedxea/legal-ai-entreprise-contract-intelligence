"use client"

import { Suspense } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  FileCode,
  Sparkles,
  Copy,
  RefreshCw,
  Lock,
  ClipboardList,
  Scale,
  Banknote,
  Lightbulb,
  Users,
  Shield,
  Globe,
  FileWarning,
  Gavel,
  Ban,
  Eye,
  Handshake,
  Clock,
  Loader2,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
} from "lucide-react"
import { type LucideIcon } from "lucide-react"
import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { apiClient, type GeneratedClause, type CuadTemplate } from "@/lib/api-client"

const CLAUSE_ICONS: Record<string, LucideIcon> = {
  governing_law: Globe,
  confidentiality: Lock,
  termination: ClipboardList,
  liability: Scale,
  indemnification: Shield,
  payment_terms: Banknote,
  intellectual_property: Lightbulb,
  data_protection: Eye,
  force_majeure: FileWarning,
  non_compete: Ban,
  exclusivity: Handshake,
  change_of_control: Users,
  anti_assignment: Gavel,
  audit_rights: FileCode,
  post_termination_services: Clock,
}

const JURISDICTION_OPTIONS = [
  { value: "", label: "General / Not specified" },
  { value: "qatar", label: "Qatar" },
  { value: "uae", label: "UAE" },
  { value: "uk", label: "United Kingdom" },
  { value: "usa", label: "United States" },
  { value: "eu", label: "European Union" },
]

function ClauseGeneratorContent() {
  const searchParams = useSearchParams()

  // Pre-fill from query params (coming from contract detail page)
  const prefillType = searchParams.get("type") ?? ""
  const prefillRisk = searchParams.get("risk") ?? ""
  const prefillJurisdiction = searchParams.get("jurisdiction") ?? ""
  const prefillContext = searchParams.get("context") ?? ""

  const [templates, setTemplates] = useState<CuadTemplate[]>([])
  const [selectedType, setSelectedType] = useState(prefillType || "confidentiality")
  const [riskDescription, setRiskDescription] = useState(prefillRisk)
  const [jurisdiction, setJurisdiction] = useState(prefillJurisdiction)
  const [contractContext, setContractContext] = useState(prefillContext)
  const [generatedClause, setGeneratedClause] = useState<GeneratedClause | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Auto-generate if pre-filled from contract detail
  const [autoGenTriggered, setAutoGenTriggered] = useState(false)

  useEffect(() => {
    loadTemplates()
  }, [])

  useEffect(() => {
    if (prefillType && prefillRisk && !autoGenTriggered) {
      setAutoGenTriggered(true)
      handleGenerate()
    }
  }, [prefillType, prefillRisk, autoGenTriggered])

  const loadTemplates = async () => {
    try {
      const t = await apiClient.getCuadTemplates()
      setTemplates(t)
    } catch {
      // Fallback: use default list
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    setError(null)
    setGeneratedClause(null)
    setCopied(false)

    try {
      const result = await apiClient.generateClause({
        clause_type: selectedType,
        risk_description: riskDescription,
        jurisdiction,
        contract_context: contractContext,
      })
      setGeneratedClause(result)
    } catch (e: any) {
      setError(e.message ?? "Failed to generate clause")
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopy = () => {
    if (generatedClause) {
      navigator.clipboard.writeText(generatedClause.clause_text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  // Build category list from templates or fallback
  const categories = templates.length > 0
    ? templates.map((t) => ({
        id: t.clause_type,
        name: t.title,
        cuadCategory: t.cuad_category,
      }))
    : Object.entries(CLAUSE_ICONS).map(([key]) => ({
        id: key,
        name: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        cuadCategory: key,
      }))

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          AI Clause Generator
        </h1>
        <p className="text-muted-foreground mt-2">
          Generate contract-ready clauses based on CUAD dataset patterns, tailored to your risk context and jurisdiction.
        </p>
      </div>

      {/* Pre-fill banner */}
      {prefillType && prefillRisk && (
        <Card className="p-4 border-primary/30 bg-primary/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium">Generating clause for detected risk</p>
              <p className="text-xs text-muted-foreground mt-1">
                <span className="font-medium">Type:</span> {prefillType.replace(/_/g, " ")} &middot;{" "}
                <span className="font-medium">Risk:</span> {prefillRisk.slice(0, 100)}{prefillRisk.length > 100 ? "…" : ""}
              </p>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clause Type Selection */}
        <div className="space-y-4">
          <Card className="p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
              CUAD Clause Types
            </h2>
            <div className="space-y-1 max-h-[480px] overflow-y-auto pr-1">
              {categories.map((cat) => {
                const Icon = CLAUSE_ICONS[cat.id] ?? FileCode
                const isActive = selectedType === cat.id
                return (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedType(cat.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors text-sm ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent text-foreground"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 flex-shrink-0" />
                      <span className="font-medium">{cat.name}</span>
                      <ChevronRight className={`w-3.5 h-3.5 ml-auto ${isActive ? "text-primary-foreground" : "text-muted-foreground"}`} />
                    </div>
                  </button>
                )
              })}
            </div>
          </Card>

          {/* Tips */}
          <Card className="p-5">
            <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              Tips
            </h3>
            <ul className="space-y-2 text-xs text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Clauses follow CUAD dataset patterns used in 510+ commercial contracts</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Always review generated clauses with legal counsel before use</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Specify jurisdiction for locally compliant language</span>
              </li>
            </ul>
          </Card>
        </div>

        {/* Generation Form + Output */}
        <div className="lg:col-span-2 space-y-6">
          {/* Input Form */}
          <Card className="p-6 space-y-4">
            <h2 className="text-lg font-semibold">
              Generate {categories.find((c) => c.id === selectedType)?.name ?? selectedType.replace(/_/g, " ")} Clause
            </h2>

            <div>
              <label className="block text-sm font-medium mb-1.5">
                Risk / Missing Clause Description
              </label>
              <textarea
                className="w-full min-h-[80px] p-3 rounded-lg border border-input bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                placeholder="E.g., No limitation of liability found — contract exposes to unlimited damages…"
                value={riskDescription}
                onChange={(e) => setRiskDescription(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">Jurisdiction</label>
                <select
                  className="w-full p-2.5 rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                  value={jurisdiction}
                  onChange={(e) => setJurisdiction(e.target.value)}
                >
                  {JURISDICTION_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1.5">Clause Type</label>
                <select
                  className="w-full p-2.5 rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">
                Contract Context <span className="text-muted-foreground font-normal">(optional)</span>
              </label>
              <textarea
                className="w-full min-h-[60px] p-3 rounded-lg border border-input bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                placeholder="Any relevant contract details or summary to help tailor the clause…"
                value={contractContext}
                onChange={(e) => setContractContext(e.target.value)}
              />
            </div>

            <Button
              className="w-full"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Clause
                </>
              )}
            </Button>

            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}
          </Card>

          {/* Generated Output */}
          {generatedClause && (
            <Card className="p-6 space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                    {generatedClause.clause_title}
                  </h2>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {generatedClause.cuad_category}
                    </Badge>
                    {generatedClause.jurisdiction && generatedClause.jurisdiction !== "general" && (
                      <Badge variant="outline" className="text-xs">
                        <Globe className="w-3 h-3 mr-1" />
                        {generatedClause.jurisdiction}
                      </Badge>
                    )}
                    {generatedClause.template_used && (
                      <Badge variant="outline" className="text-xs text-emerald-600 dark:text-emerald-400">
                        CUAD Template
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={handleCopy}>
                    {copied ? (
                      <><CheckCircle className="w-4 h-4 mr-1.5 text-emerald-500" /> Copied</>
                    ) : (
                      <><Copy className="w-4 h-4 mr-1.5" /> Copy</>
                    )}
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleGenerate} disabled={isGenerating}>
                    <RefreshCw className={`w-4 h-4 mr-1.5 ${isGenerating ? "animate-spin" : ""}`} />
                    Regenerate
                  </Button>
                </div>
              </div>

              {/* Clause Text */}
              <div className="p-4 rounded-lg bg-muted/50 border border-border">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">
                  {generatedClause.clause_text}
                </pre>
              </div>

              {/* Explanation */}
              <div className="p-4 rounded-lg border border-primary/20 bg-primary/5">
                <h3 className="text-sm font-semibold mb-1.5 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-primary" />
                  Why is this clause recommended?
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {generatedClause.explanation}
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ClauseGeneratorPage() {
  return (
    <Suspense fallback={
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex items-center gap-3 text-muted-foreground animate-pulse mt-12">
          <Clock className="w-5 h-5" />
          <span>Loading…</span>
        </div>
      </div>
    }>
      <ClauseGeneratorContent />
    </Suspense>
  )
}
