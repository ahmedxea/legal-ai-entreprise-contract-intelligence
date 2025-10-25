"use client"

import { Navigation } from "@/components/navigation"
import { ChatInputBar } from "@/components/chat-input-bar"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Sparkles, FileText, AlertCircle, CheckCircle2 } from "lucide-react"
import { useState } from "react"

interface Message {
  id: number
  role: "user" | "assistant"
  content: string
  timestamp: string
  contractContext?: string | null
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      content:
        "Hello! I'm your AI contract assistant. I can help you understand contract terms, identify risks, answer legal questions, and provide guidance on contract management. How can I assist you today?",
      timestamp: "10:30 AM",
    },
  ])
  const [isTyping, setIsTyping] = useState(false)

  const contracts = [
    { id: 1, name: "Service Agreement 2025.pdf" },
    { id: 2, name: "NDA – Tech Corp.docx" },
    { id: 3, name: "Employment Contract.pdf" },
    { id: 4, name: "Vendor Agreement.pdf" },
  ]

  const suggestedQuestions = [
    "What are the key risks in my service agreement?",
    "Explain the termination clause in simple terms",
    "What should I look for in a confidentiality agreement?",
    "How can I negotiate better payment terms?",
  ]

  const handleSendMessage = async (message: string, selectedContract: string | null) => {
    const contractName = selectedContract
      ? contracts.find((c) => String(c.id) === selectedContract)?.name
      : "ALL Contracts"

    const userMessage: Message = {
      id: messages.length + 1,
      role: "user",
      content: message,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      contractContext: contractName,
    }

    setMessages([...messages, userMessage])
    setIsTyping(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          selectedContract: selectedContract ? Number(selectedContract) : null,
        }),
      })

      const data = await response.json()

      const aiMessage: Message = {
        id: messages.length + 2,
        role: "assistant",
        content: data.response || "I'm here to help! Could you provide more details?",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error("[v0] Error sending message:", error)
      const errorMessage: Message = {
        id: messages.length + 2,
        role: "assistant",
        content: "I apologize, but I encountered an error. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question, null)
  }

  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-12rem)]">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <Card className="p-6 glass-card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg gradient-blue flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="font-semibold">AI Assistant</h2>
                  <p className="text-xs text-muted-foreground">Always available</p>
                </div>
              </div>
              <Badge className="w-full justify-center bg-success text-success-foreground">Online</Badge>
            </Card>

            <Card className="p-6 glass-card">
              <h3 className="font-semibold mb-3 text-sm">Suggested Questions</h3>
              <div className="space-y-2">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestion(question)}
                    className="w-full text-left p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors text-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </Card>

            <Card className="p-6 glass-card">
              <h3 className="font-semibold mb-3 text-sm flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Recent Contracts
              </h3>
              <div className="space-y-2">
                {contracts.map((contract) => (
                  <div key={contract.id} className="p-2 rounded-lg bg-secondary/50 text-xs">
                    <p className="font-medium truncate">{contract.name}</p>
                    <p className="text-muted-foreground">Analyzed</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-3 flex flex-col">
            <Card className="flex-1 flex flex-col overflow-hidden glass-card">
              {/* Chat Header */}
              <div className="p-6 border-b border-border">
                <h1 className="text-2xl font-bold mb-2">Ask AI Assistant</h1>
                <p className="text-sm text-muted-foreground">
                  Get instant answers about your contracts, legal terms, and compliance requirements
                </p>
              </div>

              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((message) => (
                  <div key={message.id} className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        message.role === "assistant" ? "gradient-blue" : "bg-secondary"
                      }`}
                    >
                      {message.role === "assistant" ? (
                        <Sparkles className="w-5 h-5 text-white" />
                      ) : (
                        <MessageSquare className="w-5 h-5" />
                      )}
                    </div>

                    <div className={`flex-1 ${message.role === "user" ? "flex justify-end" : ""}`}>
                      <div
                        className={`inline-block max-w-[85%] p-4 rounded-lg ${
                          message.role === "assistant" ? "bg-secondary/50" : "gradient-blue text-white"
                        }`}
                      >
                        {message.role === "user" && message.contractContext && (
                          <p className="text-xs text-white/70 mb-2">📄 Context: {message.contractContext}</p>
                        )}
                        <p className="text-sm leading-relaxed">{message.content}</p>
                        <p
                          className={`text-xs mt-2 ${message.role === "assistant" ? "text-muted-foreground" : "text-white/70"}`}
                        >
                          {message.timestamp}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-lg gradient-blue flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="inline-block p-4 rounded-lg bg-secondary/50">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                          <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0.2s]" />
                          <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0.4s]" />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="p-6 border-t border-border">
                <ChatInputBar contracts={contracts} onSend={handleSendMessage} disabled={isTyping} />

                <div className="mt-4 flex items-start gap-2 text-xs text-muted-foreground">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <p>
                    AI responses are for informational purposes only and should not be considered legal advice. Always
                    consult with qualified legal professionals for specific legal matters.
                  </p>
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <div className="grid grid-cols-3 gap-4 mt-6">
              <Card className="p-4 hover:shadow-lg transition-shadow cursor-pointer glass-card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Analyze Contract</p>
                    <p className="text-xs text-muted-foreground">Upload & review</p>
                  </div>
                </div>
              </Card>

              <Card className="p-4 hover:shadow-lg transition-shadow cursor-pointer glass-card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-warning/10 flex items-center justify-center">
                    <AlertCircle className="w-5 h-5 text-warning" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Check Risks</p>
                    <p className="text-xs text-muted-foreground">Identify issues</p>
                  </div>
                </div>
              </Card>

              <Card className="p-4 hover:shadow-lg transition-shadow cursor-pointer glass-card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
                    <CheckCircle2 className="w-5 h-5 text-success" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Generate Clause</p>
                    <p className="text-xs text-muted-foreground">Create custom</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
