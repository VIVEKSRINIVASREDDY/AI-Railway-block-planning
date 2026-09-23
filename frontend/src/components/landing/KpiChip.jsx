import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) { return twMerge(clsx(inputs)); }

/* ════════════════════════ KPI Chip ════════════════════════ */
export default function KpiChip({ label, value, color }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0a0a0d] border border-[#1a1a22] shrink-0">
      <span className={cn("text-sm font-bold tracking-tight", color)}>{value}</span>
      <span className="text-[10px] text-slate-600 font-medium uppercase tracking-wider">{label}</span>
    </div>
  );
}
