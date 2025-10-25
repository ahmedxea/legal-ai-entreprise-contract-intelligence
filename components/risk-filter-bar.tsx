"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { Calendar } from "lucide-react"

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
    // Create CSV content for simple export
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

      {/* Date Range Placeholder */}
      <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-background/50 backdrop-blur-sm border border-primary/30 text-muted-foreground">
        <Calendar className="w-4 h-4 text-primary" />
        <span className="text-sm">Date Range</span>
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
