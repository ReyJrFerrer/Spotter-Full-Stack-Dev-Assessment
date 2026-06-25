/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { ItineraryItem, DutyStatus } from '../types';
import { Clock, Navigation, Compass, Calendar, Coffee, Moon, Fuel, ClipboardCheck, ArrowRight, Globe2 } from 'lucide-react';

interface Props {
  itinerary: ItineraryItem[];
  totalDistance: number;
  totalDurationHours: number;
  tripTimezone: string;
}

const getStatusBadge = (status: DutyStatus) => {
  switch (status) {
    case DutyStatus.OFF:
      return <span className="border border-[#1A1A1A] bg-[#E8E4DF] text-[#1A1A1A] font-extrabold text-[9px] tracking-wider px-1.5 py-0.5 rounded-none">OFF DUTY</span>;
    case DutyStatus.SB:
      return <span className="border border-[#1A1A1A] bg-[#F4F1ED] text-[#1A1A1A] font-extrabold text-[9px] tracking-wider px-1.5 py-0.5 rounded-none">SLEEPER</span>;
    case DutyStatus.D:
      return <span className="border border-[#1A1A1A] bg-[#1A1A1A] text-[#FFFFFF] font-extrabold text-[9px] tracking-wider px-1.5 py-0.5 rounded-none">DRIVING</span>;
    case DutyStatus.ON:
      return <span className="border border-[#1A1A1A] bg-[#FD5368] text-white font-extrabold text-[9px] tracking-wider px-1.5 py-0.5 rounded-none">ON DUTY</span>;
  }
};

const getEventIcon = (status: DutyStatus, name: string) => {
  const norm = name.toLowerCase();
  if (norm.includes("inspect") || norm.includes("pre-trip") || norm.includes("inspec")) {
    return <ClipboardCheck className="h-4 w-4 text-[#FD5368]" />;
  }
  if (norm.includes("fuel")) {
    return <Fuel className="h-4 w-4 text-[#FF6B00]" />;
  }
  if (norm.includes("30-min") || norm.includes("break") || norm.includes("rest")) {
    return <Coffee className="h-4 w-4 text-[#FD5368]" />;
  }
  if (norm.includes("reset") || norm.includes("10-hour") || status === DutyStatus.SB) {
    return <Moon className="h-4 w-4 text-[#FD5368]" />;
  }
  if (status === DutyStatus.D) {
    return <Navigation className="h-4 w-4 text-[#FD5368]" />;
  }
  return <Compass className="h-4 w-4 text-[#FD5368]" />;
};

export default function ItineraryPanel({ itinerary, totalDistance, totalDurationHours, tripTimezone }: Props) {
  return (
    <div id="itinerary-timeline-dashboard" className="bg-white border-2 border-[#1A1A1A] p-6 shadow-[6px_6px_0px_#133658] flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b-2 border-[#1A1A1A] pb-4 mb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-widest text-[#1A1A1A] flex items-center gap-2">
            <Clock className="h-5 w-5 text-[#FD5368]" />
            3. Chronological Dispatch Itinerary
          </h2>
          <p className="text-[10px] uppercase font-bold text-[#1A1A1A]/60 mt-1 flex items-center gap-1">
            <Globe2 className="h-3 w-3" />
            All times anchored to {tripTimezone}
          </p>
        </div>
        
        {/* Rapid stats banner */}
        <div className="flex items-center gap-3 bg-[#E8E4DF] border border-[#1A1A1A] p-2 px-3 text-xs font-mono font-bold text-[#1A1A1A]">
          <div>
            MILES: <span>{totalDistance} mi</span>
          </div>
          <div className="w-px h-3 bg-[#1A1A1A]/20"></div>
          <div>
            DRIVE EST: <span className="text-[#FD5368]">{totalDurationHours} hrs</span>
          </div>
        </div>
      </div>

      {/* Itinerary Chrono list */}
      <div className="flex-1 overflow-y-auto max-h-[500px] pr-2 space-y-4">
        {itinerary.length === 0 ? (
          <div className="text-center py-10 text-slate-400 text-xs uppercase tracking-widest font-bold">
            Submit trip parameters to calculate timeline.
          </div>
        ) : (
          <div className="relative border-l-2 border-dashed border-[#1A1A1A] ml-4 pl-6 space-y-6">
            {itinerary.map((item, index) => {
              const startD = new Date(item.startTime);
              const endD = new Date(item.endTime);
              const timeOptions: Intl.DateTimeFormatOptions = {
                hour: '2-digit',
                minute: '2-digit',
                timeZone: tripTimezone,
              };
              const dateOptions: Intl.DateTimeFormatOptions = {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                timeZone: tripTimezone,
              };
              const timeRangeStr = `${startD.toLocaleTimeString([], timeOptions)} - ${endD.toLocaleTimeString([], timeOptions)}`;
              const dayStr = startD.toLocaleDateString([], dateOptions);

              return (
                <div key={item.id} id={`itinerary-item-${index}`} className="relative group">
                  {/* Timeline Node Badge Icon */}
                  <span className="absolute -left-[35px] top-0.5 bg-white border border-[#1A1A1A] p-1 flex items-center justify-center z-20 group-hover:bg-[#E8E4DF] transition-colors rounded-none">
                    {getEventIcon(item.status, item.activityName)}
                  </span>
                  
                  {/* Itinerary Item card */}
                  <div className="bg-[#F4F1ED]/30 hover:bg-white rounded-none border border-[#1A1A1A]/30 hover:border-[#1A1A1A] p-4 transition-all duration-200">
                    <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <h4 className="font-extrabold text-xs uppercase tracking-wider text-[#1A1A1A] leading-tight">
                          {item.activityName}
                        </h4>
                        {getStatusBadge(item.status)}
                      </div>
                      
                      <div className="text-[10px] font-mono font-bold text-right shrink-0">
                        <span className="bg-[#E8E4DF] border border-[#1A1A1A]/20 text-[#1A1A1A] px-1.5 py-0.5 mr-1 uppercase">
                          {dayStr}
                        </span>
                        <span className="text-slate-800">{timeRangeStr}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-[#1A1A1A]/70 mb-2">
                      <Compass className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                      <span className="font-bold underline uppercase text-[10px]">{item.locationName}</span>
                    </div>

                    {item.status === DutyStatus.D && item.distanceMiles > 0 && (
                      <div className="flex items-center gap-1.5 text-[9px] font-extrabold uppercase tracking-widest bg-emerald-50 text-emerald-900 border border-emerald-900/30 px-2.5 py-1 w-fit mb-2">
                        <span>Distance: {Math.round(item.distanceMiles)} miles</span>
                        <ArrowRight className="h-3 w-3" />
                        <span>Duration: {item.durationHours} hrs</span>
                      </div>
                    )}

                    {item.remarks && (
                      <p className="text-[11px] italic text-slate-500 border-l-2 border-[#1A1A1A] pl-2 mt-2 leading-relaxed">
                        {item.remarks}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
