import { useMemo, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell,
  AreaChart, Area,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, ZAxis,
  ComposedChart, Line,
} from 'recharts';
import { TrendingUp, ShieldAlert, Users } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) { return twMerge(clsx(inputs)); }

// ── Palette — muted, professional data-science tones ──────────────────────────
const C = {
  eng:      '#4f83cc',  // steel blue
  st:       '#4caf8a',  // muted teal
  elec:     '#9b6fb5',  // muted violet
  joint:    '#c49a3a',  // gold
  critical: '#b84040',  // muted red
  high:     '#c97a30',  // burnt orange
  medium:   '#7a9a40',  // olive
  low:      '#3a7a8a',  // slate teal
  accent:   '#4f83cc',
};

const DEPT_COLORS = { Engineering: C.eng, 'S&T': C.st, Electrical: C.elec };
const DAYS_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const DAYS_SHORT = { Monday:'Mon', Tuesday:'Tue', Wednesday:'Wed', Thursday:'Thu', Friday:'Fri', Saturday:'Sat', Sunday:'Sun' };

const tooltipStyle = {
  contentStyle: { backgroundColor: '#0d0d10', borderColor: '#2a2a35', borderRadius: '10px', color: '#c0c0cc', fontSize: 12 },
  itemStyle: { color: '#c0c0cc' },
  labelStyle: { color: '#888890', fontWeight: 600, fontSize: 11 },
  cursor: { fill: 'rgba(255,255,255,0.03)' },
};

// ── Sub-tab definitions ───────────────────────────────────────────────────────
const ANALYTICS_TABS = [
  { id: 'executive',   label: 'Executive Overview',    icon: TrendingUp },
  { id: 'safety',      label: 'Safety & Risk',         icon: ShieldAlert },
  { id: 'departments', label: 'Dept. Diagnostics',     icon: Users },
];

// ── Shared chart card wrapper ─────────────────────────────────────────────────
function ChartCard({ title, subtitle, children, span = 1, height = 240 }) {
  return (
    <div className={`bg-[#0d0d10] border border-[#1e1e26] rounded-2xl p-5 flex flex-col ${span === 2 ? 'lg:col-span-2' : ''}`}>
      <div className="mb-4">
        <div className="text-[#b0b0bc] font-semibold text-sm tracking-tight">{title}</div>
        {subtitle && <div className="text-[#44444e] text-[11px] mt-0.5">{subtitle}</div>}
      </div>
      <div style={{ height }}>{children}</div>
    </div>
  );
}

// ── Custom tooltip label ──────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label, unit = '' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d0d10] border border-[#2a2a35] rounded-xl px-3 py-2.5 text-xs min-w-[120px]">
      <div className="text-[#666670] font-semibold mb-1.5 uppercase tracking-wider text-[10px]">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: p.color || p.fill }}/>
          <span className="text-[#909098]">{p.name}:</span>
          <span className="text-[#c8c8d0] font-semibold ml-auto">{p.value}{unit}</span>
        </div>
      ))}
    </div>
  );
};

// ── Main Component ─────────────────────────────────────────────────────────────
export default function AnalyticsCharts({ schedule = [], tasks = [] }) {
  const [activeSubTab, setActiveSubTab] = useState('executive');

  // ── 1. Blocks per Day (Bar) ─────────────────────────────────────────────────
  const blocksPerDay = useMemo(() => {
    const map = {};
    DAYS_ORDER.forEach(d => { map[d] = { day: DAYS_SHORT[d], blocks: 0, hours: 0, joint: 0 }; });
    schedule.forEach(s => {
      const d = s.day_of_week;
      if (map[d]) {
        map[d].blocks += 1;
        map[d].hours = +(map[d].hours + (s.total_hours || 0)).toFixed(1);
        if (s.is_multi_department) map[d].joint += 1;
      }
    });
    return Object.values(map);
  }, [schedule]);

  // ── 2. Dept task counts (donut + bar) ──────────────────────────────────────
  const deptStats = useMemo(() => {
    const map = { Engineering: { tasks: 0, blocks: 0, hours: 0 }, 'S&T': { tasks: 0, blocks: 0, hours: 0 }, Electrical: { tasks: 0, blocks: 0, hours: 0 } };
    tasks.forEach(t => {
      const d = t.department || t.Department;
      if (d && map[d]) map[d].tasks += 1;
    });
    schedule.forEach(s => {
      const depts = (s.departments || '').split(',').map(d => d.trim());
      depts.forEach(d => {
        if (map[d]) {
          map[d].blocks += 1;
          map[d].hours = +(map[d].hours + (s.total_hours || 0) / depts.length).toFixed(1);
        }
      });
    });
    return Object.entries(map).map(([name, v]) => ({ name, ...v, color: DEPT_COLORS[name] }));
  }, [schedule, tasks]);

  // ── 3. Criticality histogram ────────────────────────────────────────────────
  const critHist = useMemo(() => {
    const bins = Array.from({ length: 10 }, (_, i) => ({
      range: `${i * 10}–${i * 10 + 9}`,
      count: 0,
      tier: i >= 8 ? 'critical' : i >= 6 ? 'high' : i >= 4 ? 'medium' : 'low',
    }));
    tasks.forEach(t => {
      const score = (t.criticality_score || t.Criticality_Score || 0) * 100;
      const idx = Math.min(Math.floor(score / 10), 9);
      bins[idx].count += 1;
    });
    return bins;
  }, [tasks]);

  const critBinColor = (tier) => ({ critical: C.critical, high: C.high, medium: C.medium, low: C.low }[tier] || C.low);

  // ── 4. Hours vs Blocks scatter per section ─────────────────────────────────
  const sectionScatter = useMemo(() => {
    const map = {};
    schedule.forEach(s => {
      const sec = (s.section || 'Unknown').substring(0, 18);
      if (!map[sec]) map[sec] = { name: sec, blocks: 0, hours: 0, tasks: 0 };
      map[sec].blocks += 1;
      map[sec].hours = +(map[sec].hours + (s.total_hours || 0)).toFixed(1);
      map[sec].tasks += (s.task_count || 0);
    });
    return Object.values(map);
  }, [schedule]);

  // ── 5. Cumulative hours by day (area) ──────────────────────────────────────
  const cumulativeHours = useMemo(() => {
    let cum = 0;
    return blocksPerDay.map(d => {
      cum = +(cum + d.hours).toFixed(1);
      return { ...d, cumulative: cum };
    });
  }, [blocksPerDay]);

  // ── 6. Radar: dept capability profile ──────────────────────────────────────
  const radarData = useMemo(() => {
    const maxHrs = Math.max(...deptStats.map(d => d.hours)) || 1;
    const maxBlk = Math.max(...deptStats.map(d => d.blocks)) || 1;
    const maxTsk = Math.max(...deptStats.map(d => d.tasks)) || 1;

    const metrics = ['Task Load', 'Block Count', 'Hours Used', 'Avg Duration', 'Joint Blocks'];
    return metrics.map(m => {
      const row = { metric: m };
      deptStats.forEach(d => {
        if (m === 'Task Load')    row[d.name] = Math.round((d.tasks / maxTsk) * 100);
        if (m === 'Block Count')  row[d.name] = Math.round((d.blocks / maxBlk) * 100);
        if (m === 'Hours Used')   row[d.name] = Math.round((d.hours / maxHrs) * 100);
        if (m === 'Avg Duration') row[d.name] = d.blocks ? Math.round((d.hours / d.blocks) * 10) : 0;
        if (m === 'Joint Blocks') {
          const joint = schedule.filter(s => s.is_multi_department && s.departments?.includes(d.name)).length;
          row[d.name] = Math.round((joint / Math.max(d.blocks, 1)) * 100);
        }
      });
      return row;
    });
  }, [deptStats, schedule, tasks]);

  // ── 7. Time-of-day heatmap (blocks by hour) ─────────────────────────────────
  const hourBuckets = useMemo(() => {
    const buckets = [
      { label: '00–04', count: 0, dept: {} },
      { label: '04–08', count: 0, dept: {} },
      { label: '08–12', count: 0, dept: {} },
      { label: '12–16', count: 0, dept: {} },
      { label: '16–20', count: 0, dept: {} },
      { label: '20–24', count: 0, dept: {} },
    ];
    schedule.forEach(s => {
      const h = Math.floor(s.block_start_hour || 0);
      const idx = Math.min(Math.floor(h / 4), 5);
      buckets[idx].count += 1;
      const dept = (s.departments || '').split(',')[0].trim();
      buckets[idx].dept[dept] = (buckets[idx].dept[dept] || 0) + 1;
    });
    return buckets.map(b => ({
      label: b.label,
      count: b.count,
      Engineering: b.dept.Engineering || 0,
      'S&T': b.dept['S&T'] || 0,
      Electrical: b.dept.Electrical || 0,
    }));
  }, [schedule]);

  // ── 8. Priority tier distribution ──────────────────────────────────────────
  const priorityData = useMemo(() => {
    const map = { 1: 0, 2: 0, 3: 0, 4: 0 };
    const labels = { 1: 'Critical', 2: 'High', 3: 'Medium', 4: 'Low' };
    tasks.forEach(t => {
      const tier = t.priority_tier || t.Priority_Tier;
      if (tier && map[tier] !== undefined) map[tier] += 1;
    });
    return Object.entries(map).map(([k, v]) => ({
      name: labels[k], value: v,
      color: { 1: C.critical, 2: C.high, 3: C.medium, 4: C.low }[k],
    }));
  }, [tasks]);

  // ── Summary KPIs derived from data ─────────────────────────────────────────
  const summary = useMemo(() => {
    const totalHours = schedule.reduce((a, s) => a + (s.total_hours || 0), 0);
    const avgHrs = schedule.length ? (totalHours / schedule.length).toFixed(1) : 0;
    const peakDay = blocksPerDay.reduce((a, b) => b.blocks > a.blocks ? b : a, blocksPerDay[0] || { day: '-', blocks: 0 });
    const jointPct = schedule.length ? Math.round(schedule.filter(s => s.is_multi_department).length / schedule.length * 100) : 0;
    return { totalHours: totalHours.toFixed(0), avgHrs, peakDay: peakDay?.day, jointPct };
  }, [schedule, blocksPerDay]);

  const isEmpty = schedule.length === 0 && tasks.length === 0;

  if (isEmpty) return (
    <div className="flex flex-col items-center justify-center py-20 text-[#333340]">
      <BarChart className="w-10 h-10 mb-4 opacity-40" />
      <p className="text-sm">Run the pipeline first to generate analytics data.</p>
    </div>
  );

  return (
    <div className="space-y-4">

      {/* ── Top summary strip — always visible ─────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Block Hours',  value: `${summary.totalHours}h`,  sub: 'across all corridors' },
          { label: 'Avg Hours / Block',  value: `${summary.avgHrs}h`,      sub: 'per maintenance block' },
          { label: 'Peak Day',           value: summary.peakDay,            sub: 'most blocks scheduled' },
          { label: 'Joint Block Rate',   value: `${summary.jointPct}%`,    sub: 'multi-dept integration' },
        ].map(m => (
          <div key={m.label} className="bg-[#0a0a0d] border border-[#191920] rounded-xl px-4 py-3">
            <div className="text-[#c0c0cc] font-bold text-xl tracking-tight">{m.value}</div>
            <div className="text-[#404050] text-[10px] font-semibold uppercase tracking-wider mt-0.5">{m.label}</div>
            <div className="text-[#30303a] text-[10px] mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Sub-Tab Navigation ─────────────────────────────────────────────── */}
      <div className="analytics-tab-bar flex gap-1 p-1">
        {ANALYTICS_TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={cn(
                "analytics-tab flex items-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 flex-1 justify-center",
                isActive
                  ? "analytics-tab-active"
                  : "text-[#606070] hover:text-[#a0a0ac] hover:bg-white/[0.02]"
              )}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ══════════════ EXECUTIVE OVERVIEW ══════════════ */}
      {activeSubTab === 'executive' && (
        <div className="space-y-4 animate-fade-in-up">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Blocks Scheduled per Day" subtitle="Bar split by single vs. joint blocks" height={240}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={blocksPerDay} margin={{ top: 5, right: 10, left: -25, bottom: 0 }} barSize={20}>
                  <CartesianGrid strokeDasharray="2 4" stroke="#151520" vertical={false}/>
                  <XAxis dataKey="day" tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<CustomTooltip/>}/>
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: '#505060' }}/>
                  <Bar dataKey="blocks"  name="Single Dept" stackId="a" fill={C.st}   radius={[0,0,0,0]}/>
                  <Bar dataKey="joint"   name="Joint Block"  stackId="a" fill={C.joint} radius={[4,4,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Cumulative Maintenance Hours" subtitle="Rolling total across the week" height={240}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={cumulativeHours} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="cumGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%"   stopColor={C.accent} stopOpacity={0.25}/>
                      <stop offset="100%" stopColor={C.accent} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="2 4" stroke="#151520" vertical={false}/>
                  <XAxis dataKey="day" tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<CustomTooltip unit="h"/>}/>
                  <Area dataKey="cumulative" name="Cumulative Hours" fill="url(#cumGrad)" stroke={C.accent} strokeWidth={2} dot={false}/>
                  <Bar dataKey="hours" name="Day Hours" fill="#1a2a38" radius={[3,3,0,0]} barSize={14}/>
                </ComposedChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <ChartCard title="Section Workload Scatter" subtitle="X = blocks, Y = total hours, size = task count" span={2} height={260}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="#151520"/>
                <XAxis dataKey="blocks" name="Blocks" type="number" tick={{ fill: '#505060', fontSize: 10 }} axisLine={false} tickLine={false} label={{ value: 'Blocks', position: 'insideBottom', offset: -5, fill: '#404050', fontSize: 10 }}/>
                <YAxis dataKey="hours"  name="Hours"  type="number" tick={{ fill: '#505060', fontSize: 10 }} axisLine={false} tickLine={false} label={{ value: 'Hrs', angle: -90, position: 'insideLeft', offset: 15, fill: '#404050', fontSize: 10 }}/>
                <ZAxis dataKey="tasks" range={[30, 200]} name="Tasks"/>
                <Tooltip
                  cursor={{ strokeDasharray: '3 3', stroke: '#2a2a38' }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0]?.payload;
                    return (
                      <div className="bg-[#0d0d10] border border-[#2a2a35] rounded-xl px-3 py-2.5 text-xs">
                        <div className="text-[#909098] font-semibold mb-1.5 text-[10px] uppercase">{d?.name}</div>
                        <div className="text-[#c8c8d0]">Blocks: <strong>{d?.blocks}</strong></div>
                        <div className="text-[#c8c8d0]">Hours: <strong>{d?.hours}h</strong></div>
                        <div className="text-[#c8c8d0]">Tasks: <strong>{d?.tasks}</strong></div>
                      </div>
                    );
                  }}
                />
                <Scatter data={sectionScatter} fill={C.accent} fillOpacity={0.7} stroke={C.accent} strokeWidth={0.5}/>
              </ScatterChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}

      {/* ══════════════ SAFETY & RISK ══════════════ */}
      {activeSubTab === 'safety' && (
        <div className="space-y-4 animate-fade-in-up">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Task Criticality Score Distribution" subtitle="Histogram across 0–100 score bands" height={260}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={critHist} margin={{ top: 5, right: 10, left: -25, bottom: 0 }} barSize={18}>
                  <CartesianGrid strokeDasharray="2 4" stroke="#151520" vertical={false}/>
                  <XAxis dataKey="range" tick={{ fill: '#505060', fontSize: 9 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<CustomTooltip/>}/>
                  <Bar dataKey="count" name="Tasks" radius={[3,3,0,0]}>
                    {critHist.map((entry, i) => (
                      <Cell key={i} fill={critBinColor(entry.tier)} fillOpacity={0.85}/>
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Priority Tier Breakdown" subtitle="Task count by AI-assigned urgency tier" height={260}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={priorityData}
                    cx="50%" cy="50%"
                    innerRadius={55} outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="none"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={{ stroke: '#2a2a38', strokeWidth: 1 }}
                  >
                    {priorityData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} fillOpacity={0.85}/>
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip/>}/>
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Risk summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {(() => {
              const critTasks = tasks.filter(t => (t.priority_tier || t.Priority_Tier) === 1).length;
              const highTasks = tasks.filter(t => (t.priority_tier || t.Priority_Tier) === 2).length;
              const avgScore = tasks.length
                ? (tasks.reduce((a, t) => a + (t.criticality_score || t.Criticality_Score || 0), 0) / tasks.length * 100).toFixed(1)
                : '0.0';
              const riskRatio = tasks.length ? ((critTasks + highTasks) / tasks.length * 100).toFixed(0) : '0';
              return [
                { label: 'Critical Tasks', value: critTasks, color: 'text-[#b84040]' },
                { label: 'High Priority', value: highTasks, color: 'text-[#c97a30]' },
                { label: 'Avg Criticality', value: `${avgScore}`, color: 'text-[#c49a3a]' },
                { label: 'Risk Ratio', value: `${riskRatio}%`, color: 'text-[#b84040]' },
              ].map(m => (
                <div key={m.label} className="bg-[#0a0a0d] border border-[#191920] rounded-xl px-4 py-3 text-center">
                  <div className={cn("font-bold text-2xl tracking-tight", m.color)}>{m.value}</div>
                  <div className="text-[#404050] text-[10px] font-semibold uppercase tracking-wider mt-1">{m.label}</div>
                </div>
              ));
            })()}
          </div>
        </div>
      )}

      {/* ══════════════ DEPARTMENT DIAGNOSTICS ══════════════ */}
      {activeSubTab === 'departments' && (
        <div className="space-y-4 animate-fade-in-up">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Department Workload Comparison" subtitle="Tasks, Blocks, Hours per department" height={250}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={deptStats} margin={{ top: 5, right: 10, left: -25, bottom: 0 }} barGap={4} barCategoryGap="35%">
                  <CartesianGrid strokeDasharray="2 4" stroke="#151520" vertical={false}/>
                  <XAxis dataKey="name" tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<CustomTooltip/>}/>
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: '#505060' }}/>
                  <Bar dataKey="tasks"  name="Tasks"  fill={C.eng}  radius={[3,3,0,0]} barSize={14}/>
                  <Bar dataKey="blocks" name="Blocks" fill={C.st}   radius={[3,3,0,0]} barSize={14}/>
                  <Bar dataKey="hours"  name="Hours"  fill={C.elec} radius={[3,3,0,0]} barSize={14}/>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Department Capability Radar" subtitle="Relative performance across 5 dimensions" height={250}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} margin={{ top: 10, right: 30, left: 30, bottom: 10 }}>
                  <PolarGrid stroke="#1e1e2a" gridType="polygon"/>
                  <PolarAngleAxis dataKey="metric" tick={{ fill: '#505060', fontSize: 10 }}/>
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#333340', fontSize: 9 }} axisLine={false}/>
                  {deptStats.map(d => (
                    <Radar key={d.name} name={d.name} dataKey={d.name}
                      stroke={d.color} fill={d.color} fillOpacity={0.12} strokeWidth={1.5}/>
                  ))}
                  <Tooltip content={<CustomTooltip unit="%"/>}/>
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: '#505060' }}/>
                </RadarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Blocks by Time of Day" subtitle="Stacked by department — identifies peak maintenance windows" height={240}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourBuckets} margin={{ top: 5, right: 10, left: -25, bottom: 0 }} barSize={28}>
                  <CartesianGrid strokeDasharray="2 4" stroke="#151520" vertical={false}/>
                  <XAxis dataKey="label" tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<CustomTooltip/>}/>
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: '#505060' }}/>
                  <Bar dataKey="Engineering" name="Engineering" stackId="h" fill={C.eng}  fillOpacity={0.85}/>
                  <Bar dataKey="S&T"         name="S&T"         stackId="h" fill={C.st}   fillOpacity={0.85}/>
                  <Bar dataKey="Electrical"  name="Electrical"  stackId="h" fill={C.elec} fillOpacity={0.85} radius={[3,3,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Weekly hours profile */}
            <ChartCard
              title="Weekly Hours Profile by Department"
              subtitle="Area chart showing each department's load across the week"
              height={240}
            >
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={blocksPerDay.map(d => {
                    const row = { day: d.day };
                    deptStats.forEach(dept => {
                      const hrs = schedule
                        .filter(s => s.day_of_week?.slice(0,3) === d.day && s.departments?.includes(dept.name))
                        .reduce((a, s) => a + (s.total_hours || 0), 0);
                      row[dept.name] = +hrs.toFixed(1);
                    });
                    return row;
                  })}
                  margin={{ top: 5, right: 20, left: -20, bottom: 0 }}
                >
                  <defs>
                    {deptStats.map(d => (
                      <linearGradient key={d.name} id={`grad_${d.name.replace('&','n')}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor={d.color} stopOpacity={0.3}/>
                        <stop offset="100%" stopColor={d.color} stopOpacity={0}/>
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid strokeDasharray="2 4" stroke="#151520" vertical={false}/>
                  <XAxis dataKey="day" tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill: '#505060', fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<CustomTooltip unit="h"/>}/>
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: '#505060' }}/>
                  {deptStats.map(d => (
                    <Area key={d.name} type="monotone" dataKey={d.name}
                      stroke={d.color} strokeWidth={1.5}
                      fill={`url(#grad_${d.name.replace('&','n')})`}
                      dot={{ r: 3, fill: d.color, strokeWidth: 0 }}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </div>
      )}

    </div>
  );
}
