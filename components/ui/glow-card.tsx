import { cn } from "@/lib/utils"

interface GlowCardProps {
  children: React.ReactNode
  className?: string
  glowColor?: "primary" | "success" | "warning" | "destructive"
}

export function GlowCard({ children, className, glowColor = "primary" }: GlowCardProps) {
  const glowColors = {
    primary: "before:bg-primary/20",
    success: "before:bg-success/20",
    warning: "before:bg-warning/20",
    destructive: "before:bg-destructive/20",
  }

  return (
    <div
      className={cn(
        "relative group rounded-xl border bg-card p-6 transition-all duration-300",
        "hover:shadow-xl hover:shadow-primary/10 hover:scale-[1.02]",
        "before:absolute before:inset-0 before:rounded-xl before:opacity-0 before:blur-xl",
        "before:transition-opacity before:duration-300 group-hover:before:opacity-100",
        glowColors[glowColor],
        className
      )}
    >
      <div className="relative z-10">{children}</div>
    </div>
  )
}

interface BentoCardProps {
  children: React.ReactNode
  className?: string
  span?: "1" | "2" | "full"
}

export function BentoCard({ children, className, span = "1" }: BentoCardProps) {
  const spanClasses = {
    "1": "col-span-1",
    "2": "md:col-span-2",
    "full": "col-span-full",
  }

  return (
    <div
      className={cn(
        "rounded-xl border bg-card/50 backdrop-blur-sm p-6",
        "hover:bg-card transition-all duration-300",
        "hover:shadow-lg hover:border-primary/30",
        spanClasses[span],
        className
      )}
    >
      {children}
    </div>
  )
}
