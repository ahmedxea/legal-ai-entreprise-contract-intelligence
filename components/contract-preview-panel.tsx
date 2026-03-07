"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { apiClient, type Risk } from "@/lib/api-client"
import { AlertTriangle, FileText, Loader2, MapPin, Minus, File as FileIcon } from "lucide-react"

// ── Severity styling maps ───────────────────────────────────────────────────

const HIGHLIGHT_CLASS: Record<string, string> = {
  critical:
    "bg-red-200 dark:bg-red-900/70 border-b-2 border-red-500 cursor-pointer hover:bg-red-300 dark:hover:bg-red-800",
  high: "bg-orange-200 dark:bg-orange-900/60 border-b-2 border-orange-500 cursor-pointer hover:bg-orange-300 dark:hover:bg-orange-800",
  medium:
    "bg-yellow-100 dark:bg-yellow-900/50 border-b-2 border-yellow-400 cursor-pointer hover:bg-yellow-200 dark:hover:bg-yellow-800",
  low: "bg-blue-100 dark:bg-blue-900/50 border-b-2 border-blue-400 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-800",
}

const LABEL_CLASS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  high: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300",
  low: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
}

const SIDEBAR_CLASS: Record<string, string> = {
  critical: "border-l-4 border-l-red-500 bg-red-50 dark:bg-red-950/30",
  high: "border-l-4 border-l-orange-500 bg-orange-50 dark:bg-orange-950/30",
  medium: "border-l-4 border-l-yellow-400 bg-yellow-50 dark:bg-yellow-950/20",
  low: "border-l-4 border-l-blue-400 bg-blue-50 dark:bg-blue-950/30",
}

// ── Text segmentation ──────────────────────────────────────────────────────

interface Span {
  start: number
  end: number
  riskIndex: number
}

interface Segment {
  text: string
  riskIndex: number | null
  severity?: string
}

function buildSegments(rawText: string, risks: Risk[]): { segments: Segment[]; mapped: Set<number> } {
  const spans: Span[] = []

  for (let i = 0; i < risks.length; i++) {
    const src = risks[i].source_text?.trim()
    if (!src || src.length < 5) continue

    // Prefer exact match, fall back to case-insensitive
    let idx = rawText.indexOf(src)
    if (idx === -1) idx = rawText.toLowerCase().indexOf(src.toLowerCase())
    if (idx !== -1) {
      spans.push({ start: idx, end: idx + src.length, riskIndex: i })
    }
  }

  spans.sort((a, b) => a.start - b.start)

  // Remove overlaps — keep the earlier one
  const filtered: Span[] = []
  let lastEnd = 0
  for (const span of spans) {
    if (span.start >= lastEnd) {
      filtered.push(span)
      lastEnd = span.end
    }
  }

  const mapped = new Set(filtered.map((s) => s.riskIndex))

  const segments: Segment[] = []
  let pos = 0
  for (const span of filtered) {
    if (span.start > pos) segments.push({ text: rawText.slice(pos, span.start), riskIndex: null })
    segments.push({
      text: rawText.slice(span.start, span.end),
      riskIndex: span.riskIndex,
      severity: risks[span.riskIndex].severity,
    })
    pos = span.end
  }
  if (pos < rawText.length) segments.push({ text: rawText.slice(pos), riskIndex: null })

  return { segments, mapped }
}

// ── Main component ──────────────────────────────────────────────────────────

interface Props {
  contractId: string
  filename: string
  risks: Risk[]
}

export function ContractPreviewPanel({ contractId, filename, risks }: Props) {
  const [rawText, setRawText] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeRisk, setActiveRisk] = useState<number | null>(null)
  const [subTab, setSubTab] = useState<"text" | "file">("text")

  const fileUrl = apiClient.getContractFileUrl(contractId)
  const isDocx = filename.toLowerCase().endsWith(".docx")
  const isPdf = filename.toLowerCase().endsWith(".pdf")
  const isLocalhost = fileUrl.includes("localhost") || fileUrl.includes("127.0.0.1")
  
  // Google Docs viewer only works with publicly accessible URLs
  const docxViewerUrl = isLocalhost
    ? null  // Can't use Google Docs Viewer for localhost
    : `https://docs.google.com/viewerng/viewer?url=${encodeURIComponent(fileUrl)}&embedded=true`

  useEffect(() => {
    let cancelled = false
    // Only fetch the text when on the text sub-tab
    if (subTab !== "text") return

    setLoading(true)
    setError(null)

    apiClient
      .getContractText(contractId)
      .then((data) => {
        if (!cancelled) setRawText(data.raw_text)
      })
      .catch((e: any) => {
        if (!cancelled) setError(e.message ?? "Failed to load contract text")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [contractId, subTab])

  const scrollToRisk = useCallback((riskIndex: number) => {
    setActiveRisk(riskIndex)
    const el = document.getElementById(`rh-${riskIndex}`)
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" })
  }, [])

  // ── Loading / error states ──────────────────────────────────────────────

  const showTextLoading = subTab === "text" && loading
  const showTextError = subTab === "text" && !!error && !rawText

  const { segments, mapped } = rawText
    ? buildSegments(rawText, risks)
    : { segments: [], mapped: new Set<number>() }
  const unmappedCount = risks.filter((_, i) => !mapped.has(i)).length

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-4">
      {/* Sub-tabs */}
      <div className="flex items-center gap-1 border-b">
        <button
          onClick={() => setSubTab("text")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            subTab === "text"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileText className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
          Contract Text
        </button>
        <button
          onClick={() => setSubTab("file")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            subTab === "file"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileIcon className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
          Raw File <span className="ml-1 text-[10px] text-muted-foreground uppercase">{filename.split(".").pop()}</span>
        </button>
      </div>

      {/* ── Raw file viewer tab ─────────────────────────────────────────── */}
      {subTab === "file" && (
        <div className="rounded-lg border overflow-hidden bg-muted/20" style={{ height: 700 }}>
          {isPdf ? (
            /* PDF — stream directly from backend */
            <iframe
              src={fileUrl}
              title="Contract PDF"
              className="w-full h-full border-0 bg-white"
            />
          ) : isDocx && docxViewerUrl ? (
            /* DOCX via Google Docs Viewer (production only) */
            <iframe
              src={docxViewerUrl}
              title="Contract document"
              className="w-full h-full border-0 bg-white"
              sandbox="allow-scripts allow-same-origin allow-popups"
            />
          ) : isDocx && isLocalhost ? (
            /* DOCX on localhost — Google Docs Viewer doesn't work */
            <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
              <FileIcon className="w-16 h-16 text-muted-foreground" />
              <div className="text-center space-y-2 max-w-md">
                <p className="text-sm font-medium">DOCX Preview Not Available in Development</p>
                <p className="text-xs text-muted-foreground">
                  Google Docs Viewer requires a publicly accessible URL. This feature works in production on Azure.
                </p>
                <a
                  href={fileUrl}
                  download={filename}
                  className="inline-flex items-center gap-2 mt-4 px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <FileIcon className="w-4 h-4" />
                  Download {filename}
                </a>
              </div>
            </div>
          ) : (
            /* Unsupported file type */
            <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
              <AlertTriangle className="w-12 h-12 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Preview not available for this file type</p>
            </div>
          )}
        </div>
      )}

      {/* ── Contract text + risk highlights tab ────────────────────────── */}
      {subTab === "text" && (
        <>
          {showTextLoading && (
            <div className="flex items-center gap-3 text-muted-foreground p-12 justify-center">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Loading contract text…</span>
            </div>
          )}

          {showTextError && (
            <div className="p-10 text-center">
              <AlertTriangle className="w-8 h-8 mx-auto mb-3 text-destructive" />
              <p className="text-sm text-destructive font-medium">{error}</p>
              <p className="text-xs text-muted-foreground mt-2 max-w-sm mx-auto">
                Text extraction may still be in progress. Wait until status is "analyzed" then try again.
              </p>
            </div>
          )}

          {!showTextLoading && !showTextError && rawText && (
            <>
          {/* Legend */}
          <div className="flex flex-wrap items-center gap-3 pb-2 border-b">
            <span className="text-xs font-medium text-muted-foreground">Legend:</span>
            {(["critical", "high", "medium", "low"] as const).map((sev) => (
              <span key={sev} className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${LABEL_CLASS[sev]}`}>
                {sev.charAt(0).toUpperCase() + sev.slice(1)}
              </span>
            ))}
            {unmappedCount > 0 && (
              <span className="text-[11px] text-muted-foreground ml-auto">
                {unmappedCount} risk{unmappedCount > 1 ? "s" : ""} without position
              </span>
            )}
          </div>

          <div className="flex flex-col lg:flex-row gap-4" style={{ minHeight: 560 }}>
            {/* ── Contract text panel ─────────────────────────────────────── */}
            <div className="flex-1 flex flex-col min-w-0">
              <div className="flex items-center gap-2 px-4 py-2.5 bg-muted/30 border rounded-t-lg">
                <FileText className="w-4 h-4 text-primary" />
                <span className="text-sm font-semibold">Contract Text</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {mapped.size}/{risks.length} risks highlighted
                </span>
              </div>
              <div className="flex-1 overflow-y-auto border border-t-0 rounded-b-lg bg-background p-4 scroll-smooth" style={{ maxHeight: 600 }}>
                <p className="whitespace-pre-wrap text-sm leading-7 font-mono break-words">
                  {segments.map((seg, idx) => {
                    if (seg.riskIndex === null) return <span key={idx}>{seg.text}</span>

                    const sev = (seg.severity ?? "low").toLowerCase()
                    const cls = HIGHLIGHT_CLASS[sev] ?? HIGHLIGHT_CLASS.low
                    const isActive = activeRisk === seg.riskIndex

                    return (
                      <span
                        key={idx}
                        id={`rh-${seg.riskIndex}`}
                        title={risks[seg.riskIndex!].description}
                        onClick={() => setActiveRisk(seg.riskIndex!)}
                        className={`inline rounded-sm px-0.5 transition-all duration-200 ${cls} ${
                          isActive ? "ring-2 ring-offset-1 ring-primary" : ""
                        }`}
                      >
                        {seg.text}
                      </span>
                    )
                  })}
                </p>
              </div>
            </div>

            {/* ── Risk sidebar ────────────────────────────────────────────── */}
            <div className="w-full lg:w-72 flex-shrink-0 flex flex-col">
              <div className="flex items-center gap-2 px-4 py-2.5 bg-muted/30 border rounded-t-lg">
                <AlertTriangle className="w-4 h-4 text-destructive" />
                <span className="text-sm font-semibold">Flagged Risks</span>
                <span className="ml-auto text-xs font-medium text-muted-foreground">{risks.length}</span>
              </div>
              <div className="flex-1 overflow-y-auto border border-t-0 rounded-b-lg divide-y" style={{ maxHeight: 600 }}>
                {risks.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-10">No risks detected</p>
                )}
                {risks.map((risk, i) => {
                  const hasMapped = mapped.has(i)
                  const sev = (risk.severity ?? "low").toLowerCase()
                  const cls = SIDEBAR_CLASS[sev] ?? SIDEBAR_CLASS.low
                  const isActive = activeRisk === i

                  return (
                    <div
                      key={i}
                      onClick={() => hasMapped && scrollToRisk(i)}
                      className={`px-3 py-3 ${cls} ${hasMapped ? "cursor-pointer hover:opacity-80" : "opacity-60"} ${
                        isActive ? "ring-2 ring-inset ring-primary" : ""
                      } transition-all`}
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full capitalize ${LABEL_CLASS[sev] ?? LABEL_CLASS.low}`}>
                          {risk.severity}
                        </span>
                        {hasMapped ? (
                          <span className="ml-auto text-[10px] text-primary flex items-center gap-0.5 font-medium">
                            <MapPin className="w-3 h-3" /> jump to
                          </span>
                        ) : (
                          <span className="ml-auto text-[10px] text-muted-foreground flex items-center gap-0.5">
                            <Minus className="w-3 h-3" /> no position
                          </span>
                        )}
                      </div>
                      <p className="text-xs leading-snug line-clamp-3">{risk.description}</p>
                      {risk.recommendation && (
                        <p className="text-[10px] text-muted-foreground mt-1.5 leading-snug line-clamp-2 italic">
                          {risk.recommendation}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </>
          )}
        </>
      )}
    </div>
  )
}
