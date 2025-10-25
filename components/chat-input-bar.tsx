"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Send, Paperclip } from "lucide-react"
import { useState } from "react"

interface Contract {
  id: number | string
  name: string
}

interface ChatInputBarProps {
  contracts: Contract[]
  onSend: (message: string, selectedContract: string | null) => void
  disabled?: boolean
}

export function ChatInputBar({ contracts, onSend, disabled = false }: ChatInputBarProps) {
  const [message, setMessage] = useState("")
  const [selectedContract, setSelectedContract] = useState<string | null>(null)

  const handleSend = () => {
    if (!message.trim()) return
    onSend(message, selectedContract)
    setMessage("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="space-y-4">
      {/* Input Bar with Contract Selector */}
      <div className="flex gap-3 items-center">
        {/* Contract Selector Dropdown */}
        <Select
          value={selectedContract || "all"}
          onValueChange={(value) => setSelectedContract(value === "all" ? null : value)}
        >
          <SelectTrigger className="w-[200px] glass-card border-primary/20 hover:border-primary/40 transition-colors">
            <SelectValue placeholder="ALL Contracts" />
          </SelectTrigger>
          <SelectContent className="glass-card border-primary/20">
            <SelectItem value="all" className="cursor-pointer">
              ALL Contracts
            </SelectItem>
            {contracts.map((contract) => (
              <SelectItem key={contract.id} value={String(contract.id)} className="cursor-pointer">
                {contract.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Attachment Button */}
        <Button
          variant="outline"
          size="icon"
          className="flex-shrink-0 glass-card border-primary/20 hover:border-primary/40 hover:bg-primary/5 transition-all bg-transparent"
          disabled={disabled}
        >
          <Paperclip className="w-4 h-4" />
        </Button>

        {/* Message Input */}
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me anything about your contracts..."
          disabled={disabled}
          className="flex-1 px-4 py-3 rounded-xl glass-card border border-primary/20 bg-background/50 backdrop-blur-xl focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/40 transition-all placeholder:text-muted-foreground disabled:opacity-50 disabled:cursor-not-allowed"
        />

        {/* Send Button */}
        <Button
          onClick={handleSend}
          disabled={!message.trim() || disabled}
          className="gradient-blue text-white hover:opacity-90 hover:shadow-lg hover:shadow-primary/20 transition-all flex-shrink-0 rounded-xl"
        >
          <Send className="w-4 h-4 mr-2" />
          Send
        </Button>
      </div>
    </div>
  )
}
