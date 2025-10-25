"use client"

import { useState, useMemo } from "react"
import { Navigation } from "@/components/navigation"
import { RiskFilterBar } from "@/components/risk-filter-bar"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, AlertTriangle, CheckCircle2, TrendingUp, FileText, AlertCircle } from "lucide-react"

export default function RiskAnalysisPage() {
  const [filters, setFilters] = useState({
    riskLevel: "All Levels",
    contract: "All Contracts",
    dateRange: { from: null, to: null },
  })

  const riskSummary = {
    total: 89,
    high: 12,
    medium: 34,
    low: 43,
  }

  const complianceScore = 87

  const riskCategories = [
    { name: "Financial Risk", count: 23, severity: "high", trend: "up" },
    { name: "Legal Compliance", count: 18, severity: "medium", trend: "down" },
    { name: "Operational Risk", count: 15, severity: "medium", trend: "stable" },
    { name: "Data Privacy", count: 12, severity: "high", trend: "up" },
    { name: "Termination Clauses", count: 21, severity: "low", trend: "stable" },
  ]

  const allRisks = [
    {
      id: 1,
      contract: "Service Agreement 2025.pdf",
      severity: "high",
      category: "Financial Risk",
      description: "Unlimited liability clause without cap or insurance requirement",
      recommendation: "Add liability cap of 2x annual contract value and require professional indemnity insurance",
      date: "2025-01-15",
    },
    {
      id: 2,
      contract: "NDA - Tech Corp.docx",
      severity: "medium",
      category: "Legal Compliance",
      description: "Auto-renewal clause without adequate notice period",
      recommendation: "Require 90-day written notice before auto-renewal takes effect",
      date: "2025-01-14",
    },
    {
      id: 3,
      contract: "Employment Contract.pdf",
      severity: "high",
      category: "Data Privacy",
      description: "Missing GDPR compliance clauses for EU data processing",
      recommendation: "Add Data Processing Agreement (DPA) and GDPR compliance terms",
      date: "2025-01-14",
    },
    {
      id: 4,
      contract: "Vendor Agreement.pdf",
      severity: "low",
      category: "Operational Risk",
      description: "Vague service level agreement (SLA) definitions",
      recommendation: "Define specific uptime requirements, response times, and penalties",
      date: "2025-01-13",
    },
  ]

  const contracts = [
    { id: 1, name: "Service Agreement 2025.pdf" },
    { id: 2, name: "NDA - Tech Corp.docx" },
    { id: 3, name: "Employment Contract.pdf" },
    { id: 4, name: "Vendor Agreement.pdf" },
  ]

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
  }, [filters])

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

  return (
    <div className="min-h-screen">
      <Navigation />

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
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-xl gradient-blue flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <Badge variant="outline">Total</Badge>
            </div>
            <p className="text-3xl font-bold mb-1">{filteredRisks.length}</p>
            <p className="text-sm text-muted-foreground">Total Risks Detected</p>
          </Card>

          <Card className="p-6 border-destructive/20 bg-destructive/5">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-destructive/10 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-destructive" />
              </div>
              <Badge variant="destructive">High</Badge>
            </div>
            <p className="text-3xl font-bold mb-1 text-destructive">
              {filteredRisks.filter((r) => r.severity === "high").length}
            </p>
            <p className="text-sm text-muted-foreground">High Priority Risks</p>
          </Card>

          <Card className="p-6 border-warning/20 bg-warning/5">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-warning/10 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-warning" />
              </div>
              <Badge className="bg-warning text-warning-foreground">Medium</Badge>
            </div>
            <p className="text-3xl font-bold mb-1 text-warning">
              {filteredRisks.filter((r) => r.severity === "medium").length}
            </p>
            <p className="text-sm text-muted-foreground">Medium Priority Risks</p>
          </Card>

          <Card className="p-6 border-success/20 bg-success/5">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-success" />
              </div>
              <Badge className="bg-success text-success-foreground">Low</Badge>
            </div>
            <p className="text-3xl font-bold mb-1 text-success">
              {filteredRisks.filter((r) => r.severity === "low").length}
            </p>
            <p className="text-sm text-muted-foreground">Low Priority Risks</p>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Compliance Score */}
          <Card className="p-6 lg:col-span-1">
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
                    className="text-secondary"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 70}`}
                    strokeDashoffset={`${2 * Math.PI * 70 * (1 - complianceScore / 100)}`}
                    className="text-success transition-all duration-1000"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-4xl font-bold">{complianceScore}</p>
                    <p className="text-sm text-muted-foreground">Score</p>
                  </div>
                </div>
              </div>
              <Badge className="bg-success text-success-foreground">Good Standing</Badge>
            </div>
          </Card>

          {/* Risk Categories */}
          <Card className="p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-6">Risk Categories</h2>
            <div className="space-y-4">
              {riskCategories.map((category, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{category.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">{category.count} issues</span>
                        {category.trend === "up" && <TrendingUp className="w-4 h-4 text-destructive" />}
                        {category.trend === "down" && <TrendingUp className="w-4 h-4 text-success rotate-180" />}
                      </div>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          category.severity === "high"
                            ? "bg-destructive"
                            : category.severity === "medium"
                              ? "bg-warning"
                              : "bg-success"
                        }`}
                        style={{ width: `${(category.count / riskSummary.total) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Compliance Checks */}
        <Card className="p-6 mb-8">
          <h2 className="text-xl font-semibold mb-6">Compliance Checks</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {complianceChecks.map((check, index) => (
              <div key={index} className="p-4 rounded-lg bg-secondary/50">
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center ${
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
                <p className="font-medium text-sm mb-1">{check.name}</p>
                <p className="text-2xl font-bold mb-1">{check.score}%</p>
                <Badge
                  variant={
                    check.status === "passed" ? "default" : check.status === "warning" ? "secondary" : "destructive"
                  }
                  className="text-xs"
                >
                  {check.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        {/* Recent Risks */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6">
            {filters.riskLevel !== "All Levels" || filters.contract !== "All Contracts" || filters.dateRange.from
              ? "Filtered Risk Detections"
              : "Recent Risk Detections"}
          </h2>
          <div className="space-y-4">
            {filteredRisks.length > 0 ? (
              filteredRisks.map((risk) => (
                <div
                  key={risk.id}
                  className="p-5 rounded-lg border border-border hover:border-primary/50 transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        risk.severity === "high"
                          ? "bg-destructive/10"
                          : risk.severity === "medium"
                            ? "bg-warning/10"
                            : "bg-success/10"
                      }`}
                    >
                      {risk.severity === "high" ? (
                        <AlertCircle className="w-5 h-5 text-destructive" />
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
                          >
                            {risk.severity.toUpperCase()}
                          </Badge>
                          <Badge variant="outline">{risk.category}</Badge>
                        </div>
                        <span className="text-sm text-muted-foreground whitespace-nowrap">{risk.date}</span>
                      </div>

                      <div className="flex items-center gap-2 mb-3">
                        <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <p className="font-medium text-sm">{risk.contract}</p>
                      </div>

                      <p className="text-sm mb-3">{risk.description}</p>

                      <div className="p-3 rounded-lg bg-primary/5 border border-primary/10">
                        <p className="text-xs font-medium text-primary mb-1">Recommendation</p>
                        <p className="text-sm">{risk.recommendation}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No risks match the selected filters</p>
              </div>
            )}
          </div>
        </Card>
      </main>
    </div>
  )
}
