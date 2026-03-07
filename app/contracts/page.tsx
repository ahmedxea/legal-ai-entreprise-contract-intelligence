"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
import { Search, Upload, FileText, Calendar, AlertTriangle, CheckCircle, Filter, Trash2, Loader2, Scale } from "lucide-react"
import { useState, useEffect } from "react"
import Link from "next/link"
import { apiClient, type Contract } from "@/lib/api-client"

function getUploadDate(contract: Contract) {
  return contract.uploaded_at ?? contract.upload_date ?? new Date().toISOString()
}

function getGoverningLaw(contract: Contract) {
  return contract.extracted_data?.governing_law || contract.analysis?.entities?.governing_law || contract.analysis?.extracted_data?.governing_law || "Unclassified"
}

export default function ContractsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [contracts, setContracts] = useState<Contract[]>([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [deleteTarget, setDeleteTarget] = useState<Contract | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    fetchContracts()
  }, [])

  const fetchContracts = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getContracts()
      setContracts(data)
    } catch (error) {
      console.error("Failed to fetch contracts:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      setDeleting(true)
      await apiClient.deleteContract(deleteTarget.id)
      setContracts((prev) => prev.filter((c) => c.id !== deleteTarget.id))
      setDeleteTarget(null)
    } catch (err: any) {
      console.error("Delete failed:", err)
    } finally {
      setDeleting(false)
    }
  }

  const filteredContracts = contracts.filter((contract) => {
    const matchesSearch = (contract.filename ?? "").toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = filterStatus === "all" || contract.status.toLowerCase() === filterStatus.toLowerCase()
    return matchesSearch && matchesFilter
  })

  const getStatusBadge = (status: string) => {
    const statusLower = status.toLowerCase()
    if (statusLower === "completed" || statusLower === "analyzed") {
      return <span className="badge-success">Analyzed</span>
    } else if (statusLower === "processing" || statusLower === "pending") {
      return <span className="badge-warning">Processing</span>
    } else {
      return <span className="badge-danger">Failed</span>
    }
  }

  const getRiskBadge = (riskScore?: number) => {
    if (!riskScore) return <span className="text-sm text-muted-foreground">N/A</span>
    if (riskScore < 3) return <span className="text-sm text-success flex items-center gap-1"><CheckCircle className="w-3 h-3" />Low</span>
    if (riskScore < 7) return <span className="text-sm text-warning flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Medium</span>
    return <span className="text-sm text-danger flex items-center gap-1"><AlertTriangle className="w-3 h-3" />High</span>
  }

  return (
    <div className="p-6 max-w-screen-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-3xl font-bold text-foreground">All Contracts</h1>
            <p className="text-muted-foreground mt-1">Review jurisdiction, processing status, and risk exposure across your contract portfolio</p>
          </div>
          <Link href="/home">
            <Button className="btn-enterprise">
              <Upload className="w-4 h-4 mr-2" />
              Upload Contract
            </Button>
          </Link>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="enterprise-card mb-6">
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search contracts by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 input-enterprise"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-enterprise w-40"
            >
              <option value="all">All Status</option>
              <option value="completed">Analyzed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading contracts...</p>
          </div>
        </div>
      )}

      {/* Contracts Table */}
      {!loading && filteredContracts.length > 0 && (
        <div className="enterprise-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Document</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Type</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Governing Law</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Upload Date</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Risk Level</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredContracts.map((contract) => (
                  <tr key={contract.id} className="border-b border-border hover:bg-muted/50 transition-colors">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <FileText className="w-5 h-5 text-primary" />
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-foreground truncate">{contract.filename}</p>
                          <p className="text-sm text-muted-foreground">{contract.filename.split('.').pop()?.toUpperCase() || 'FILE'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-sm text-foreground">{contract.industry || "General"}</span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
                        <Scale className="w-3 h-3" />
                        {getGoverningLaw(contract)}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="w-4 h-4" />
                        {new Date(getUploadDate(contract)).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      {getStatusBadge(contract.status)}
                    </td>
                    <td className="py-4 px-4">
                      {getRiskBadge(contract.analysis?.overall_risk_score)}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <Link href={`/contracts/detail?id=${contract.id}`}>
                          <Button variant="outline" size="sm" className="text-xs">
                            View Details
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={() => setDeleteTarget(contract)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredContracts.length === 0 && (
        <div className="enterprise-card text-center py-16">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">No contracts found</h3>
          <p className="text-muted-foreground mb-6">
            {searchQuery ? "Try adjusting your search terms" : "Upload your first contract to get started"}
          </p>
          <Link href="/home">
            <Button className="btn-enterprise">
              <Upload className="w-4 h-4 mr-2" />
              Upload Contract
            </Button>
          </Link>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete contract?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete <strong>{deleteTarget?.filename}</strong> and all its
              analysis data. This action cannot be undone.
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
