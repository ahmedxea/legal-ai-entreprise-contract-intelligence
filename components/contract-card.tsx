"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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
import { FileText, Calendar, Users, DollarSign, MoreVertical, ExternalLink } from "lucide-react"
import { useState } from "react"

interface Contract {
  id: string | number
  name: string
  fileUrl: string
  status: string
  riskLevel: "Low" | "Medium" | "High"
  value: string
  duration: string
  parties: string[]
  startDate: string
  endDate: string
  type?: string
}

interface ContractCardProps {
  contract: Contract
  onRename: (contract: Contract, newName: string) => void
  onDelete: (id: string | number) => void
}

export function ContractCard({ contract, onRename, onDelete }: ContractCardProps) {
  const [showRenameDialog, setShowRenameDialog] = useState(false)
  const [newName, setNewName] = useState(contract.name)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const handleRename = () => {
    if (newName.trim() && newName !== contract.name) {
      onRename(contract, newName.trim())
      setShowRenameDialog(false)
    }
  }

  const handleDelete = () => {
    onDelete(contract.id)
    setShowDeleteDialog(false)
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case "Low":
        return "bg-success/10 text-success border-success/20"
      case "Medium":
        return "bg-warning/10 text-warning border-warning/20"
      case "High":
        return "bg-destructive/10 text-destructive border-destructive/20"
      default:
        return "bg-secondary/10 text-secondary-foreground border-secondary/20"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Active":
      case "Completed":
        return "bg-success/10 text-success border-success/20"
      case "Processing":
      case "Under Review":
        return "bg-primary/10 text-primary border-primary/20"
      case "Expiring Soon":
        return "bg-warning/10 text-warning border-warning/20"
      default:
        return "bg-secondary/10 text-secondary-foreground border-secondary/20"
    }
  }

  return (
    <>
      <div className="group relative rounded-3xl bg-card/60 backdrop-blur-xl border border-border/50 p-6 transition-all duration-300 hover:shadow-[0_0_30px_rgba(0,198,255,0.15)] hover:border-primary/30 hover:-translate-y-1">
        {/* Header with Title and Menu */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="w-10 h-10 rounded-xl gradient-blue flex items-center justify-center flex-shrink-0">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg mb-1 truncate">{contract.name}</h3>
              {contract.type && <p className="text-sm text-muted-foreground">{contract.type}</p>}
            </div>
          </div>

          {/* Three-dot menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="p-2 rounded-full hover:bg-secondary/80 transition-colors">
                <MoreVertical size={18} className="text-foreground" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="bg-card/95 backdrop-blur-xl text-foreground rounded-xl border border-primary/20 shadow-lg"
            >
              <DropdownMenuItem
                onClick={() => {
                  setNewName(contract.name)
                  setShowRenameDialog(true)
                }}
                className="cursor-pointer"
              >
                Rename Document
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => setShowDeleteDialog(true)}
                className="cursor-pointer text-destructive focus:text-destructive"
              >
                Delete Document
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Status and Risk Badges */}
        <div className="flex items-center gap-2 mb-4">
          <Badge className={`${getStatusColor(contract.status)} border`}>{contract.status}</Badge>
          <Badge className={`${getRiskColor(contract.riskLevel)} border`}>{contract.riskLevel} Risk</Badge>
        </div>

        {/* Contract Details Grid */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex items-start gap-2">
            <DollarSign className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-muted-foreground">Value</p>
              <p className="text-sm font-medium">{contract.value}</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Calendar className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-muted-foreground">Duration</p>
              <p className="text-sm font-medium">{contract.duration}</p>
            </div>
          </div>
        </div>

        {/* Parties */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-primary" />
            <p className="text-xs text-muted-foreground">Parties</p>
          </div>
          <div className="space-y-1">
            {contract.parties.map((party, index) => (
              <p key={index} className="text-sm pl-6">
                {party}
              </p>
            ))}
          </div>
        </div>

        {/* Key Dates */}
        <div className="mb-6 p-3 rounded-xl bg-secondary/30">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Start Date</p>
              <p className="font-medium">{contract.startDate}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">End Date</p>
              <p className="font-medium">{contract.endDate}</p>
            </div>
          </div>
        </div>

        {/* View PDF Button */}
        <Button
          onClick={() => window.open(contract.fileUrl, "_blank")}
          className="w-full rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white hover:opacity-90 transition-all duration-300 hover:shadow-[0_0_20px_rgba(0,198,255,0.4)]"
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          View PDF
        </Button>
      </div>

      <Dialog open={showRenameDialog} onOpenChange={setShowRenameDialog}>
        <DialogContent className="bg-card/95 backdrop-blur-xl border border-border/50 rounded-3xl">
          <DialogHeader>
            <DialogTitle>Rename Contract</DialogTitle>
            <DialogDescription>Enter a new name for this contract document.</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="contract-name" className="text-sm font-medium mb-2 block">
              Contract Name
            </Label>
            <Input
              id="contract-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter contract name"
              className="rounded-xl"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleRename()
                }
              }}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRenameDialog(false)} className="rounded-xl">
              Cancel
            </Button>
            <Button
              onClick={handleRename}
              disabled={!newName.trim() || newName === contract.name}
              className="rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white hover:opacity-90"
            >
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="bg-card/95 backdrop-blur-xl border border-border/50 rounded-3xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Contract</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{contract.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="rounded-xl bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
