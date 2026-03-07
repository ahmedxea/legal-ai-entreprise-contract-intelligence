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

class APIClient {
  private baseURL: string
  private _token: string | null = null

  constructor(baseURL: string = config.apiUrl) {
    this.baseURL = baseURL
  }

  setToken(token: string | null) {
    this._token = token
  }

  private get authHeaders(): Record<string, string> {
    if (this._token) {
      return { Authorization: `Bearer ${this._token}` }
    }
    return {}
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; ollama_status?: string; database?: string }> {
    const response = await fetch(`${this.baseURL}/health`)
    if (!response.ok) throw new Error("Backend is offline")
    return response.json()
  }

  // Contracts
  async getContracts(): Promise<Contract[]> {
    const response = await fetch(`${this.baseURL}/api/contracts/`, {
      headers: this.authHeaders,
    })
    if (!response.ok) throw new Error("Failed to fetch contracts")
    return response.json()
  }

  async getContract(contractId: string): Promise<Contract> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}`, {
      headers: this.authHeaders,
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
      headers: this.authHeaders,
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
      headers: this.authHeaders,
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Analysis failed" }))
      throw new Error(body.detail || `Analysis failed (${response.status})`)
    }

    return response.json()
  }

  async getContractAnalysis(contractId: string): Promise<ContractAnalysisResult> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}/analysis`, {
      headers: this.authHeaders,
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Failed to fetch analysis" }))
      throw new Error(body.detail || `Analysis fetch failed (${response.status})`)
    }

    return response.json()
  }

  /** Poll GET /contracts/{id} until the contract reaches one of the target statuses.
   *  Returns the final status string. Throws on "failed" or timeout. */
  async pollContractStatus(
    contractId: string,
    targetStatuses: string[],
    intervalMs = 3000,
    maxAttempts = 40,
  ): Promise<string> {
    for (let i = 0; i < maxAttempts; i++) {
      const contract = await this.getContract(contractId)
      if (targetStatuses.includes(contract.status)) return contract.status
      if (contract.status === "failed") throw new Error("Contract processing failed")
      await new Promise((r) => setTimeout(r, intervalMs))
    }
    throw new Error("Timed out waiting for contract processing")
  }

  async deleteContract(contractId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/contracts/${contractId}`, {
      method: "DELETE",
      headers: this.authHeaders,
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
      headers: this.authHeaders,
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Failed to fetch text" }))
      throw new Error(body.detail || `Text fetch failed (${response.status})`)
    }
    return response.json()
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await fetch(`${this.baseURL}/api/contracts/dashboard`, {
      headers: this.authHeaders,
    })
    if (!response.ok) throw new Error("Failed to fetch dashboard stats")
    return response.json()
  }
}

// Export singleton instance
export const apiClient = new APIClient()

// Export class for custom instances
export { APIClient }
