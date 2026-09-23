import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) { return twMerge(clsx(inputs)); }

/* ════════════════════════ KPI Box ════════════════════════ */
export default function KpiBox({ icon, value, label, color, animation }) {
  return (
    <div className="flex flex-col items-center justify-center p-6 sm:p-8 rounded-2xl bg-[#0a0a0a] border border-[#1a1a1a] hover:border-[#333] transition-colors group">
      <div className={cn("mb-3 opacity-90 transition-transform group-hover:scale-110", color, animation)}>
        {icon}
      </div>
      <div className="text-2xl sm:text-4xl font-extrabold text-white mb-1.5 font-outfit tracking-tight">
        {value}
      </div>
      <div className="text-[10px] sm:text-xs text-slate-500 font-semibold tracking-wide uppercase">
        {label}
      </div>
    </div>
  );
}
