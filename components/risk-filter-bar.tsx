"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { Calendar } from "lucide-react"
import jsPDF from "jspdf"
import autoTable from "jspdf-autotable"

interface Risk {
  id: number
  contract: string
  severity: string
  category: string
  description: string
  recommendation: string
  date: string
}

interface Contract {
  id: number
  name: string
}

interface RiskFilterBarProps {
  risks: Risk[]
  contracts: Contract[]
  onFilter: (filters: {
    riskLevel: string
    contract: string
    dateRange: { from: Date | null; to: Date | null }
  }) => void
}

export function RiskFilterBar({ risks, contracts, onFilter }: RiskFilterBarProps) {
  const [riskLevel, setRiskLevel] = useState("All Levels")
  const [contract, setContract] = useState("All Contracts")
  const [dateRange, setDateRange] = useState<{ from: Date | null; to: Date | null }>({
    from: null,
    to: null,
  })

  const applyFilters = () => {
    onFilter({ riskLevel, contract, dateRange })
  }

  const exportPDF = () => {
    const doc = new jsPDF()
    doc.setFontSize(16)
    doc.text("Risk Report", 14, 16)
    doc.setFontSize(10)
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 24)
    autoTable(doc, {
      startY: 30,
      head: [["Level", "Category", "Date", "Contract", "Issue", "Recommendation"]],
      body: risks.map((r) => [r.severity, r.category, r.date, r.contract, r.description, r.recommendation]),
      styles: { fontSize: 8, cellPadding: 3 },
      columnStyles: { 4: { cellWidth: 50 }, 5: { cellWidth: 50 } },
    })
    doc.save("Risk_Report.pdf")
  }

  const exportCSV = () => {
    const csvContent =
      "Level,Category,Date,Contract,Issue,Recommendation\n" +
      risks
        .map((r) => `${r.severity},${r.category},${r.date},${r.contract},"${r.description}","${r.recommendation}"`)
        .join("\n")

    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "Risk_Report.csv"
    link.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 rounded-2xl glass-card border border-primary/20">
      {/* Risk Level Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            className="rounded-xl bg-background/50 backdrop-blur-sm border-primary/30 hover:bg-background/70 hover:border-primary/50 transition-all"
          >
            {riskLevel}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="glass-card border-primary/20 rounded-xl">
          {["All Levels", "High", "Medium", "Low"].map((lvl) => (
            <DropdownMenuItem
              key={lvl}
              onClick={() => {
                setRiskLevel(lvl)
              }}
              className="cursor-pointer"
            >
              {lvl}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Contract Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            className="rounded-xl bg-background/50 backdrop-blur-sm border-primary/30 hover:bg-background/70 hover:border-primary/50 transition-all"
          >
            {contract}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="glass-card border-primary/20 rounded-xl max-h-[300px] overflow-y-auto">
          <DropdownMenuItem
            onClick={() => {
              setContract("All Contracts")
            }}
            className="cursor-pointer"
          >
            All Contracts
          </DropdownMenuItem>
          {contracts.map((c) => (
            <DropdownMenuItem
              key={c.id}
              onClick={() => {
                setContract(c.name)
              }}
              className="cursor-pointer"
            >
              {c.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Date Range */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-background/50 backdrop-blur-sm border border-primary/30">
        <Calendar className="w-4 h-4 text-primary shrink-0" />
        <input
          type="date"
          aria-label="From date"
          value={dateRange.from ? dateRange.from.toISOString().split("T")[0] : ""}
          onChange={(e) =>
            setDateRange((prev) => ({ ...prev, from: e.target.value ? new Date(e.target.value) : null }))
          }
          className="text-sm bg-transparent outline-none"
          style={{ color: "rgb(var(--foreground))" }}
        />
        <span className="text-xs text-muted-foreground">–</span>
        <input
          type="date"
          aria-label="To date"
          value={dateRange.to ? dateRange.to.toISOString().split("T")[0] : ""}
          onChange={(e) =>
            setDateRange((prev) => ({ ...prev, to: e.target.value ? new Date(e.target.value) : null }))
          }
          className="text-sm bg-transparent outline-none"
          style={{ color: "rgb(var(--foreground))" }}
        />
      </div>

      {/* Apply Filter */}
      <Button onClick={applyFilters} className="rounded-xl gradient-blue text-white hover:opacity-90 transition-all">
        Apply Filter
      </Button>

      {/* Export Report */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button className="rounded-xl gradient-blue text-white hover:opacity-90 transition-all">Export Report</Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="glass-card border-primary/20 rounded-xl">
          <DropdownMenuItem onClick={exportPDF} className="cursor-pointer">
            Export as PDF
          </DropdownMenuItem>
          <DropdownMenuItem onClick={exportCSV} className="cursor-pointer">
            Export as CSV
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
