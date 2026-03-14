"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"
import { apiClient } from "@/lib/api-client"
import { config } from "@/lib/config"
import {
  User,
  Lock,
  Building2,
  Mail,
  Shield,
  Server,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Save,
  Eye,
  EyeOff,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export default function SettingsPage() {
  const { user } = useAuth()

  // Profile form
  const [fullName, setFullName] = useState("")
  const [organization, setOrganization] = useState("")
  const [profileSaving, setProfileSaving] = useState(false)
  const [profileMsg, setProfileMsg] = useState<{ type: "success" | "error"; text: string } | null>(null)

  // Password form
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showCurrentPw, setShowCurrentPw] = useState(false)
  const [showNewPw, setShowNewPw] = useState(false)
  const [pwSaving, setPwSaving] = useState(false)
  const [pwMsg, setPwMsg] = useState<{ type: "success" | "error"; text: string } | null>(null)

  // System status
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking")
  const [ollamaStatus, setOllamaStatus] = useState<"checking" | "online" | "offline">("checking")

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || user.name || "")
      setOrganization(user.organization || "")
    }
  }, [user])

  useEffect(() => {
    checkBackendHealth()
    checkOllamaHealth()
  }, [])

  async function checkBackendHealth() {
    try {
      await apiClient.healthCheck()
      setBackendStatus("online")
    } catch {
      setBackendStatus("offline")
    }
  }

  async function checkOllamaHealth() {
    try {
      const res = await fetch(`${config.apiUrl}/health`)
      const data = await res.json()
      setOllamaStatus(data.ollama === "connected" ? "online" : "offline")
    } catch {
      setOllamaStatus("offline")
    }
  }

  async function handleProfileSave() {
    setProfileSaving(true)
    setProfileMsg(null)
    try {
      const result = await apiClient.updateProfile({
        full_name: fullName,
        organization,
      })
      setProfileMsg({ type: "success", text: result.message || "Profile updated" })
      // Update local storage so sidebar reflects changes
      const savedUser = localStorage.getItem("lexra_user")
      if (savedUser) {
        const parsed = JSON.parse(savedUser)
        parsed.name = fullName
        parsed.full_name = fullName
        parsed.organization = organization
        localStorage.setItem("lexra_user", JSON.stringify(parsed))
      }
    } catch (err: any) {
      setProfileMsg({ type: "error", text: err.message || "Failed to update profile" })
    } finally {
      setProfileSaving(false)
    }
  }

  async function handlePasswordChange() {
    if (newPassword !== confirmPassword) {
      setPwMsg({ type: "error", text: "New passwords do not match" })
      return
    }
    if (newPassword.length < 6) {
      setPwMsg({ type: "error", text: "Password must be at least 6 characters" })
      return
    }
    setPwSaving(true)
    setPwMsg(null)
    try {
      const result = await apiClient.changePassword(currentPassword, newPassword)
      setPwMsg({ type: "success", text: result.message || "Password changed" })
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
    } catch (err: any) {
      setPwMsg({ type: "error", text: err.message || "Failed to change password" })
    } finally {
      setPwSaving(false)
    }
  }

  const StatusDot = ({ status }: { status: "checking" | "online" | "offline" }) => (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full ${
        status === "online"
          ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"
          : status === "offline"
          ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"
          : "bg-yellow-500 animate-pulse"
      }`}
    />
  )

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account and application preferences</p>
      </div>

      {/* Profile Section */}
      <div className="enterprise-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/10 to-secondary/10">
            <User className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Profile</h2>
            <p className="text-sm text-muted-foreground">Update your personal information</p>
          </div>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          {/* Email (read-only) */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Mail className="w-4 h-4 text-muted-foreground" /> Email
            </label>
            <input
              type="email"
              value={user?.email || ""}
              disabled
              className="w-full rounded-lg border border-border bg-muted/50 px-3 py-2.5 text-sm text-muted-foreground cursor-not-allowed"
            />
          </div>

          {/* Role (read-only) */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Shield className="w-4 h-4 text-muted-foreground" /> Role
            </label>
            <div className="flex items-center h-[42px]">
              <Badge className="bg-primary/10 text-primary border-primary/20 capitalize">
                {user?.role || "user"}
              </Badge>
            </div>
          </div>

          {/* Full Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <User className="w-4 h-4 text-muted-foreground" /> Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your full name"
              className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 transition-shadow"
            />
          </div>

          {/* Organization */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Building2 className="w-4 h-4 text-muted-foreground" /> Organization
            </label>
            <input
              type="text"
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
              placeholder="Company or organization"
              className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 transition-shadow"
            />
          </div>
        </div>

        {profileMsg && (
          <div className={`mt-4 flex items-center gap-2 text-sm ${profileMsg.type === "success" ? "text-emerald-600" : "text-destructive"}`}>
            {profileMsg.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {profileMsg.text}
          </div>
        )}

        <div className="mt-5 flex justify-end">
          <Button onClick={handleProfileSave} disabled={profileSaving} className="gap-2">
            {profileSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Profile
          </Button>
        </div>
      </div>

      {/* Password Section */}
      <div className="enterprise-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-orange-500/10 to-red-500/10">
            <Lock className="w-5 h-5 text-orange-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Change Password</h2>
            <p className="text-sm text-muted-foreground">Update your account password</p>
          </div>
        </div>

        <div className="grid gap-5 max-w-md">
          {/* Current Password */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Current Password</label>
            <div className="relative">
              <input
                type={showCurrentPw ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                className="w-full rounded-lg border border-border bg-background px-3 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 transition-shadow"
              />
              <button
                type="button"
                onClick={() => setShowCurrentPw(!showCurrentPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* New Password */}
          <div className="space-y-2">
            <label className="text-sm font-medium">New Password</label>
            <div className="relative">
              <input
                type={showNewPw ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 6 characters"
                className="w-full rounded-lg border border-border bg-background px-3 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 transition-shadow"
              />
              <button
                type="button"
                onClick={() => setShowNewPw(!showNewPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter new password"
              className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 transition-shadow"
            />
          </div>
        </div>

        {pwMsg && (
          <div className={`mt-4 flex items-center gap-2 text-sm ${pwMsg.type === "success" ? "text-emerald-600" : "text-destructive"}`}>
            {pwMsg.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {pwMsg.text}
          </div>
        )}

        <div className="mt-5 flex justify-end">
          <Button
            onClick={handlePasswordChange}
            disabled={pwSaving || !currentPassword || !newPassword || !confirmPassword}
            variant="outline"
            className="gap-2"
          >
            {pwSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
            Change Password
          </Button>
        </div>
      </div>

      {/* System Status Section */}
      <div className="enterprise-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/10 to-cyan-500/10">
            <Server className="w-5 h-5 text-emerald-500" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">System Status</h2>
            <p className="text-sm text-muted-foreground">Backend services and platform information</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div className="flex items-center gap-3">
              <Server className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Backend API</p>
                <p className="text-xs text-muted-foreground truncate max-w-[180px]">{config.apiUrl}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot status={backendStatus} />
              <span className="text-xs font-medium capitalize">{backendStatus}</span>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-border p-4">
            <div className="flex items-center gap-3">
              <svg className="w-4 h-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              <div>
                <p className="text-sm font-medium">AI Engine</p>
                <p className="text-xs text-muted-foreground">Ollama LLM Service</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot status={ollamaStatus} />
              <span className="text-xs font-medium capitalize">{ollamaStatus}</span>
            </div>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setBackendStatus("checking")
              setOllamaStatus("checking")
              checkBackendHealth()
              checkOllamaHealth()
            }}
            className="gap-2 text-xs"
          >
            Refresh Status
          </Button>
        </div>
      </div>

      {/* About Section */}
      <div className="enterprise-card p-6">
        <h2 className="text-lg font-semibold mb-4">About Lexra</h2>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p><span className="font-medium text-foreground">Platform:</span> Lexra Contract Intelligence</p>
          <p><span className="font-medium text-foreground">Version:</span> 1.0.0</p>
          <p><span className="font-medium text-foreground">Framework:</span> CUAD (Contract Understanding Atticus Dataset)</p>
          <p><span className="font-medium text-foreground">Capabilities:</span> Contract analysis, risk assessment, clause extraction, AI-powered legal advisory</p>
        </div>
      </div>
    </div>
  )
}
