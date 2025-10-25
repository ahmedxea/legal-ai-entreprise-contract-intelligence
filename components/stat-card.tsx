import type { LucideIcon } from "lucide-react"
import { Card } from "@/components/ui/card"

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: {
    value: string
    positive: boolean
  }
}

export function StatCard({ title, value, icon: Icon, trend }: StatCardProps) {
  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-semibold mt-2">{value}</p>
          {trend && (
            <p className={`text-sm mt-2 ${trend.positive ? "text-success" : "text-destructive"}`}>
              {trend.positive ? "↑" : "↓"} {trend.value}
            </p>
          )}
        </div>
        <div className="w-12 h-12 rounded-xl gradient-blue flex items-center justify-center">
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </Card>
  )
}
