"use client"

import { Suspense } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  ArrowLeft,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Sparkles,
  Users,
  Calendar,
  Scale,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Trash2,
  Eye,
  Loader2,
} from "lucide-react"
import { useState, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { apiClient, type Contract, type ContractAnalysisResult, type Risk } from "@/lib/api-client"
import { ContractPreviewPanel } from "@/components/contract-preview-panel"

const SEVERITY_CONFIG: Record<string, { label: string; className: string }> = {
  critical: { label: "Critical", className: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300" },
  high: { label: "High", className: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
  medium: { label: "Medium", className: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300" },
  low: { label: "Low", className: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
}

function RiskBadge({ severity }: { severity: string }) {
  const cfg = SEVERITY_CONFIG[severity?.toLowerCase()] ?? SEVERITY_CONFIG.low
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cfg.className}`}>{cfg.label}</span>
}

function RiskScore({ score }: { score: number }) {
  const color = score >= 7 ? "text-red-500" : score >= 4 ? "text-amber-500" : "text-emerald-500"
  const label = score >= 7 ? "High Risk" : score >= 4 ? "Medium Risk" : "Low Risk"
  return (
    <div className="flex items-center gap-3">
      <span className={`text-5xl font-bold ${color}`}>{score.toFixed(1)}</span>
      <div>
        <p className={`font-semibold ${color}`}>{label}</p>
        <p className="text-xs text-muted-foreground">out of 10</p>
      </div>
    </div>
  )
}

function ContractDetailContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const id = searchParams.get("id") ?? ""

  const [contract, setContract] = useState<Contract | null>(null)
  const [analysis, setAnalysis] = useState<ContractAnalysisResult | null>(null)
  const [loadingContract, setLoadingContract] = useState(true)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"analysis" | "preview">("analysis")
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!id) return
    loadContractData()
  }, [id])

  const loadContractData = async () => {
    try {
      setLoadingContract(true)
      setError(null)
      const c = await apiClient.getContract(id)
      setContract(c)
      if (c.status === "analyzed" || c.status === "completed") {
        await loadAnalysis()
      }
    } catch (e: any) {
      setError(e.message ?? "Failed to load contract")
    } finally {
      setLoadingContract(false)
    }
  }

  const loadAnalysis = async () => {
    try {
      setLoadingAnalysis(true)
      const a = await apiClient.getContractAnalysis(id)
      setAnalysis(a)
    } catch {
      // analysis not yet available
    } finally {
      setLoadingAnalysis(false)
    }
  }

  const handleAnalyze = async () => {
    if (!contract) return
    try {
      setAnalyzing(true)
      setError(null)
      await apiClient.analyzeContract(id)
      await apiClient.pollContractStatus(id, ["analyzed", "completed"], 3000, 200)
      await loadContractData()
    } catch (e: any) {
      setError(e.message ?? "Analysis failed")
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDelete = async () => {
    try {
      setDeleting(true)
      await apiClient.deleteContract(id)
      router.push("/contracts")
    } catch (e: any) {
      setError(e.message ?? "Failed to delete contract")
      setDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  if (!id) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <Link href="/contracts">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Contracts
          </Button>
        </Link>
        <Card className="p-8 text-center text-muted-foreground">No contract ID provided.</Card>
      </div>
    )
  }

  if (loadingContract) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex items-center gap-3 text-muted-foreground animate-pulse mt-12">
          <Clock className="w-5 h-5" />
          <span>Loading contract…</span>
        </div>
      </div>
    )
  }

  if (error && !contract) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <Link href="/contracts">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Contracts
          </Button>
        </Link>
        <Card className="p-8 text-center text-destructive">
          <AlertTriangle className="w-8 h-8 mx-auto mb-3" />
          <p>{error}</p>
        </Card>
      </div>
    )
  }

  if (!contract) return null

  const isAnalyzed = contract.status === "analyzed" || contract.status === "completed"
  const isProcessing =
    contract.status === "uploading" ||
    contract.status === "extracting" ||
    contract.status === "processing" ||
    contract.status === "analyzing"

  const entities = analysis?.entities ?? {}
  const risks: Risk[] = analysis?.risks ?? []
  const missingClauses: string[] = analysis?.missing_clauses ?? []
  const riskScore = analysis?.overall_risk_score ?? null
  const governingLaw = entities.governing_law || contract.extracted_data?.governing_law || contract.analysis?.entities?.governing_law || contract.analysis?.extracted_data?.governing_law || null
  const uploadedAt = contract.uploaded_at ?? contract.upload_date ?? new Date().toISOString()

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contracts" className="hover:text-foreground transition-colors">
          Contracts
        </Link>
        <span>/</span>
        <span className="text-foreground font-medium truncate max-w-xs">{contract.filename}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold break-all">{contract.filename}</h1>
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              <Badge variant="outline" className="text-xs capitalize">
                {contract.language}
              </Badge>
              {contract.industry && (
                <Badge variant="outline" className="text-xs capitalize">
                  {contract.industry}
                </Badge>
              )}
              {governingLaw && (
                <Badge variant="outline" className="text-xs">
                  <Scale className="w-3 h-3 mr-1" />
                  {governingLaw}
                </Badge>
              )}
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {new Date(uploadedAt).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isAnalyzed ? (
            <Button variant="outline" size="sm" onClick={handleAnalyze} disabled={analyzing}>
              <RefreshCw className={`w-4 h-4 mr-2 ${analyzing ? "animate-spin" : ""}`} />
              Re-analyze
            </Button>
          ) : isProcessing ? (
            <Button disabled size="sm">
              <Clock className="w-4 h-4 mr-2 animate-spin" />
              Processing…
            </Button>
          ) : (
            <Button onClick={handleAnalyze} disabled={analyzing} size="sm">
              <Sparkles className="w-4 h-4 mr-2" />
              {analyzing ? "Analyzing…" : "Run Analysis"}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={() => setShowDeleteConfirm(true)}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {error && (
        <Card className="p-4 border-destructive/50 bg-destructive/5 text-destructive text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error}
        </Card>
      )}

      {/* Not yet analyzed */}
      {!isAnalyzed && !isProcessing && (
        <Card className="p-8 text-center space-y-3">
          <Sparkles className="w-10 h-10 mx-auto text-muted-foreground" />
          <p className="font-medium">This contract hasn't been analyzed yet.</p>
          <p className="text-sm text-muted-foreground">
            Click <strong>Run Analysis</strong> to extract entities, detect risks, and identify missing clauses.
          </p>
        </Card>
      )}

      {isProcessing && !isAnalyzed && (
        <Card className="p-8 text-center space-y-3 animate-pulse">
          <Clock className="w-10 h-10 mx-auto text-muted-foreground" />
          <p className="font-medium">Analysis in progress…</p>
          <p className="text-sm text-muted-foreground">This may take 30–60 seconds.</p>
        </Card>
      )}

      {/* Analysis Results */}
      {isAnalyzed && (
        <>
          {/* Tabs */}
          <div className="flex items-center gap-1 border-b">
            <button
              onClick={() => setActiveTab("analysis")}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                activeTab === "analysis"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
              Analysis
            </button>
            <button
              onClick={() => setActiveTab("preview")}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                activeTab === "preview"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Eye className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
              Contract Preview
            </button>
          </div>

          {/* Preview tab */}
          {activeTab === "preview" && (
            <Card className="p-6">
              <ContractPreviewPanel contractId={id} filename={contract.filename} risks={risks} />
            </Card>
          )}

          {/* Analysis tab */}
          {activeTab === "analysis" && (
          loadingAnalysis ? (
            <Card className="p-6 animate-pulse text-center text-muted-foreground">Loading analysis…</Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {analysis?.summary && (
                  <Card className="p-6 space-y-3">
                    <h2 className="font-semibold flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary" /> Summary
                    </h2>
                    <p className="text-sm text-muted-foreground leading-relaxed">{analysis.summary}</p>
                  </Card>
                )}

                <Card className="p-6 space-y-4">
                  <h2 className="font-semibold flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-destructive" /> Identified Risks
                    {risks.length > 0 && (
                      <Badge variant="outline" className="ml-auto text-xs">{risks.length}</Badge>
                    )}
                  </h2>
                  {risks.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No risks detected.</p>
                  ) : (
                    <div className="space-y-3">
                      {risks.map((risk, i) => (
                        <div key={i} className="p-4 rounded-lg border border-border space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-medium leading-snug">{risk.description}</p>
                            <RiskBadge severity={risk.severity} />
                          </div>
                          {risk.recommendation && (
                            <p className="text-xs text-muted-foreground">
                              <span className="font-medium">Recommendation:</span> {risk.recommendation}
                            </p>
                          )}
                          <div className="pt-1">
                            <Link
                              href={`/clauses?type=${encodeURIComponent(risk.risk_type ?? "")}&risk=${encodeURIComponent(risk.description)}&jurisdiction=${encodeURIComponent(governingLaw ?? "")}&context=${encodeURIComponent(analysis?.summary ?? "")}`}
                            >
                              <Button variant="outline" size="sm" className="h-7 text-xs">
                                <Sparkles className="w-3 h-3 mr-1.5" />
                                Generate Clause
                              </Button>
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>

                <Card className="p-6 space-y-4">
                  <h2 className="font-semibold flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-amber-500" /> Missing Clauses
                    {missingClauses.length > 0 && (
                      <Badge variant="outline" className="ml-auto text-xs">{missingClauses.length}</Badge>
                    )}
                  </h2>
                  {missingClauses.length === 0 ? (
                    <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
                      <CheckCircle className="w-4 h-4" /> All standard clauses are present.
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {missingClauses.map((clause, i) => (
                        <Link
                          key={i}
                          href={`/clauses?type=${encodeURIComponent(clause)}&risk=${encodeURIComponent(`Missing ${clause.replace(/_/g, " ")} clause`)}&jurisdiction=${encodeURIComponent(governingLaw ?? "")}&context=${encodeURIComponent(analysis?.summary ?? "")}`}
                        >
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 capitalize hover:bg-amber-200 dark:hover:bg-amber-900/60 transition-colors cursor-pointer">
                            {clause.replace(/_/g, " ")}
                            <Sparkles className="w-3 h-3" />
                          </span>
                        </Link>
                      ))}
                    </div>
                  )}
                </Card>
              </div>

              <div className="space-y-6">
                {governingLaw && (
                  <Card className="p-6 space-y-3">
                    <div className="flex items-center gap-2">
                      <Scale className="w-4 h-4 text-primary" />
                      <h2 className="font-semibold">Governing Law</h2>
                    </div>
                    <p className="text-2xl font-semibold">{governingLaw}</p>
                    <p className="text-xs text-muted-foreground">Auto-detected jurisdiction signal from the contract text</p>
                  </Card>
                )}

                {riskScore !== null && (
                  <Card className="p-6 space-y-3">
                    <h2 className="font-semibold">Risk Score</h2>
                    <RiskScore score={riskScore} />
                  </Card>
                )}

                {Object.keys(entities).length > 0 && (
                  <Card className="p-6 space-y-4">
                    <h2 className="font-semibold flex items-center gap-2">
                      <Users className="w-4 h-4 text-primary" /> Key Details
                    </h2>
                    <dl className="space-y-3">
                      {entities.parties && Array.isArray(entities.parties) && entities.parties.length > 0 && (
                        <div>
                          <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Parties</dt>
                          <dd className="space-y-1">
                            {entities.parties.map((p: string, i: number) => (
                              <p key={i} className="text-sm">{p}</p>
                            ))}
                          </dd>
                        </div>
                      )}
                      {entities.effective_date && (
                        <div>
                          <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
                            <Calendar className="w-3 h-3" /> Effective Date
                          </dt>
                          <dd className="text-sm">{entities.effective_date}</dd>
                        </div>
                      )}
                      {entities.expiration_date && (
                        <div>
                          <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
                            <Calendar className="w-3 h-3" /> Expiration Date
                          </dt>
                          <dd className="text-sm">{entities.expiration_date}</dd>
                        </div>
                      )}
                      {entities.governing_law && (
                        <div>
                          <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
                            <Scale className="w-3 h-3" /> Governing Law
                          </dt>
                          <dd className="text-sm">{entities.governing_law}</dd>
                        </div>
                      )}
                      {entities.contract_value && (
                        <div>
                          <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Contract Value</dt>
                          <dd className="text-sm">{entities.contract_value}</dd>
                        </div>
                      )}
                      {entities.financial_terms && Array.isArray(entities.financial_terms) && entities.financial_terms.length > 0 && (
                        <div>
                          <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Financial Terms</dt>
                          <dd className="space-y-1">
                            {entities.financial_terms.map((term: string, i: number) => (
                              <p key={i} className="text-sm">{term}</p>
                            ))}
                          </dd>
                        </div>
                      )}
                      {entities.obligations && Array.isArray(entities.obligations) && entities.obligations.length > 0 && (
                        <div>
                          <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Key Obligations</dt>
                          <dd className="space-y-1">
                            {entities.obligations.map((ob: string, i: number) => (
                              <p key={i} className="text-sm">{ob}</p>
                            ))}
                          </dd>
                        </div>
                      )}
                    </dl>
                  </Card>
                )}
              </div>
            </div>
          )
          )}
        </>
      )}

      {/* Delete confirmation dialog */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete contract?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete <strong>{contract?.filename}</strong> and all its analysis
              data. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? (
                <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Deleting…</>
              ) : (
                "Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default function ContractDetailPage() {
  return (
    <Suspense fallback={
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex items-center gap-3 text-muted-foreground animate-pulse mt-12">
          <Clock className="w-5 h-5" />
          <span>Loading…</span>
        </div>
      </div>
    }>
      <ContractDetailContent />
    </Suspense>
  )
}
