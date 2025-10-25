"use client"

import { Navigation } from "@/components/navigation"
import { ProtectedRoute } from "@/components/protected-route"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Calendar, Users, AlertTriangle, Clock, Download, Eye } from "lucide-react"
import { useState } from "react"
import { motion } from "framer-motion"

export default function DashboardPage() {
  const [selectedContract, setSelectedContract] = useState<number | null>(1)

  const contracts = [
    {
      id: 1,
      name: "Service Agreement 2025.pdf",
      type: "Service Agreement",
      parties: ["Acme Corp", "Tech Solutions Inc"],
      value: "$250,000",
      startDate: "2025-01-01",
      endDate: "2026-01-01",
      status: "Active",
      riskLevel: "Low",
      fileUrl: "https://example.com/contracts/service-agreement-2025.pdf",
      keyTerms: ["Payment Terms", "Termination Clause", "Liability Cap", "Confidentiality"],
      risks: [
        { severity: "medium", description: "Auto-renewal clause without notice period" },
        { severity: "low", description: "Liability cap may be insufficient for project scope" },
      ],
      obligations: [
        { party: "Acme Corp", description: "Monthly payment of $20,833", dueDate: "1st of each month" },
        { party: "Tech Solutions Inc", description: "Deliver quarterly reports", dueDate: "End of each quarter" },
      ],
    },
  ]

  const contract = contracts.find((c) => c.id === selectedContract)

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-b from-white to-[#F9FAFB]">
        <Navigation />

        <main className="pt-24 pb-16 px-6 max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-10">
            <div>
              <h1 className="text-4xl font-bold text-[#111827] leading-tight">Contract Dashboard</h1>
              <p className="text-[#6B7280] mt-2">View insights, risks, and performance summaries</p>
            </div>
            <Button className="bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white rounded-xl px-6 py-3 hover:opacity-90 shadow-[0_0_15px_rgba(0,198,255,0.3)] transition-all hover:shadow-[0_0_25px_rgba(0,198,255,0.5)]">
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <div className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] p-6">
                <h2 className="text-lg font-semibold text-[#111827] mb-4">Recent Contracts</h2>
                <div className="space-y-2">
                  {contracts.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => setSelectedContract(c.id)}
                      className={`w-full text-left p-4 rounded-2xl transition-all ${
                        selectedContract === c.id
                          ? "bg-gradient-to-r from-[#007AFF]/10 to-[#00C6FF]/10 border border-[#00C6FF]/20"
                          : "hover:bg-[#F3F4F6]"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate text-sm text-[#111827]">{c.name}</p>
                          <p className="text-xs mt-1 text-[#6B7280]">{c.type}</p>
                        </div>
                        <Badge
                          className={`text-xs ${
                            c.riskLevel === "Low"
                              ? "bg-[#E0F7F4] text-[#007AFF] border-0"
                              : c.riskLevel === "Medium"
                                ? "bg-[#FFF9E6] text-[#CBA800] border-0"
                                : "bg-[#FFECEC] text-[#D93025] border-0"
                          }`}
                        >
                          {c.riskLevel}
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="lg:col-span-2 space-y-6">
              {contract && (
                <>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6"
                  >
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex-1">
                        <h2 className="text-2xl font-bold text-[#111827] mb-2">{contract.name}</h2>
                        <p className="text-[#6B7280]">{contract.type}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          onClick={() => window.open(contract.fileUrl, "_blank")}
                          className="bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white rounded-xl hover:opacity-90 shadow-[0_0_12px_rgba(0,198,255,0.3)] transition-all hover:shadow-[0_0_20px_rgba(0,198,255,0.5)]"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View PDF
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-[#6B7280] mb-1">Status</p>
                        <Badge className="bg-[#E0F7F4] text-[#10B981] border-0">{contract.status}</Badge>
                      </div>
                      <div>
                        <p className="text-sm text-[#6B7280] mb-1">Risk Level</p>
                        <Badge
                          className={`${
                            contract.riskLevel === "Low"
                              ? "bg-[#E0F7F4] text-[#007AFF]"
                              : contract.riskLevel === "Medium"
                                ? "bg-[#FFF9E6] text-[#CBA800]"
                                : "bg-[#FFECEC] text-[#D93025]"
                          } border-0`}
                        >
                          {contract.riskLevel}
                        </Badge>
                      </div>
                      <div>
                        <p className="text-sm text-[#6B7280] mb-1">Contract Value</p>
                        <p className="font-semibold text-[#111827]">{contract.value}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#6B7280] mb-1">Duration</p>
                        <p className="font-semibold text-[#111827]">12 months</p>
                      </div>
                    </div>
                  </motion.div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                      className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6"
                    >
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center shadow-[0_0_10px_rgba(0,122,255,0.3)]">
                          <Users className="w-5 h-5 text-white" />
                        </div>
                        <h3 className="text-lg font-semibold text-[#111827]">Parties Involved</h3>
                      </div>
                      <div className="space-y-2">
                        {contract.parties.map((party, index) => (
                          <div key={index} className="p-3 rounded-xl bg-[#F9FAFB]">
                            <p className="font-medium text-[#111827]">{party}</p>
                          </div>
                        ))}
                      </div>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.15 }}
                      className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6"
                    >
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center shadow-[0_0_10px_rgba(0,122,255,0.3)]">
                          <Calendar className="w-5 h-5 text-white" />
                        </div>
                        <h3 className="text-lg font-semibold text-[#111827]">Important Dates</h3>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm text-[#6B7280]">Start Date</p>
                          <p className="font-medium text-[#111827]">{contract.startDate}</p>
                        </div>
                        <div>
                          <p className="text-sm text-[#6B7280]">End Date</p>
                          <p className="font-medium text-[#111827]">{contract.endDate}</p>
                        </div>
                      </div>
                    </motion.div>
                  </div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6"
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center shadow-[0_0_10px_rgba(0,122,255,0.3)]">
                        <FileText className="w-5 h-5 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-[#111827]">Key Terms Identified</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {contract.keyTerms.map((term, index) => (
                        <Badge
                          key={index}
                          className="px-3 py-1 bg-[#F9FAFB] text-[#111827] border border-[#E5E7EB] hover:bg-[#F3F4F6] transition-colors"
                        >
                          {term}
                        </Badge>
                      ))}
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                    className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6"
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-xl bg-[#FFF9E6] flex items-center justify-center">
                        <AlertTriangle className="w-5 h-5 text-[#CBA800]" />
                      </div>
                      <h3 className="text-lg font-semibold text-[#111827]">Detected Risks & Issues</h3>
                    </div>
                    <div className="space-y-3">
                      {contract.risks.map((risk, index) => (
                        <div key={index} className="flex items-start gap-3 p-4 rounded-xl bg-[#F9FAFB]">
                          <div
                            className={`w-2 h-2 rounded-full mt-2 ${risk.severity === "high" ? "bg-[#D93025]" : risk.severity === "medium" ? "bg-[#CBA800]" : "bg-[#007AFF]"}`}
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge
                                className={`text-xs ${
                                  risk.severity === "high"
                                    ? "bg-[#FFECEC] text-[#D93025]"
                                    : risk.severity === "medium"
                                      ? "bg-[#FFF9E6] text-[#CBA800]"
                                      : "bg-[#E0F7F4] text-[#007AFF]"
                                } border-0`}
                              >
                                {risk.severity.toUpperCase()}
                              </Badge>
                            </div>
                            <p className="text-sm text-[#111827]">{risk.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6"
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center shadow-[0_0_10px_rgba(0,122,255,0.3)]">
                        <Clock className="w-5 h-5 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-[#111827]">Key Obligations</h3>
                    </div>
                    <div className="space-y-3">
                      {contract.obligations.map((obligation, index) => (
                        <div key={index} className="p-4 rounded-xl bg-[#F9FAFB]">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <p className="font-medium mb-1 text-[#111827]">{obligation.party}</p>
                              <p className="text-sm text-[#6B7280]">{obligation.description}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-[#6B7280] mb-1">Due Date</p>
                              <p className="text-sm font-medium text-[#111827]">{obligation.dueDate}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
