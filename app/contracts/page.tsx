"use client"

import { Navigation } from "@/components/navigation"
import { ContractCard } from "@/components/contract-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Upload } from "lucide-react"
import { useState } from "react"
import Link from "next/link"

export default function ContractsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [contracts, setContracts] = useState([
    {
      id: 1,
      name: "Service Agreement 2025.pdf",
      type: "Service Agreement",
      fileUrl: "https://example.com/contracts/service-agreement-2025.pdf",
      status: "Active",
      riskLevel: "Low" as const,
      value: "$250,000",
      duration: "12 months",
      parties: ["Acme Corp", "Tech Solutions Inc"],
      startDate: "2025-01-01",
      endDate: "2026-01-01",
    },
    {
      id: 2,
      name: "NDA - Tech Corp.docx",
      type: "Non-Disclosure Agreement",
      fileUrl: "https://example.com/contracts/nda-tech-corp.pdf",
      status: "Processing",
      riskLevel: "Medium" as const,
      value: "$0",
      duration: "24 months",
      parties: ["Your Company", "Tech Corp"],
      startDate: "2025-01-14",
      endDate: "2027-01-14",
    },
    {
      id: 3,
      name: "Employment Contract.pdf",
      type: "Employment Agreement",
      fileUrl: "https://example.com/contracts/employment-contract.pdf",
      status: "Completed",
      riskLevel: "Low" as const,
      value: "$120,000/year",
      duration: "Indefinite",
      parties: ["Your Company", "John Doe"],
      startDate: "2025-01-01",
      endDate: "Ongoing",
    },
    {
      id: 4,
      name: "Vendor Agreement.pdf",
      type: "Vendor Agreement",
      fileUrl: "https://example.com/contracts/vendor-agreement.pdf",
      status: "Under Review",
      riskLevel: "High" as const,
      value: "$500,000",
      duration: "36 months",
      parties: ["Your Company", "Global Vendors Inc"],
      startDate: "2025-02-01",
      endDate: "2028-02-01",
    },
  ])

  const handleRename = (contract: any, newName: string) => {
    console.log("[v0] Renaming contract:", contract.id, "to:", newName)
    setContracts((prev) => prev.map((c) => (c.id === contract.id ? { ...c, name: newName } : c)))
    // TODO: Add API call to update contract name on server
  }

  const handleDelete = (id: string | number) => {
    console.log("[v0] Deleting contract:", id)
    setContracts((prev) => prev.filter((c) => c.id !== id))
    // TODO: Add API call to delete contract from server
  }

  const filteredContracts = contracts.filter((contract) =>
    contract.name.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-3 text-balance">All Contracts</h1>
          <p className="text-lg text-muted-foreground">Manage and view all your contract documents</p>
        </div>

        {/* Search and Actions */}
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-8">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search contracts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Link href="/upload">
            <Button className="gradient-blue text-white hover:opacity-90 w-full sm:w-auto">
              <Upload className="w-4 h-4 mr-2" />
              Upload New Contract
            </Button>
          </Link>
        </div>

        {/* Contracts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredContracts.map((contract) => (
            <ContractCard key={contract.id} contract={contract} onRename={handleRename} onDelete={handleDelete} />
          ))}
        </div>

        {filteredContracts.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No contracts found matching your search.</p>
          </div>
        )}
      </main>
    </div>
  )
}
