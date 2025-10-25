"use client"

import type React from "react"

import { Navigation } from "@/components/navigation"
import { ProtectedRoute } from "@/components/protected-route"
import { Button } from "@/components/ui/button"
import { Upload, FileText, CheckCircle2, AlertCircle } from "lucide-react"
import { useState } from "react"
import { motion } from "framer-motion"

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<
    Array<{ name: string; size: string; status: "uploading" | "analyzing" | "complete" | "error" }>
  >([])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    processFiles(files)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      processFiles(files)
    }
  }

  const processFiles = (files: File[]) => {
    files.forEach((file) => {
      const sizeInMB = (file.size / (1024 * 1024)).toFixed(2)
      const newFile = {
        name: file.name,
        size: `${sizeInMB} MB`,
        status: "uploading" as const,
      }

      setUploadedFiles((prev) => [...prev, newFile])

      setTimeout(() => {
        setUploadedFiles((prev) => prev.map((f) => (f.name === file.name ? { ...f, status: "analyzing" as const } : f)))
      }, 1500)

      setTimeout(() => {
        setUploadedFiles((prev) => prev.map((f) => (f.name === file.name ? { ...f, status: "complete" as const } : f)))
      }, 3500)
    })
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-b from-white to-[#F9FAFB]">
        <Navigation />

        <main className="pt-32 pb-16 px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-4xl mx-auto text-center"
          >
            <h1 className="text-5xl font-bold text-[#111827] mb-4 leading-tight">Upload Your Contract</h1>
            <p className="text-lg text-[#6B7280] mb-12">
              Upload your PDF or DOCX files and let AI analyze them intelligently in seconds.
            </p>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-3xl p-12 transition-all ${
                  isDragging
                    ? "border-[#007AFF] bg-[#007AFF]/5 scale-[1.02]"
                    : "border-[#E5E7EB] bg-white/70 hover:bg-white shadow-[0_0_30px_rgba(0,0,0,0.05)]"
                }`}
              >
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center shadow-[0_0_20px_rgba(0,122,255,0.3)]">
                    <Upload className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <input
                      type="file"
                      id="file-upload"
                      className="hidden"
                      multiple
                      accept=".pdf,.doc,.docx,.txt"
                      onChange={handleFileInput}
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <p className="text-lg text-[#111827] font-medium">
                        Drag & Drop your file here or{" "}
                        <span className="text-[#007AFF] underline hover:text-[#00C6FF] transition-colors">browse</span>
                      </p>
                    </label>
                    <p className="text-sm text-[#6B7280] mt-3">Supported formats: PDF, DOCX</p>
                  </div>
                </div>
              </div>
            </motion.div>

            {uploadedFiles.length > 0 && uploadedFiles.some((f) => f.status === "complete") && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                <Button className="mt-10 bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white rounded-xl px-8 py-6 text-lg hover:opacity-90 shadow-[0_0_20px_rgba(0,198,255,0.4)] transition-all hover:shadow-[0_0_30px_rgba(0,198,255,0.6)]">
                  Analyze Contract →
                </Button>
              </motion.div>
            )}
          </motion.div>

          {uploadedFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="max-w-4xl mx-auto mt-12"
            >
              <div className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] p-8">
                <h2 className="text-2xl font-bold text-[#111827] mb-6">Processing Files</h2>
                <div className="space-y-4">
                  {uploadedFiles.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 rounded-2xl bg-[#F9FAFB] hover:bg-[#F3F4F6] transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center">
                          <FileText className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-[#111827]">{file.name}</p>
                          <p className="text-sm text-[#6B7280]">{file.size}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {file.status === "uploading" && (
                          <div className="flex items-center gap-2 text-[#007AFF]">
                            <div className="w-4 h-4 border-2 border-[#007AFF] border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm font-medium">Uploading...</span>
                          </div>
                        )}
                        {file.status === "analyzing" && (
                          <div className="flex items-center gap-2 text-[#00C6FF]">
                            <div className="w-4 h-4 border-2 border-[#00C6FF] border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm font-medium">Analyzing...</span>
                          </div>
                        )}
                        {file.status === "complete" && (
                          <div className="flex items-center gap-2 text-[#10B981]">
                            <CheckCircle2 className="w-5 h-5" />
                            <span className="text-sm font-medium">Complete</span>
                          </div>
                        )}
                        {file.status === "error" && (
                          <div className="flex items-center gap-2 text-[#EF4444]">
                            <AlertCircle className="w-5 h-5" />
                            <span className="text-sm font-medium">Error</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 max-w-6xl mx-auto"
          >
            <div className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center mb-4 shadow-[0_0_15px_rgba(0,122,255,0.3)]">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[#111827] mb-2">Smart Extraction</h3>
              <p className="text-sm text-[#6B7280]">
                Automatically extract key terms, dates, parties, and obligations from your contracts
              </p>
            </div>

            <div className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center mb-4 shadow-[0_0_15px_rgba(0,122,255,0.3)]">
                <AlertCircle className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[#111827] mb-2">Risk Detection</h3>
              <p className="text-sm text-[#6B7280]">
                Identify potential risks, unfavorable terms, and compliance issues in real-time
              </p>
            </div>

            <div className="bg-white rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)] transition-all p-6">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] flex items-center justify-center mb-4 shadow-[0_0_15px_rgba(0,122,255,0.3)]">
                <CheckCircle2 className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[#111827] mb-2">Compliance Check</h3>
              <p className="text-sm text-[#6B7280]">
                Ensure your contracts meet regulatory requirements and industry standards
              </p>
            </div>
          </motion.div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
