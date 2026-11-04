import { useState } from 'react';
import { Download, FileText, Table, CheckCircle, Loader2, QrCode } from 'lucide-react';

export default function ReportExporter({ schedule = [], stats = null }) {
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfDone, setPdfDone] = useState(false);
  const isApproved = stats?.solver_status === 'OPTIMAL' && stats?.plan_approved === true;

  const fmtH = h => {
    const hh = Math.floor(h), mm = Math.round((h - hh) * 60);
    return `${String(hh).padStart(2,'0')}:${String(mm).padStart(2,'0')}`;
  };

  const downloadCSV = () => {
    if (!schedule.length) return;
    const headers = ['Block ID', 'Section', 'Corridor', 'Day', 'Start Time', 'End Time', 'Duration (hrs)', 'Departments', 'Tasks', 'Joint Block'];
    const rows = schedule.map(r => [
      r.block_id, r.section, r.corridor, r.day_of_week,
      fmtH(r.block_start_hour), fmtH(r.block_end_hour),
      r.total_hours?.toFixed(1), r.departments, r.task_count,
      r.is_multi_department ? 'Yes' : 'No'
    ]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${v ?? ''}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `railway_block_schedule_${new Date().toISOString().slice(0,10)}.csv`;
    a.click(); URL.revokeObjectURL(url);
  };

  const downloadPDF = async () => {
    if (!schedule.length || pdfLoading) return;
    setPdfLoading(true);
    try {
      const { default: jsPDF } = await import('jspdf');
      const { default: autoTable } = await import('jspdf-autotable');
      const QRCode = await import('qrcode');

      const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const W = doc.internal.pageSize.getWidth();
      const H = doc.internal.pageSize.getHeight();

      // ── Page 1: Cover ──────────────────────────────────────────────────
      // Dark background
      doc.setFillColor(0, 0, 0);
      doc.rect(0, 0, W, H, 'F');

      // Header bar
      doc.setFillColor(16, 185, 129);
      doc.rect(0, 0, W, 16, 'F');

      doc.setTextColor(0, 0, 0);
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.text('INDIAN RAILWAYS — AI BLOCK PLANNING SYSTEM', 10, 10);
      doc.text(`Ref: PS-26027 | Generated: ${new Date().toLocaleString('en-IN')}`, W - 10, 10, { align: 'right' });

      // Title
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(26);
      doc.setFont('helvetica', 'bold');
      doc.text(isApproved ? 'SANCTIONED BLOCK CLEARANCE ORDER' : 'DRAFT BLOCK CLEARANCE ORDER', 10, 36);

      // Draft watermark across page 1 if not approved
      if (!isApproved) {
        doc.setFontSize(54);
        doc.setTextColor(239, 68, 68);
        doc.text('DRAFT — NOT SANCTIONED', W / 2, H / 2, { align: 'center', angle: 30 });
      }
      doc.text('DAILY BLOCK CLEARANCE ORDER', W / 2, 55, { align: 'center' });

      doc.setFontSize(12);
      doc.setTextColor(16, 185, 129);
      doc.text('AI-Optimised Maintenance Block Schedule', W / 2, 65, { align: 'center' });

      // KPI summary boxes
      if (stats) {
        const kpis = [
          { label: 'Asset Availability', value: `${stats.asset_availability_pct?.toFixed(1)}%` },
          { label: 'Block Utilization',  value: `${stats.block_utilization_pct?.toFixed(1)}%` },
          { label: 'Schedule Rate',      value: `${stats.schedule_rate_pct?.toFixed(0)}%` },
          { label: 'Integration Rate',   value: `${stats.integration_rate_pct?.toFixed(1)}%` },
          { label: 'Blocks Scheduled',   value: `${stats.blocks_scheduled}` },
          { label: 'Multi-Dept Blocks',  value: `${stats.multi_dept_blocks_scheduled}` },
        ];
        const boxW = (W - 20) / kpis.length;
        kpis.forEach((kpi, i) => {
          const x = 10 + i * boxW;
          doc.setFillColor(20, 20, 20);
          doc.roundedRect(x, 80, boxW - 3, 22, 2, 2, 'F');
          doc.setFontSize(14);
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(16, 185, 129);
          doc.text(kpi.value, x + (boxW - 3) / 2, 90, { align: 'center' });
          doc.setFontSize(7);
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(148, 163, 184);
          doc.text(kpi.label.toUpperCase(), x + (boxW - 3) / 2, 97, { align: 'center' });
        });
      }

      // Safety checklist
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(255, 255, 255);
      doc.text('PRE-BLOCK SAFETY CHECKLIST', 10, 120);
      const checklist = [
        'Caution Order issued to all train drivers on affected section',
        'Track patrolman deployed at both ends of engineering block',
        'Emergency contact numbers distributed to gang foremen',
        'Machines placed outside danger zone before opening line',
        'TPC (Traffic Power Controller) notified for OHE blocks',
        'Signal Gang posted at nearest cabin for S&T blocks',
        'Medical First Aid kit available at block site',
        'All staff briefed on emergency train movement procedures',
      ];
      checklist.forEach((item, i) => {
        doc.setFillColor(30, 30, 30);
        doc.roundedRect(10, 125 + i * 10, W - 20, 8, 1, 1, 'F');
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(200, 200, 200);
        doc.text(`☐  ${item}`, 14, 130.5 + i * 10);
      });

      // Footer
      doc.setFillColor(20, 20, 20);
      doc.rect(0, H - 10, W, 10, 'F');
      doc.setFontSize(7);
      doc.setTextColor(100, 100, 100);
      doc.text('CONFIDENTIAL — For Internal Railway Use Only | AI Block Planning System v1.0', W / 2, H - 4, { align: 'center' });

      // ── Page 2: Schedule Table ──────────────────────────────────────────
      doc.addPage();
      doc.setFillColor(0, 0, 0);
      doc.rect(0, 0, W, H, 'F');

      doc.setFillColor(16, 185, 129);
      doc.rect(0, 0, W, 12, 'F');
      doc.setTextColor(0); doc.setFontSize(8); doc.setFont('helvetica', 'bold');
      doc.text('OPTIMISED BLOCK SCHEDULE — FULL LISTING', 10, 8);
      doc.text(`Total Blocks: ${schedule.length}`, W - 10, 8, { align: 'right' });

      const tableRows = schedule.map(r => [
        r.block_id,
        r.section?.substring(0, 18) || '',
        r.corridor?.substring(0, 14) || '',
        r.day_of_week?.substring(0, 3) || '',
        `${fmtH(r.block_start_hour)}–${fmtH(r.block_end_hour)}`,
        r.total_hours?.toFixed(1),
        r.departments?.substring(0, 22) || '',
        r.task_count,
        r.is_multi_department ? '✓ Joint' : 'Single',
      ]);

      autoTable(doc, {
        head: [['Block ID', 'Section', 'Corridor', 'Day', 'Time Window', 'Hrs', 'Departments', 'Tasks', 'Type']],
        body: tableRows,
        startY: 18,
        theme: 'grid',
        styles: { fontSize: 7, cellPadding: 2, textColor: [200, 200, 200], fillColor: [10, 10, 10], lineColor: [40, 40, 40] },
        headStyles: { fillColor: [16, 185, 129], textColor: [0, 0, 0], fontStyle: 'bold', fontSize: 7 },
        alternateRowStyles: { fillColor: [18, 18, 18] },
        columnStyles: {
          0: { cellWidth: 28, textColor: [16, 185, 129], fontStyle: 'bold' },
          8: { halign: 'center' },
        },
      });

      // QR code on last page
      try {
        const qrData = `RAILWAY-BLOCK-SCHEDULE|${new Date().toISOString()}|BLOCKS:${schedule.length}|REF:PS-26027`;
        const qrCanvas = await QRCode.toCanvas(document.createElement('canvas'), qrData, {
          width: 100, margin: 1,
          color: { dark: '#10b981', light: '#000000' },
        });
        const qrImgData = qrCanvas.toDataURL('image/png');
        const finalY = (doc.lastAutoTable?.finalY || 200) + 10;
        if (finalY < H - 40) {
          doc.addImage(qrImgData, 'PNG', W - 40, finalY, 28, 28);
          doc.setFontSize(6); doc.setTextColor(100);
          doc.text('Scan to verify', W - 26, finalY + 31, { align: 'center' });
        }
      } catch (qrErr) { /* QR optional */ }

      doc.save(`railway_block_clearance_order_${new Date().toISOString().slice(0,10)}.pdf`);
      setPdfDone(true);
      setTimeout(() => setPdfDone(false), 3000);
    } catch (err) {
      console.error('PDF generation failed:', err);
      alert('PDF generation failed. Check console for details.');
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex items-center gap-1.5 text-xs text-slate-500 mr-auto">
        <FileText className="w-3.5 h-3.5"/>
        <span>{schedule.length} blocks ready to export</span>
      </div>

      {/* CSV Export */}
      <button
        onClick={downloadCSV}
        disabled={!schedule.length}
        className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[#333] bg-[#111] text-slate-300 hover:text-white hover:border-[#444] transition-all text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <Table className="w-3.5 h-3.5 text-emerald-400"/>
        Export CSV
      </button>

      {/* PDF Export */}
      <button
        onClick={downloadPDF}
        disabled={!schedule.length || pdfLoading}
        title={!isApproved ? "Document will be stamped DRAFT until formally approved by Divisional Officer." : undefined}
        className={`flex items-center gap-2 px-5 py-2 rounded-xl font-semibold text-xs transition-all ${
          pdfDone
            ? 'bg-emerald-600 text-white border border-emerald-500'
            : isApproved
            ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)]'
            : 'bg-[#1e1e24] border border-[#333] text-amber-300 hover:border-amber-500/50'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {pdfLoading ? (
          <><Loader2 className="w-3.5 h-3.5 animate-spin"/>Generating PDF...</>
        ) : pdfDone ? (
          <><CheckCircle className="w-3.5 h-3.5"/>Downloaded!</>
        ) : isApproved ? (
          <><Download className="w-3.5 h-3.5"/><QrCode className="w-3.5 h-3.5"/>Download Sanctioned Permit (PDF)</>
        ) : (
          <><FileText className="w-3.5 h-3.5"/>Export Draft Order (PDF)</>
        )}
      </button>
    </div>
  );
}
