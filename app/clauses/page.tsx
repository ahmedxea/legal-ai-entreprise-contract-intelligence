"use client"

import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileCode, Sparkles, Copy, Download, RefreshCw, ChevronRight } from "lucide-react"
import { useState } from "react"

export default function ClauseGeneratorPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("confidentiality")
  const [generatedClause, setGeneratedClause] = useState<string>("")
  const [isGenerating, setIsGenerating] = useState(false)

  const clauseCategories = [
    { id: "confidentiality", name: "Confidentiality", icon: "🔒", count: 12 },
    { id: "termination", name: "Termination", icon: "📋", count: 8 },
    { id: "liability", name: "Liability & Indemnity", icon: "⚖️", count: 10 },
    { id: "payment", name: "Payment Terms", icon: "💰", count: 6 },
    { id: "ip", name: "Intellectual Property", icon: "💡", count: 9 },
    { id: "dispute", name: "Dispute Resolution", icon: "🤝", count: 7 },
  ]

  const clauseTemplates = {
    confidentiality: [
      {
        name: "Standard NDA Clause",
        description: "Basic confidentiality agreement for general business use",
        jurisdiction: "US",
      },
      {
        name: "Mutual Confidentiality",
        description: "Two-way confidentiality for partnerships",
        jurisdiction: "US",
      },
      {
        name: "GDPR-Compliant Confidentiality",
        description: "EU data protection compliant confidentiality clause",
        jurisdiction: "EU",
      },
    ],
    termination: [
      {
        name: "Termination for Convenience",
        description: "Allow either party to terminate with notice",
        jurisdiction: "US",
      },
      {
        name: "Termination for Cause",
        description: "Termination based on breach or non-performance",
        jurisdiction: "US",
      },
    ],
  }

  const sampleClause = `CONFIDENTIALITY AND NON-DISCLOSURE

1. Definition of Confidential Information
   "Confidential Information" means any and all technical and non-technical information disclosed by either party, including but not limited to:
   (a) Trade secrets, know-how, inventions, techniques, processes, algorithms, software programs, and software source documents;
   (b) Information regarding plans for research, development, new products, marketing and selling, business plans, budgets and unpublished financial statements;
   (c) Customer and supplier lists, pricing information, and other proprietary information.

2. Obligations
   The Receiving Party agrees to:
   (a) Hold and maintain the Confidential Information in strict confidence;
   (b) Not disclose the Confidential Information to any third parties without prior written consent;
   (c) Use the Confidential Information solely for the purpose of this Agreement;
   (d) Protect the Confidential Information using the same degree of care used to protect its own confidential information, but in no event less than reasonable care.

3. Exceptions
   The obligations set forth in this Section shall not apply to information that:
   (a) Was publicly known at the time of disclosure or becomes publicly known through no breach of this Agreement;
   (b) Was rightfully received from a third party without breach of any confidentiality obligation;
   (c) Was independently developed without use of or reference to the Confidential Information;
   (d) Is required to be disclosed by law or court order, provided that the Receiving Party provides prompt notice to the Disclosing Party.

4. Term
   The obligations under this Section shall survive for a period of five (5) years from the date of disclosure of the Confidential Information.`

  const handleGenerate = () => {
    setIsGenerating(true)
    setTimeout(() => {
      setGeneratedClause(sampleClause)
      setIsGenerating(false)
    }, 2000)
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedClause)
  }

  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-3 text-balance">AI Clause Generator</h1>
          <p className="text-lg text-muted-foreground">
            Generate legally sound contract clauses tailored to your specific needs
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Clause Categories Sidebar */}
          <div className="lg:col-span-1">
            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-4">Clause Categories</h2>
              <div className="space-y-2">
                {clauseCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedCategory === category.id ? "bg-primary text-primary-foreground" : "hover:bg-secondary"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{category.icon}</span>
                        <div>
                          <p className="font-medium text-sm">{category.name}</p>
                          <p
                            className={`text-xs mt-0.5 ${selectedCategory === category.id ? "text-primary-foreground/80" : "text-muted-foreground"}`}
                          >
                            {category.count} templates
                          </p>
                        </div>
                      </div>
                      <ChevronRight
                        className={`w-4 h-4 ${selectedCategory === category.id ? "text-primary-foreground" : "text-muted-foreground"}`}
                      />
                    </div>
                  </button>
                ))}
              </div>
            </Card>

            {/* Quick Tips */}
            <Card className="p-6 mt-6">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                Quick Tips
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>Always review generated clauses with legal counsel</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>Customize clauses to fit your specific jurisdiction</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>Consider industry-specific requirements</span>
                </li>
              </ul>
            </Card>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Template Selection */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">
                {clauseCategories.find((c) => c.id === selectedCategory)?.name} Templates
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {(clauseTemplates[selectedCategory as keyof typeof clauseTemplates] || []).map((template, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-semibold mb-1">{template.name}</h3>
                        <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
                        <Badge variant="outline" className="text-xs">
                          {template.jurisdiction}
                        </Badge>
                      </div>
                      <Button size="sm" className="gradient-blue text-white hover:opacity-90" onClick={handleGenerate}>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Custom Generation */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Custom Clause Generation</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Describe your requirements</label>
                  <textarea
                    className="w-full min-h-32 p-3 rounded-lg border border-input bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="E.g., I need a confidentiality clause for a software development agreement that includes provisions for source code protection and a 3-year confidentiality period..."
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Jurisdiction</label>
                    <select className="w-full p-3 rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring">
                      <option>United States</option>
                      <option>European Union</option>
                      <option>United Kingdom</option>
                      <option>Canada</option>
                      <option>Australia</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Industry</label>
                    <select className="w-full p-3 rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring">
                      <option>Technology</option>
                      <option>Healthcare</option>
                      <option>Finance</option>
                      <option>Manufacturing</option>
                      <option>Retail</option>
                    </select>
                  </div>
                </div>

                <Button className="gradient-blue text-white hover:opacity-90 w-full" onClick={handleGenerate}>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Custom Clause
                </Button>
              </div>
            </Card>

            {/* Generated Clause Output */}
            {(generatedClause || isGenerating) && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <FileCode className="w-5 h-5" />
                    Generated Clause
                  </h2>
                  {!isGenerating && (
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={handleCopy}>
                        <Copy className="w-4 h-4 mr-2" />
                        Copy
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleGenerate}>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Regenerate
                      </Button>
                    </div>
                  )}
                </div>

                {isGenerating ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
                    <p className="text-muted-foreground">Generating your clause...</p>
                  </div>
                ) : (
                  <div className="p-4 rounded-lg bg-secondary/50 font-mono text-sm whitespace-pre-wrap leading-relaxed">
                    {generatedClause}
                  </div>
                )}

                {!isGenerating && (
                  <div className="mt-4 p-4 rounded-lg bg-warning/10 border border-warning/20">
                    <p className="text-sm text-warning-foreground">
                      <strong>Legal Disclaimer:</strong> This clause is generated by AI and should be reviewed by
                      qualified legal counsel before use. It may not be suitable for all situations or jurisdictions.
                    </p>
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
