import type { LucideIcon } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: {
    value: string
    positive: boolean
  }
  note?: string
  color?: "primary" | "success" | "warning" | "danger"
  delay?: number
}

export function StatCard({ title, value, icon: Icon, trend, note, color = "primary", delay = 0 }: StatCardProps) {
  const iconColors = {
    primary: "bg-gradient-to-br from-primary to-primary/80",
    success: "bg-gradient-to-br from-success to-success/80",
    warning: "bg-gradient-to-br from-warning to-warning/80",
    danger: "bg-gradient-to-br from-destructive to-destructive/80",
  }

  return (
    <Card 
      className="group relative overflow-hidden p-6 transition-all duration-500 hover:shadow-2xl hover:shadow-primary/10 hover:scale-[1.02] animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="relative flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-muted-foreground tracking-wide uppercase">
            {title}
          </p>
          <p className="text-4xl font-bold tracking-tight transition-all duration-300 group-hover:scale-105">
            {value}
          </p>
          {note && (
            <p className="text-xs text-muted-foreground mt-1">
              {note}
            </p>
          )}
          {trend && (
            <div className="flex items-center gap-1.5">
              <div
                className={cn(
                  "flex items-center gap-1 text-sm font-medium px-2 py-0.5 rounded-full",
                  trend.positive
                    ? "bg-success/10 text-success"
                    : "bg-destructive/10 text-destructive"
                )}
              >
                <span className="text-base">{trend.positive ? "↑" : "↓"}</span>
                <span>{trend.value}</span>
              </div>
            </div>
          )}
        </div>
        <div
          className={cn(
            "relative w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300",
            "group-hover:scale-110 group-hover:rotate-6",
            iconColors[color]
          )}
        >
          {/* Glow effect */}
          <div className={cn(
            "absolute inset-0 rounded-2xl blur-xl opacity-0 group-hover:opacity-50 transition-opacity duration-300",
            iconColors[color]
          )} />
          <Icon className="relative w-7 h-7 text-white" />
        </div>
      </div>
    </Card>
  )
}
