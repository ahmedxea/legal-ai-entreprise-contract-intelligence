"use client"

import { useState, useMemo, useEffect, useRef } from "react"
import { RiskFilterBar } from "@/components/risk-filter-bar"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, AlertTriangle, CheckCircle2, TrendingUp, FileText, AlertCircle, Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api-client"

// Animated counter hook
function useAnimatedCounter(target: number, duration = 1000) {
  const [count, setCount] = useState(0)
  const hasAnimated = useRef(false)

  useEffect(() => {
    if (hasAnimated.current) {
      setCount(target)
      return
    }

    hasAnimated.current = true
    let startTime: number | null = null
    const startValue = 0

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
      setCount(Math.floor(startValue + (target - startValue) * eased))

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [target, duration])

  return count
}

// Shape expected by RiskFilterBar
interface UIRisk {
  id: number
  contract: string
  severity: string
  category: string
  description: string
  recommendation: string
  date: string
}

interface UIContract {
  id: number
  name: string
}

interface RiskCategory {
  name: string
  count: number
  severity: string
  trend: string
}

function toTitleCase(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function RiskAnalysisPage() {
  const [filters, setFilters] = useState({
    riskLevel: "All Levels",
    contract: "All Contracts",
    dateRange: { from: null, to: null },
  })

  const [loading, setLoading] = useState(true)
  const [allRisks, setAllRisks] = useState<UIRisk[]>([])
  const [contracts, setContracts] = useState<UIContract[]>([])
  const [complianceScore, setComplianceScore] = useState(0)
  const [riskCategories, setRiskCategories] = useState<RiskCategory[]>([])
  const [isVisible, setIsVisible] = useState(false)

  // Trigger entrance animations after load
  useEffect(() => {
    if (!loading) {
      const timer = setTimeout(() => setIsVisible(true), 100)
      return () => clearTimeout(timer)
    }
  }, [loading])

  useEffect(() => {
    let cancelled = false

    async function loadRisks() {
      setLoading(true)
      try {
        const contractList = await apiClient.getContracts()
        const analyzedContracts = contractList.filter((c) => c.status === "analyzed")

        if (cancelled) return

        const uiContracts: UIContract[] = analyzedContracts.map((c, i) => ({
          id: i + 1,
          name: c.filename,
        }))

        // Fetch analysis for each analyzed contract in parallel
        const analyses = await Promise.all(
          analyzedContracts.map((c) =>
            apiClient.getContractAnalysis(c.id).catch(() => null)
          )
        )

        if (cancelled) return

        const aggregatedRisks: UIRisk[] = []
        let riskIdCounter = 1
        let totalRiskScore = 0
        let scoreCount = 0

        analyses.forEach((analysis, idx) => {
          if (!analysis) return
          const contract = analyzedContracts[idx]
          const dateStr = contract.uploaded_at
            ? new Date(contract.uploaded_at).toISOString().split("T")[0]
            : new Date().toISOString().split("T")[0]

          if (typeof analysis.overall_risk_score === "number") {
            totalRiskScore += analysis.overall_risk_score
            scoreCount++
          }

          ;(analysis.risks ?? []).forEach((r) => {
            aggregatedRisks.push({
              id: riskIdCounter++,
              contract: contract.filename,
              severity: r.severity ?? "low",
              category: r.risk_type ? toTitleCase(r.risk_type) : "General Risk",
              description: r.description,
              recommendation: r.source_text ?? r.recommendation ?? "Review this clause carefully.",
              date: dateStr,
            })
          })
        })

        // Derive compliance score (0-100, higher = safer)
        const avgScore = scoreCount > 0 ? totalRiskScore / scoreCount : 0
        const derivedCompliance = Math.round(Math.max(0, Math.min(100, 100 - avgScore * 10)))

        // Group into categories
        const categoryMap: Record<string, { count: number; highCount: number; mediumCount: number }> = {}
        aggregatedRisks.forEach((r) => {
          if (!categoryMap[r.category]) {
            categoryMap[r.category] = { count: 0, highCount: 0, mediumCount: 0 }
          }
          categoryMap[r.category].count++
          if (r.severity === "high" || r.severity === "critical") categoryMap[r.category].highCount++
          else if (r.severity === "medium") categoryMap[r.category].mediumCount++
        })

        const derivedCategories: RiskCategory[] = Object.entries(categoryMap)
          .sort((a, b) => b[1].count - a[1].count)
          .slice(0, 5)
          .map(([name, data]) => ({
            name,
            count: data.count,
            severity: data.highCount > 0 ? "high" : data.mediumCount > 0 ? "medium" : "low",
            trend: "stable",
          }))

        setAllRisks(aggregatedRisks)
        setContracts(uiContracts)
        setComplianceScore(derivedCompliance)
        setRiskCategories(derivedCategories)
      } catch (err) {
        console.error("Failed to load risk data:", err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadRisks()
    return () => {
      cancelled = true
    }
  }, [])

  const riskSummary = useMemo(
    () => ({
      total: allRisks.length,
      high: allRisks.filter((r) => r.severity === "high" || r.severity === "critical").length,
      medium: allRisks.filter((r) => r.severity === "medium").length,
      low: allRisks.filter((r) => r.severity === "low").length,
    }),
    [allRisks]
  )

  const filteredRisks = useMemo(() => {
    return allRisks.filter((risk) => {
      if (filters.riskLevel !== "All Levels" && risk.severity.toLowerCase() !== filters.riskLevel.toLowerCase()) {
        return false
      }

      if (filters.contract !== "All Contracts" && risk.contract !== filters.contract) {
        return false
      }

      if (filters.dateRange.from && filters.dateRange.to) {
        const riskDate = new Date(risk.date)
        const fromDate = new Date(filters.dateRange.from)
        const toDate = new Date(filters.dateRange.to)
        if (riskDate < fromDate || riskDate > toDate) {
          return false
        }
      }

      return true
    })
  }, [filters, allRisks])

  const handleFilter = (newFilters: any) => {
    setFilters(newFilters)
  }

  const complianceChecks = [
    { name: "GDPR Compliance", status: "passed", score: 95 },
    { name: "SOC 2 Requirements", status: "passed", score: 92 },
    { name: "HIPAA Standards", status: "warning", score: 78 },
    { name: "ISO 27001", status: "passed", score: 88 },
    { name: "PCI DSS", status: "failed", score: 65 },
  ]

  // Animated counters for stats
  const totalCount = useAnimatedCounter(filteredRisks.length, 1200)
  const highCount = useAnimatedCounter(filteredRisks.filter((r) => r.severity === "high").length, 1200)
  const mediumCount = useAnimatedCounter(filteredRisks.filter((r) => r.severity === "medium").length, 1200)
  const lowCount = useAnimatedCounter(filteredRisks.filter((r) => r.severity === "low").length, 1200)
  const animatedCompliance = useAnimatedCounter(complianceScore, 1500)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <Loader2 className="w-10 h-10 animate-spin text-primary" />
          <p className="text-sm">Loading risk intelligence…</p>
        </div>
      </div>
    )
  }

  if (!loading && allRisks.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4 text-muted-foreground text-center max-w-sm">
          <Shield className="w-12 h-12 text-muted-foreground/40" />
          <h2 className="text-lg font-semibold">No Risk Data Yet</h2>
          <p className="text-sm">
            Upload and fully analyse at least one contract to see risk insights here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-3 text-balance">Risk & Compliance Insights</h1>
          <p className="text-lg text-muted-foreground">
            Monitor risks, track compliance, and get actionable recommendations
          </p>
        </div>

        <div className="mb-8">
          <RiskFilterBar risks={filteredRisks} contracts={contracts} onFilter={handleFilter} />
        </div>

        {/* Risk Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card 
            className={`modern-card p-6 group hover:shadow-lg hover:-translate-y-1 transition-all duration-300 ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: '0ms' }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <span className="badge-neutral badge-modern">Total</span>
            </div>
            <p className="text-3xl font-bold mb-1 tabular-nums">{totalCount}</p>
            <p className="text-sm text-muted-foreground">Total Risks Detected</p>
          </Card>

          <Card 
            className={`modern-card p-6 border-destructive/20 bg-destructive/5 group hover:shadow-lg hover:-translate-y-1 transition-all duration-300 ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: '100ms' }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-destructive/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <AlertCircle className="w-6 h-6 text-destructive group-hover:animate-pulse" />
              </div>
              <span className="badge-error badge-modern">High</span>
            </div>
            <p className="text-3xl font-bold mb-1 text-destructive tabular-nums">{highCount}</p>
            <p className="text-sm text-muted-foreground">High Priority Risks</p>
          </Card>

          <Card 
            className={`modern-card p-6 border-warning/20 bg-warning/5 group hover:shadow-lg hover:-translate-y-1 transition-all duration-300 ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: '200ms' }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-warning/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <AlertTriangle className="w-6 h-6 text-warning" />
              </div>
              <span className="badge-warning badge-modern">Medium</span>
            </div>
            <p className="text-3xl font-bold mb-1 text-warning tabular-nums">{mediumCount}</p>
            <p className="text-sm text-muted-foreground">Medium Priority Risks</p>
          </Card>

          <Card 
            className={`modern-card p-6 border-success/20 bg-success/5 group hover:shadow-lg hover:-translate-y-1 transition-all duration-300 ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: '300ms' }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-success/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <CheckCircle2 className="w-6 h-6 text-success" />
              </div>
              <span className="badge-success badge-modern">Low</span>
            </div>
            <p className="text-3xl font-bold mb-1 text-success tabular-nums">{lowCount}</p>
            <p className="text-sm text-muted-foreground">Low Priority Risks</p>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Compliance Score */}
          <Card 
            className={`modern-card p-6 lg:col-span-1 hover:shadow-lg transition-all duration-500 ${
              isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
            }`}
            style={{ transitionDelay: '400ms' }}
          >
            <h2 className="text-xl font-semibold mb-6">Overall Compliance Score</h2>
            <div className="flex flex-col items-center justify-center py-8">
              <div className="relative w-40 h-40 mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="none"
                    className="text-slate-200 dark:text-slate-700"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 70}`}
                    strokeDashoffset={`${2 * Math.PI * 70 * (1 - animatedCompliance / 100)}`}
                    className="text-success transition-all duration-1000 ease-out"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-4xl font-bold tabular-nums">{animatedCompliance}</p>
                    <p className="text-sm text-muted-foreground">Score</p>
                  </div>
                </div>
              </div>
              <span className="badge-success badge-modern animate-pulse">Good Standing</span>
            </div>
          </Card>

          {/* Risk Categories */}
          <Card 
            className={`modern-card p-6 lg:col-span-2 hover:shadow-lg transition-all duration-500 ${
              isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
            }`}
            style={{ transitionDelay: '500ms' }}
          >
            <h2 className="text-xl font-semibold mb-6">Risk Categories</h2>
            <div className="space-y-4">
              {riskCategories.map((category, index) => (
                <div 
                  key={index} 
                  className={`flex items-center gap-4 group transition-all duration-300 ${
                    isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'
                  }`}
                  style={{ transitionDelay: `${600 + index * 100}ms` }}
                >
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium group-hover:text-primary transition-colors">{category.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground tabular-nums">{category.count} issues</span>
                        {category.trend === "up" && <TrendingUp className="w-4 h-4 text-destructive animate-pulse" />}
                        {category.trend === "down" && <TrendingUp className="w-4 h-4 text-success rotate-180 animate-pulse" />}
                      </div>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ease-out ${
                          category.severity === "high"
                            ? "bg-destructive"
                            : category.severity === "medium"
                              ? "bg-warning"
                              : "bg-success"
                        }`}
                        style={{ 
                          width: isVisible ? `${(category.count / riskSummary.total) * 100}%` : '0%',
                          transitionDelay: `${700 + index * 100}ms`
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Compliance Checks */}
        <Card 
          className={`modern-card p-6 mb-8 transition-all duration-500 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
          style={{ transitionDelay: '900ms' }}
        >
          <h2 className="text-xl font-semibold mb-6">Compliance Checks</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {complianceChecks.map((check, index) => (
              <div 
                key={index} 
                className={`p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-border hover:border-primary/50 hover:shadow-md hover:-translate-y-1 transition-all duration-300 cursor-pointer group ${
                  isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
                }`}
                style={{ transitionDelay: `${1000 + index * 80}ms` }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300 ${
                      check.status === "passed"
                        ? "bg-success/10"
                        : check.status === "warning"
                          ? "bg-warning/10"
                          : "bg-destructive/10"
                    }`}
                  >
                    {check.status === "passed" ? (
                      <CheckCircle2 className="w-5 h-5 text-success" />
                    ) : check.status === "warning" ? (
                      <AlertTriangle className="w-5 h-5 text-warning" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-destructive" />
                    )}
                  </div>
                </div>
                <p className="font-medium text-sm mb-1 group-hover:text-primary transition-colors">{check.name}</p>
                <p className="text-2xl font-bold mb-1 tabular-nums">{check.score}%</p>
                <span
                  className={`badge-modern ${
                    check.status === "passed" ? "badge-success" : check.status === "warning" ? "badge-warning" : "badge-error"
                  }`}
                >
                  {check.status}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Recent Risks */}
        <Card 
          className={`modern-card p-6 transition-all duration-500 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
          style={{ transitionDelay: '1100ms' }}
        >
          <h2 className="text-xl font-semibold mb-6">
            {filters.riskLevel !== "All Levels" || filters.contract !== "All Contracts" || filters.dateRange.from
              ? "Filtered Risk Detections"
              : "Recent Risk Detections"}
          </h2>
          <div className="space-y-4">
            {filteredRisks.length > 0 ? (
              filteredRisks.map((risk, idx) => (
                <div
                  key={risk.id}
                  className={`p-5 rounded-lg border border-border hover:border-primary/50 hover:bg-accent/30 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 cursor-pointer group ${
                    isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'
                  }`}
                  style={{ transitionDelay: `${1200 + Math.min(idx * 50, 500)}ms` }}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300 ${
                        risk.severity === "high"
                          ? "bg-destructive/10"
                          : risk.severity === "medium"
                            ? "bg-warning/10"
                            : "bg-success/10"
                      }`}
                    >
                      {risk.severity === "high" ? (
                        <AlertCircle className="w-5 h-5 text-destructive group-hover:animate-pulse" />
                      ) : risk.severity === "medium" ? (
                        <AlertTriangle className="w-5 h-5 text-warning" />
                      ) : (
                        <CheckCircle2 className="w-5 h-5 text-success" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge
                            variant={
                              risk.severity === "high"
                                ? "destructive"
                                : risk.severity === "medium"
                                  ? "secondary"
                                  : "default"
                            }
                            className="group-hover:shadow-sm transition-shadow"
                          >
                            {risk.severity.toUpperCase()}
                          </Badge>
                          <Badge variant="outline" className="group-hover:border-primary/50 transition-colors">{risk.category}</Badge>
                        </div>
                        <span className="text-sm text-muted-foreground whitespace-nowrap">{risk.date}</span>
                      </div>

                      <div className="flex items-center gap-2 mb-3">
                        <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0 group-hover:text-primary transition-colors" />
                        <p className="font-medium text-sm group-hover:text-primary transition-colors">{risk.contract}</p>
                      </div>

                      <p className="text-sm mb-3 leading-relaxed">{risk.description}</p>

                      <div className="p-3 rounded-lg bg-primary/5 border border-primary/10 group-hover:bg-primary/10 group-hover:border-primary/20 transition-colors">
                        <p className="text-xs font-medium text-primary mb-1">💡 Recommendation</p>
                        <p className="text-sm leading-relaxed">{risk.recommendation}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <Shield className="w-12 h-12 mx-auto mb-3 text-muted-foreground/30" />
                <p className="text-muted-foreground">No risks match the selected filters</p>
              </div>
            )}
          </div>
        </Card>
      </main>
    </div>
  )
}
