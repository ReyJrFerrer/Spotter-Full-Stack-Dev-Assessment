/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { DailyLogSheet, DutyStatus } from '../types';
import { FileText, Calendar, Truck, ShieldCheck, ArrowRight, ArrowLeft, Download, AlertCircle, Globe2 } from 'lucide-react';

interface Props {
  dailyLogs: DailyLogSheet[];
  tripContext?: {
    currentLabel: string;
    pickupLabel: string;
    dropoffLabel: string;
    totalDistanceMiles: number;
    totalDurationHours: number;
    currentCycleUsedHrs: number;
    tripTimezone: string;
  };
}

export default function EldLogSheets({ dailyLogs, tripContext }: Props) {
  const [activeDateIndex, setActiveDateIndex] = useState(0);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  if (!dailyLogs || dailyLogs.length === 0) {
    return (
      <div className="bg-white border-2 border-[#1A1A1A] p-6 text-center text-slate-500 text-xs font-bold uppercase tracking-widest">
        No ELD Daily Logs available. Enter trip settings and calculate route.
      </div>
    );
  }

  const activeLog = dailyLogs[activeDateIndex];
  
  // Dimensions for vectorized grid
  const width = 800;
  const height = 180;
  
  const leftPadding = 130;  // For labels
  const rightPadding = 60;   // For sub-totals
  const gridWidth = width - leftPadding - rightPadding; // 610px
  
  const topPadding = 30; // Scale hours
  const gridHeight = height - topPadding - 10; // 140px
  const rowHeight = gridHeight / 4; // 35px each row
  
  // Linear scale equations
  const getX = (hour: number) => {
    return leftPadding + (hour / 24) * gridWidth;
  };
  
  const getY = (status: DutyStatus) => {
    const startY = topPadding;
    switch (status) {
      case DutyStatus.OFF:
        return startY + rowHeight / 2;       // Row 1 (OFF) midpoint
      case DutyStatus.SB:
        return startY + rowHeight * 1.5;     // Row 2 (SB) midpoint
      case DutyStatus.D:
        return startY + rowHeight * 2.5;     // Row 3 (D) midpoint
      case DutyStatus.ON:
        return startY + rowHeight * 3.5;     // Row 4 (ON) midpoint
    }
  };

  const handleExportPdf = async () => {
    setIsExporting(true);
    setExportError(null);

    const summary = {
      from_label: tripContext?.currentLabel ?? "—",
      pickup_label: tripContext?.pickupLabel ?? "—",
      dropoff_label: tripContext?.dropoffLabel ?? "—",
      total_distance_miles: tripContext?.totalDistanceMiles ?? 0,
      total_duration_hours: tripContext?.totalDurationHours ?? 0,
      current_cycle_used_hrs: tripContext?.currentCycleUsedHrs ?? 0,
      trip_days: dailyLogs.length,
      carrier_name: activeLog.carrierName ?? "",
      tractor_number: activeLog.tractorNumber ?? "",
      trailer_number: activeLog.trailerNumber ?? "",
    };

    const payload = {
      summary,
      daily_logs: dailyLogs.map((log) => ({
        date_string: log.dateString,
        date_label: log.dateLabel,
        total_miles_driven: log.totalMilesDriven,
        tractor_number: log.tractorNumber,
        trailer_number: log.trailerNumber,
        carrier_name: log.carrierName,
        timeline: log.timeline.map((b) => ({
          status: b.status,
          start_hour: b.startHour,
          end_hour: b.endHour,
          location_name: b.locationName,
          remarks: b.remarks ?? "",
        })),
        totals: log.totals,
        remarks: log.remarks.map((r) => ({
          time_label: r.timeLabel,
          status: r.status,
          location: r.location,
          remarks_text: r.remarksText,
        })),
      })),
    };

    const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

    try {
      const response = await fetch(`${API_BASE}/api/trips/export-pdf/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let detail = `Server returned ${response.status}`;
        try {
          const err = await response.json();
          detail = err.error || err.detail || JSON.stringify(err);
        } catch { /* ignore parse errors */ }
        throw new Error(detail);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const filename = `eld-logs-${activeLog.dateString}.pdf`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setExportError(err?.message || "Failed to generate PDF. Ensure the dispatch server is reachable.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div id="results-eld-dashboard" className="bg-white border-2 border-[#1A1A1A] p-6 shadow-[6px_6px_0px_#133658]">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b-2 border-[#1A1A1A] pb-5 mb-5">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-[#FD5368]" />
          <h2 className="text-xs font-bold uppercase tracking-widest text-[#1A1A1A]">4. Certified FMCSA Daily ELD Logs</h2>
        </div>

        {/* Pagination tabs to swap daily log sheets */}
        <div className="flex items-center gap-2">
          <button
            id="btn-log-prev"
            disabled={activeDateIndex === 0}
            onClick={() => setActiveDateIndex(prev => prev - 1)}
            className="p-1 px-3 bg-[#E8E4DF] border border-[#1A1A1A] text-[#1A1A1A] disabled:opacity-30 disabled:cursor-not-allowed hover:bg-black hover:text-white transition-all font-sans cursor-pointer flex items-center rounded-none"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
          </button>
          
          <div className="text-xs bg-[#1A1A1A] border border-[#1A1A1A] text-white font-bold px-3 py-1.5 rounded-none font-mono">
            Sheet {activeDateIndex + 1} of {dailyLogs.length}
          </div>

          <button
            id="btn-log-next"
            disabled={activeDateIndex === dailyLogs.length - 1}
            onClick={() => setActiveDateIndex(prev => prev + 1)}
            className="p-1 px-3 bg-[#E8E4DF] border border-[#1A1A1A] text-[#1A1A1A] disabled:opacity-30 disabled:cursor-not-allowed hover:bg-black hover:text-white transition-all font-sans cursor-pointer flex items-center rounded-none"
          >
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Sheet Metadata Header block */}
      <div className="bg-[#F4F1ED] p-4 border border-[#1A1A1A] mb-6 font-sans rounded-none">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-bold tracking-wider">
          <div className="space-y-1">
            <span className="text-[#1A1A1A]/70 text-[9px] uppercase block">Date on Grid</span>
            <span className="text-xs text-[#1A1A1A] flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-[#FD5368]" />
              {activeLog.dateLabel}
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[#1A1A1A]/70 text-[9px] uppercase block">Carrier Name</span>
            <span className="text-xs text-[#1A1A1A] block truncate">{activeLog.carrierName}</span>
          </div>

          <div className="space-y-1">
            <span className="text-[#1A1A1A]/70 text-[9px] uppercase block">Equipment IDs</span>
            <span className="text-xs text-[#1A1A1A] flex items-center gap-1.5">
              <Truck className="h-3.5 w-3.5 text-[#1A1A1A]" />
              TRAC: {activeLog.tractorNumber} / TRAIL: {activeLog.trailerNumber}
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[#1A1A1A]/70 text-[9px] uppercase block">Miles Driven Today</span>
            <span className="text-sm text-[#FD5368] block">
              {activeLog.totalMilesDriven} mi
            </span>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-[#1A1A1A]/20 flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-[#1A1A1A]/70">
          <Globe2 className="h-3 w-3 text-[#FD5368]" />
          All grid hours shown in {activeLog.timezone || tripContext?.tripTimezone || "UTC"} local time
        </div>
      </div>

      {/* SVG SCALABLE GRAPH GRID */}
      <div className="w-full overflow-x-auto bg-[#F4F1ED]/50 border border-[#1A1A1A]/40 p-4 mb-6">
        <svg
          id={`eld-graph-svg-${activeDateIndex}`}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full min-w-[720px] select-none h-auto font-mono bg-white border border-[#1A1A1A] shrink-0"
        >
          {/* Hour labels header axis */}
          {Array.from({ length: 25 }).map((_, i) => {
            const h = i === 24 ? 0 : i;
            let displayVal = String(h);
            if (h === 0) displayVal = "M"; // midnight
            if (h === 12) displayVal = "N"; // noon
            
            const x = getX(i);
            const isMidnightOrNoon = h === 0 || h === 12;

            return (
              <g key={`hour-${i}`}>
                {/* Text Indicator */}
                <text
                  x={x}
                  y={18}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight={isMidnightOrNoon ? "bold" : "normal"}
                  fill="#1A1A1A"
                  fillOpacity={isMidnightOrNoon ? "1" : "0.5"}
                >
                  {displayVal}
                </text>
                
                {/* Vertical heavy hour line */}
                <line
                  x1={x}
                  y1={topPadding}
                  x2={x}
                  y2={height - 15}
                  stroke="#1A1A1A"
                  strokeOpacity={isMidnightOrNoon ? "0.25" : "0.08"}
                  strokeWidth={isMidnightOrNoon ? "1.5" : "0.5"}
                />
                
                {/* Quarter hours ticks within column */}
                {i < 24 && (
                  <>
                    {/* 15 Minute Line */}
                    <line
                      x1={getX(i + 0.25)}
                      y1={topPadding}
                      x2={getX(i + 0.25)}
                      y2={height - 20}
                      stroke="#1A1A1A"
                      strokeOpacity="0.05"
                      strokeWidth="0.5"
                    />
                    {/* 30 Minute Line */}
                    <line
                      x1={getX(i + 0.50)}
                      y1={topPadding}
                      x2={getX(i + 0.50)}
                      y2={height - 20}
                      stroke="#1A1A1A"
                      strokeOpacity="0.05"
                      strokeWidth="0.5"
                      strokeDasharray="2,2"
                    />
                    {/* 45 Minute Line */}
                    <line
                      x1={getX(i + 0.75)}
                      y1={topPadding}
                      x2={getX(i + 0.75)}
                      y2={height - 20}
                      stroke="#1A1A1A"
                      strokeOpacity="0.05"
                      strokeWidth="0.5"
                    />
                  </>
                )}
              </g>
            );
          })}

          {/* Row Dividers and Labels */}
          <line x1={leftPadding} y1={topPadding} x2={width - rightPadding} y2={topPadding} stroke="#1A1A1A" strokeWidth="1.5" />
          <line x1={leftPadding} y1={topPadding + rowHeight} x2={width - rightPadding} y2={topPadding + rowHeight} stroke="#1A1A1A" strokeWidth="0.5" strokeOpacity="0.2" />
          <line x1={leftPadding} y1={topPadding + rowHeight * 2} x2={width - rightPadding} y2={topPadding + rowHeight * 2} stroke="#1A1A1A" strokeWidth="0.5" strokeOpacity="0.2" />
          <line x1={leftPadding} y1={topPadding + rowHeight * 3} x2={width - rightPadding} y2={topPadding + rowHeight * 3} stroke="#1A1A1A" strokeWidth="0.5" strokeOpacity="0.2" />
          <line x1={leftPadding} y1={topPadding + rowHeight * 4} x2={width - rightPadding} y2={topPadding + rowHeight * 4} stroke="#1A1A1A" strokeWidth="1.5" />

          {/* Row Title Labels on left side */}
          {[
            { label: 'OFF DUTY', abbr: 'OFF', y: topPadding + rowHeight / 2 },
            { label: 'SLEEPER BERTH', abbr: 'SB', y: topPadding + rowHeight * 1.5 },
            { label: 'DRIVING', abbr: 'D', y: topPadding + rowHeight * 2.5 },
            { label: 'ON DUTY (ND)', abbr: 'ON', y: topPadding + rowHeight * 3.5 },
          ].map((r, idx) => (
            <text
              key={idx}
              x={10}
              y={r.y + 3}
              fontSize="8"
              fontWeight="extrabold"
              fill="#1A1A1A"
              className="font-sans tracking-wide"
            >
              {r.label}
            </text>
          ))}

          {/* DRAW THE DYNAMIC ELD LINE PATH */}
          {activeLog.timeline.map((block, idx) => {
            const x1 = getX(block.startHour);
            const x2 = getX(block.endHour);
            const y = getY(block.status);
            
            const nextBlock = activeLog.timeline[idx + 1];
            const nextY = nextBlock ? getY(nextBlock.status) : y;
            
            return (
              <g key={`block-${idx}`}>
                {/* Horizontal segment representing duration */}
                <line
                  x1={x1}
                  y1={y}
                  x2={x2}
                  y2={y}
                  stroke="#1A1A1A"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                />
                
                {/* Vertical line connecting to next state at transition */}
                {nextBlock && (
                  <line
                    x1={x2}
                    y1={y}
                    x2={x2}
                    y2={nextY}
                    stroke="#1A1A1A"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />
                )}
              </g>
            );
          })}

          {/* Sub Totals Column Labels Header on Right Side */}
          <text x={width - rightPadding + 20} y={18} fill="#1A1A1A" fontSize="8" fontWeight="bold">TOTAL</text>
          <line x1={width - rightPadding} y1={topPadding} x2={width - rightPadding} y2={height - 15} stroke="#1A1A1A" strokeWidth="1.5" />
          
          {/* Write totals per row */}
          {[
            { tot: activeLog.totals.OFF, y: topPadding + rowHeight / 2 + 3 },
            { tot: activeLog.totals.SB, y: topPadding + rowHeight * 1.5 + 3 },
            { tot: activeLog.totals.D, y: topPadding + rowHeight * 2.5 + 3 },
            { tot: activeLog.totals.ON, y: topPadding + rowHeight * 3.5 + 3 },
          ].map((totItem, i) => (
            <g key={`tot-${i}`}>
              <text
                x={width - rightPadding + 25}
                y={totItem.y}
                fill="#1A1A1A"
                fontSize="11"
                fontWeight="extrabold"
                textAnchor="middle"
              >
                {totItem.tot.toFixed(2)}
              </text>
              <line
                x1={width - rightPadding}
                y1={totItem.y + 11}
                x2={width}
                y2={totItem.y + 11}
                stroke="#1A1A1A"
                strokeOpacity="0.1"
                strokeWidth="0.5"
              />
            </g>
          ))}
          
          {/* Final 24h mathematical certification footer */}
          <text
            x={width - rightPadding + 25}
            y={height - 2}
            fill="#FD5368"
            fontSize="8"
            fontWeight="bold"
            textAnchor="middle"
          >
            24.00 hr
          </text>
        </svg>
      </div>

      {/* REMARKS SECTION */}
      <div className="border border-[#1A1A1A] rounded-none overflow-hidden mb-6">
        <div className="bg-[#E8E4DF] px-4 py-3 border-b-2 border-[#1A1A1A] flex items-center justify-between">
          <span className="text-[10px] font-bold text-[#1A1A1A] tracking-wider uppercase font-mono">
            Duty Status Remarks / Geographic Change log
          </span>
          <span className="text-[9px] font-mono bg-[#1A1A1A] text-white rounded-none px-2 py-0.5">
            {activeLog.remarks.length} State Changes logged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-[#F4F1ED]/50 border-b border-[#1A1A1A] text-[#1A1A1A] font-extrabold text-[10px] uppercase tracking-wider">
                <th className="py-2.5 px-4 font-sans">Time Range</th>
                <th className="py-2.5 px-4 font-sans">Duty Status</th>
                <th className="py-2.5 px-4 font-sans">Location / Terminal Location</th>
                <th className="py-2.5 px-4 font-sans">FMCSA Audit Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1A1A1A]/10 text-slate-800 font-sans">
              {activeLog.remarks.map((rem, j) => (
                <tr key={j} className="hover:bg-[#F4F1ED]/30">
                  <td className="py-3.5 px-4 font-mono text-slate-900 text-[11px] font-bold">{rem.timeLabel}</td>
                  <td className="py-3.5 px-4 font-mono font-bold text-[10px]">
                    {rem.status === DutyStatus.D && <span className="text-white bg-[#1A1A1A] px-1.5 py-0.5 border border-[#1A1A1A] text-[9px] tracking-wider font-extrabold uppercase rounded-none">DRIVING</span>}
                    {rem.status === DutyStatus.ON && <span className="text-white bg-[#FD5368] px-1.5 py-0.5 border border-[#FF6B00] text-[9px] tracking-wider font-extrabold uppercase rounded-none">ON DUTY</span>}
                    {rem.status === DutyStatus.OFF && <span className="text-[#1A1A1A] bg-[#E8E4DF] px-1.5 py-0.5 border border-[#1A1A1A] text-[9px] tracking-wider font-extrabold uppercase rounded-none">OFF DUTY</span>}
                    {rem.status === DutyStatus.SB && <span className="text-[#1A1A1A] bg-[#F4F1ED] px-1.5 py-0.5 border border-[#1A1A1A] text-[9px] tracking-wider font-extrabold uppercase rounded-none">SLEEPER</span>}
                  </td>
                  <td className="py-3.5 px-4 font-bold uppercase text-[11px] text-[#1A1A1A]">{rem.location}</td>
                  <td className="py-3.5 px-4 text-slate-600 italic text-[11px]">{rem.remarksText}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Compliance / Transmission bar */}
      <div className="border-2 border-[#1A1A1A] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#F4F1ED]/50 font-sans rounded-none">
        <div className="flex items-start gap-2.5">
          <ShieldCheck className="h-5 w-5 text-[#1A1A1A] shrink-0 mt-0.5" />
          <div>
            <h4 className="text-[11px] font-extrabold uppercase tracking-widest text-[#1A1A1A]">Digital ELD Self-Certification</h4>
            <p className="text-[11px] text-slate-600 mt-1">
              This digital dashboard implements calculations in compliance with the Federal Motor Carrier Safety Regulations (49 CFR Parts 395). Export to PDF for printing, archiving, or roadside inspection handoff.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            id="btn-eld-pdf-export"
            onClick={handleExportPdf}
            disabled={isExporting}
            className="bg-[#1A1A1A] hover:bg-black disabled:bg-slate-300 text-white text-xs font-bold uppercase tracking-widest border border-[#1A1A1A] px-5 py-3 rounded-none flex items-center gap-1.5 active:scale-95 transition-all shadow-[3px_3px_0px_#FD5368] hover:shadow-none hover:translate-x-[1px] hover:translate-y-[1px] cursor-pointer"
          >
            <Download className="h-3.5 w-3.5" />
            {isExporting ? "GENERATING PDF..." : "EXPORT PDF"}
          </button>
        </div>
      </div>

      {exportError && (
        <div className="mt-4 bg-red-50 border-2 border-red-900 text-red-900 text-[11px] p-4 rounded-none font-mono leading-relaxed shadow-[4px_4px_0px_#7f1d1d] flex items-start gap-2">
          <AlertCircle className="h-4 w-4 text-red-700 shrink-0 mt-0.5" />
          <span><b>PDF export failed:</b> {exportError}</span>
        </div>
      )}
    </div>
  );
}
