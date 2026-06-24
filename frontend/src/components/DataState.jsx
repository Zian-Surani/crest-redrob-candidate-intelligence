export default function DataState({
  loading,
  error,
  children,
  compact = false,
}) {
  if (loading) {
    return (
      <div
        className={`bg-white border border-slate-200/60 rounded-premium shadow-premium flex items-center justify-center ${compact ? "p-8" : "p-16"}`}
      >
        <span className="w-6 h-6 rounded-full border-2 border-slate-200 border-t-primary animate-spin mr-3" />
        <span className="text-sm font-medium text-slate-500">
          Loading intelligence…
        </span>
      </div>
    );
  }
  if (error) {
    return (
      <div
        className={`bg-white border border-danger/20 rounded-premium shadow-premium ${compact ? "p-6" : "p-10"} flex items-start space-x-3`}
      >
        <span className="material-symbols-outlined text-danger">error</span>
        <div>
          <p className="font-bold text-slate-900">Backend unavailable</p>
          <p className="text-sm text-slate-500 mt-1">{error}</p>
        </div>
      </div>
    );
  }
  return children;
}
