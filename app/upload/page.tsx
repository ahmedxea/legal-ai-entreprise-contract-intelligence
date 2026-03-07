"use client"

import type React from "react"
import { useCallback, useRef, useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { config } from "@/lib/config"
import { apiClient } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
  ShieldCheck,
  ScanSearch,
  Scale,
  Sparkles,
  Eye,
} from "lucide-react"

const MAX_FILE_SIZE_MB = 50
const ALLOWED_EXTENSIONS = [".pdf", ".docx"]

type FileStatus = "pending" | "uploading" | "extracting" | "analyzing" | "analyzed" | "error"

interface UploadedFile {
  id: string
  file: File
  name: string
  size: string
  status: FileStatus
  contractId?: string
  errorMessage?: string
}

export default function UploadPage() {
  const { token } = useAuth()
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  /* ── Helpers ── */

  const humanSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const validateFile = (file: File): string | null => {
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type "${ext}". Only PDF and DOCX files are accepted.`
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return `File is too large (${humanSize(file.size)}). Maximum size is ${MAX_FILE_SIZE_MB} MB.`
    }
    if (file.size === 0) {
      return "File is empty."
    }
    return null
  }

  /* ── Upload a single file ── */

  const uploadFile = useCallback(
    async (entry: UploadedFile) => {
      setFiles((prev) =>
        prev.map((f) => (f.id === entry.id ? { ...f, status: "uploading" as FileStatus } : f))
      )

      try {
        const formData = new FormData()
        formData.append("file", entry.file)

        const params = new URLSearchParams({ language: "en" })

        const res = await fetch(`${config.apiUrl}/api/contracts/upload?${params}`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        })

        if (!res.ok) {
          const body = await res.json().catch(() => ({ detail: "Upload failed" }))
          // FastAPI validation errors return detail as an array of objects
          const detail = body.detail
          const message =
            typeof detail === "string"
              ? detail
              : Array.isArray(detail)
              ? detail.map((d: any) => d.msg ?? JSON.stringify(d)).join("; ")
              : `Upload failed (${res.status})`
          throw new Error(message)
        }

        const data = await res.json()
        const contractId: string = data.contract_id

        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id
              ? { ...f, status: "extracting" as FileStatus, contractId }
              : f
          )
        )

        // Phase 1 → wait for text extraction to complete
        await apiClient.pollContractStatus(contractId, ["extracted", "analyzed"])

        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id ? { ...f, status: "analyzing" as FileStatus } : f
          )
        )

        // Phase 2 → trigger AI analysis
        await apiClient.analyzeContract(contractId)

        // Poll until analysis is done (up to ~5 min for large contracts)
        await apiClient.pollContractStatus(contractId, ["analyzed"], 4000, 75)

        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id ? { ...f, status: "analyzed" as FileStatus } : f
          )
        )
      } catch (err: any) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id
              ? { ...f, status: "error" as FileStatus, errorMessage: err.message }
              : f
          )
        )
      }
    },
    [token]
  )

  /* ── Add files (from input or drag) ── */

  const addFiles = useCallback(
    (incoming: File[]) => {
      const newEntries: UploadedFile[] = incoming.map((file) => {
        const validationError = validateFile(file)
        return {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          file,
          name: file.name,
          size: humanSize(file.size),
          status: validationError ? ("error" as FileStatus) : ("pending" as FileStatus),
          errorMessage: validationError ?? undefined,
        }
      })

      setFiles((prev) => [...prev, ...newEntries])

      // Auto-upload valid files
      newEntries
        .filter((e) => e.status === "pending")
        .forEach((e) => uploadFile(e))
    },
    [uploadFile]
  )

  /* ── Drag & drop handlers ── */

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }
  const onDragLeave = () => setIsDragging(false)
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    addFiles(Array.from(e.dataTransfer.files))
  }

  /* ── File input handler ── */

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files))
      e.target.value = "" // allow re-selecting same file
    }
  }

  /* ── Remove file from list ── */

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  /* ── Status badge renderer ── */

  const StatusBadge = ({ file }: { file: UploadedFile }) => {
    switch (file.status) {
      case "pending":
        return (
          <span className="text-xs text-muted-foreground font-medium">Queued</span>
        )
      case "uploading":
        return (
          <span className="flex items-center gap-1.5 text-primary text-xs font-medium">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Uploading…
          </span>
        )
      case "extracting":
        return (
          <span className="flex items-center gap-1.5 text-blue-500 text-xs font-medium">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Extracting…
          </span>
        )
      case "analyzing":
        return (
          <span className="flex items-center gap-1.5 text-violet-500 text-xs font-medium">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Analysing…
          </span>
        )
      case "analyzed":
        return (
          <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
            <Sparkles className="h-3.5 w-3.5" />
            Analysed
          </span>
        )
      case "error":
        return (
          <span className="flex items-center gap-1.5 text-destructive text-xs font-medium">
            <AlertCircle className="h-3.5 w-3.5" />
            Failed
          </span>
        )
    }
  }

  /* ── Render ── */

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Upload Contracts</h1>
        <p className="text-muted-foreground mt-1">
          Upload PDF or DOCX files for AI-powered contract analysis.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`relative rounded-xl border-2 border-dashed p-10 text-center transition-all duration-200 ${
          isDragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-border bg-card hover:border-primary/40 hover:bg-accent/30"
        }`}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
            <Upload className="h-6 w-6 text-primary" />
          </div>

          <div>
            <p className="text-base font-medium">
              Drag & drop files here, or{" "}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-primary underline underline-offset-2 hover:text-primary/80 transition-colors"
              >
                browse
              </button>
            </p>
            <p className="text-sm text-muted-foreground mt-1.5">
              Accepted: <strong>PDF, DOCX</strong> &middot; Max size: <strong>{MAX_FILE_SIZE_MB} MB</strong>
            </p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            multiple
            accept=".pdf,.docx"
            onChange={onFileInput}
          />
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="rounded-xl border bg-card">
          <div className="flex items-center justify-between border-b px-5 py-3">
            <h2 className="text-sm font-semibold">
              Uploads ({files.filter((f) => f.status === "analyzed").length}/{files.length})
            </h2>
            {files.length > 0 && (
              <button
                onClick={() => setFiles([])}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear all
              </button>
            )}
          </div>

          <div className="divide-y">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-4 px-5 py-3 hover:bg-accent/30 transition-colors"
              >
                {/* Icon */}
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <FileText className="h-4 w-4 text-primary" />
                </div>

                {/* Name + size */}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {file.size}
                    {file.contractId && (
                      <span className="ml-2 text-emerald-600 dark:text-emerald-400">
                        ID: {file.contractId.slice(0, 8)}…
                      </span>
                    )}
                    {file.errorMessage && (
                      <span className="ml-2 text-destructive">{file.errorMessage}</span>
                    )}
                  </p>
                </div>

                {/* Status */}
                <StatusBadge file={file} />

                {/* View Preview shortcut after analysis */}
                {file.status === "analyzed" && file.contractId && (
                  <Link href={`/contracts/detail?id=${file.contractId}`}>
                    <Button variant="outline" size="sm" className="text-xs gap-1.5 shrink-0">
                      <Eye className="h-3.5 w-3.5" />
                      View
                    </Button>
                  </Link>
                )}

                {/* Remove */}
                <button
                  onClick={() => removeFile(file.id)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  title="Remove"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          {
            icon: ScanSearch,
            title: "Smart Extraction",
            desc: "Automatically extract key terms, dates, parties, and obligations from your contracts.",
          },
          {
            icon: ShieldCheck,
            title: "Risk Detection",
            desc: "Identify potential risks, unfavorable terms, and compliance issues in real-time.",
          },
          {
            icon: Scale,
            title: "Compliance Check",
            desc: "Ensure your contracts meet regulatory requirements and industry standards.",
          },
        ].map((card) => (
          <div
            key={card.title}
            className="rounded-xl border bg-card p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 mb-3">
              <card.icon className="h-5 w-5 text-primary" />
            </div>
            <h3 className="text-sm font-semibold mb-1">{card.title}</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
