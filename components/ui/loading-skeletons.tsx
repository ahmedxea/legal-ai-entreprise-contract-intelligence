import { Skeleton } from "@/components/ui/skeleton"

export function StatCardSkeleton() {
  return (
    <div className="enterprise-card p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-8 w-16 mt-2" />
          <Skeleton className="h-3 w-20 mt-2" />
        </div>
        <Skeleton className="w-12 h-12 rounded-lg" />
      </div>
    </div>
  )
}

export function ContractCardSkeleton() {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg border">
      <div className="flex items-center gap-3 flex-1">
        <Skeleton className="w-10 h-10 rounded-lg" />
        <div className="flex-1">
          <Skeleton className="h-5 w-48 mb-2" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div>
          <Skeleton className="h-5 w-12 mb-1" />
          <Skeleton className="h-3 w-16" />
        </div>
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 rounded-lg border">
          <Skeleton className="w-10 h-10 rounded" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-8 w-24 rounded" />
        </div>
      ))}
    </div>
  )
}

export function UploadZoneSkeleton() {
  return (
    <div className="rounded-xl border-2 border-dashed p-10">
      <div className="flex flex-col items-center gap-3">
        <Skeleton className="w-14 h-14 rounded-full" />
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
    </div>
  )
}
