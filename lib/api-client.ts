import { config } from "./config"

export interface Contract {
  id: string
  filename: string
  language: string
  industry?: string
  status: string
  uploaded_at?: string
  upload_date?: string
  blob_url: string
  extracted_data?: Record<string, any>
  analysis?: ContractAnalysis
}

export interface ContractAnalysis {
  extracted_data?: Record<string, any>
  entities?: Record<string, any>
  risks?: Risk[]
  legal_opinion?: Record<string, any>
  compliance?: Record<string, any>
  summary?: string
  missing_clauses?: string[]
  overall_risk_score?: number
  compliance_score?: number
}

export interface Risk {
  risk_type?: string
  severity: "low" | "medium" | "high" | "critical"
  description: string
  source_text?: string
  recommendation?: string
}

export interface ContractAnalysisResult {
  contract_id: string
  status: string
  summary?: string
  entities?: Record<string, any>
  risks?: Risk[]
  missing_clauses?: string[]
  overall_risk_score?: number
}

export interface DashboardStats {
  total_contracts: number
  analyzed_contracts: number
  pending_contracts: number
  high_risks: number
  average_risk_score: number
  compliance_score: number
}

export interface GenerateClauseRequest {
  clause_type: string
  risk_description?: string
  jurisdiction?: string
  contract_context?: string
}

export interface GeneratedClause {
  clause_title: string
  clause_text: string
  explanation: string
  clause_type: string
  jurisdiction: string
  template_used: boolean
  cuad_category: string
}

export interface CuadTemplate {
  clause_type: string
  title: string
  cuad_category: string
  placeholders: string[]
}

class APIClient {
  private baseURL: string

  constructor(baseURL: string = config.apiUrl) {
    this.baseURL = baseURL
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; ollama_status?: string; database?: string }> {
    const response = await fetch(`${this.baseURL}/health`)
    if (!response.ok) throw new Error("Backend is offline")
    return response.json()
  }

  // Contracts
  async getContracts(limit = 20, offset = 0): Promise<Contract[]> {
    const response = await fetch(
      `${this.baseURL}/api/contracts/?limit=${limit}&offset=${offset}`,
      { credentials: "include" }
    )
    if (!response.ok) throw new Error("Failed to fetch contracts")
    return response.json()
  }

  async getContract(contractId: string): Promise<Contract> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}`, {
      credentials: "include",
    })
    if (!response.ok) throw new Error("Failed to fetch contract")
    return response.json()
  }

  async uploadContract(file: File, language: string, industry?: string): Promise<Contract> {
    const formData = new FormData()
    formData.append("file", file)

    const params = new URLSearchParams({ language })
    if (industry) params.append("industry", industry)

    const response = await fetch(`${this.baseURL}/api/contracts/upload?${params}`, {
      method: "POST",
      credentials: "include",
      body: formData,
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Upload failed" }))
      throw new Error(body.detail || `Upload failed (${response.status})`)
    }

    return response.json()
  }

  async analyzeContract(contractId: string): Promise<{ contract_id: string; status: string; message: string }> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}/analyze`, {
      method: "POST",
      credentials: "include",
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Analysis failed" }))
      throw new Error(body.detail || `Analysis failed (${response.status})`)
    }

    return response.json()
  }

  async getContractAnalysis(contractId: string): Promise<ContractAnalysisResult> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}/analysis`, {
      credentials: "include",
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Failed to fetch analysis" }))
      throw new Error(body.detail || `Analysis fetch failed (${response.status})`)
    }

    return response.json()
  }

  /** Poll GET /contracts/{id} until the contract reaches one of the target statuses.
   *  Returns the final status string. Throws on "failed" or timeout.
   *  Tolerates up to 3 consecutive transient errors before giving up. */
  async pollContractStatus(
    contractId: string,
    targetStatuses: string[],
    intervalMs = 3000,
    maxAttempts = 200,
  ): Promise<string> {
    let consecutiveErrors = 0
    const maxConsecutiveErrors = 10

    for (let i = 0; i < maxAttempts; i++) {
      try {
        const contract = await this.getContract(contractId)
        consecutiveErrors = 0
        if (targetStatuses.includes(contract.status)) return contract.status
        if (contract.status === "failed") throw new Error("Contract processing failed")
      } catch (err: any) {
        // If it's a definitive processing failure, re-throw immediately
        if (err.message === "Contract processing failed") throw err
        consecutiveErrors++
        if (consecutiveErrors >= maxConsecutiveErrors) {
          throw new Error(`Lost connection to server while checking contract status: ${err.message}`)
        }
      }
      await new Promise((r) => setTimeout(r, intervalMs))
    }
    throw new Error("Timed out waiting for contract processing")
  }

  async deleteContract(contractId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}`, {
      method: "DELETE",
      credentials: "include",
    })

    if (!response.ok) throw new Error("Failed to delete contract")
  }

  /** Returns the URL that serves the original uploaded file (PDF/DOCX). */
  getContractFileUrl(contractId: string): string {
    return `${this.baseURL}/api/contracts/${contractId}/file`
  }

  async getContractText(contractId: string): Promise<{
    document_id: string
    raw_text: string
    paragraphs: string[]
    page_count?: number
    file_type?: string
  }> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}/text`, {
      credentials: "include",
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Failed to fetch text" }))
      throw new Error(body.detail || `Text fetch failed (${response.status})`)
    }
    return response.json()
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await fetch(`${this.baseURL}/api/contracts/dashboard`, {
      credentials: "include",
    })
    if (!response.ok) throw new Error("Failed to fetch dashboard stats")
    return response.json()
  }

  async generateClause(request: GenerateClauseRequest): Promise<GeneratedClause> {
    const response = await fetch(`${this.baseURL}/api/clauses/generate-for-risk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Generation failed" }))
      throw new Error(body.detail || `Clause generation failed (${response.status})`)
    }
    return response.json()
  }

  async getCuadTemplates(): Promise<CuadTemplate[]> {
    const response = await fetch(`${this.baseURL}/api/clauses/cuad-templates`, {
      credentials: "include",
    })
    if (!response.ok) throw new Error("Failed to fetch CUAD templates")
    return response.json()
  }

  async updateProfile(data: { full_name?: string; organization?: string }): Promise<{ user: any; message: string }> {
    const response = await fetch(`${this.baseURL}/api/auth/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Update failed" }))
      throw new Error(body.detail || `Profile update failed (${response.status})`)
    }
    return response.json()
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseURL}/api/auth/change-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Password change failed" }))
      throw new Error(body.detail || `Password change failed (${response.status})`)
    }
    return response.json()
  }
}

// Export singleton instance
export const apiClient = new APIClient()

// Export class for custom instances
export { APIClient }
