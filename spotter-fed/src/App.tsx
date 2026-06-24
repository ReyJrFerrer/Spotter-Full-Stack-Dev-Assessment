/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { TripInputs, TripGenerationResult } from './types';
import { mapBackendResponse, mergeUserMetadata } from './utils/apiTransform';
import TripDetailsForm from './components/TripDetailsForm';
import CalculatedMap from './components/CalculatedMap';
import ItineraryPanel from './components/ItineraryPanel';
import EldLogSheets from './components/EldLogSheets';
import { ShieldCheck, Compass, AlertCircle } from 'lucide-react';

export default function App() {
  const [result, setResult] = useState<TripGenerationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Trigger an initial automatic calculation on mount to show beautiful default data
  useEffect(() => {
    handleCalculate({
      currentLocation: 'Los Angeles, CA',
      pickupLocation: 'Las Vegas, NV',
      dropoffLocation: 'Salt Lake City, UT',
      currentCycleUsed: 15.5,
      carrierName: 'Swift Logistical Transit Group',
      tractorNumber: 'TRK-9801C',
      trailerNumber: 'TRL-552A',
      startTime: new Date().toISOString()
    });
  }, []);

  const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

  const handleCalculate = async (inputs: TripInputs) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const response = await fetch(`${API_BASE}/api/trips/generate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_location: inputs.currentLocation,
          pickup_location: inputs.pickupLocation,
          dropoff_location: inputs.dropoffLocation,
          current_cycle_used_hrs: inputs.currentCycleUsed,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        const message =
          data.error || (typeof data === 'object' ? JSON.stringify(data) : "Route calculation failed.");
        throw new Error(message);
      }

      const mapped = mapBackendResponse(data);
      const merged = mergeUserMetadata(
        mapped,
        inputs.carrierName,
        inputs.tractorNumber,
        inputs.trailerNumber
      );
      setResult(merged);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Network error trying to connect to dispatch server. Please ensure the backend server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F1ED] flex flex-col text-[#1A1A1A]">
      
      {/* 1. Header Navigation Banner: Editorial Layout */}
      <header className="bg-[#F4F1ED] text-[#1A1A1A] border-b-2 border-[#1A1A1A] sticky top-0 z-50 py-5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row md:items-baseline md:justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-serif italic font-black tracking-tighter">
              ELD.01 <span className="text-xs font-sans not-italic uppercase tracking-[0.25em] font-bold ml-2 md:ml-4 opacity-70">Route & Log Generator</span>
            </h1>
            <p className="text-[10px] uppercase tracking-widest font-bold opacity-60 mt-1">Automated Commercial Truck Routing & Certified Daily Log System</p>
          </div>

          <div className="flex items-center gap-1.5 bg-[#E8E4DF] text-[#1A1A1A] px-3 py-1.5 border border-[#1A1A1A] shadow-[2px_2px_0px_#1A1A1A] text-[10px] uppercase tracking-widest font-extrabold">
            <span>ROUTING ENGINE: OSRM + NOMINATIM</span>
          </div>
        </div>
      </header>

      {/* 2. Main Content Board Wrap */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Error Callout */}
        {errorMsg && (
          <div className="bg-red-50 border-2 border-red-900 rounded-none p-4 text-sm text-red-900 flex items-start gap-2.5 animate-fade-in shadow-[4px_4px_0px_#7f1d1d]">
            <AlertCircle className="h-5 w-5 text-red-700 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold mb-0.5 font-serif italic">Calculation Interrupted</h4>
              <p className="text-xs leading-relaxed">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* Top: Input form */}
        <TripDetailsForm onSubmit={handleCalculate} isLoading={isLoading} />

        {/* Bottom Results: Map + Itinerary side by side, ELD full-width below */}
        {result ? (
          <div className="space-y-8">
            {/* Top Row: Map (7-col) + Itinerary (5-col), equal height */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
              <div className="lg:col-span-7">
                <CalculatedMap
                  start={result.current}
                  pickup={result.pickup}
                  dropoff={result.dropoff}
                  itinerary={result.itinerary}
                  routeCoordinates={result.routeCoordinates}
                />
              </div>
              <div className="lg:col-span-5">
                <ItineraryPanel
                  itinerary={result.itinerary}
                  totalDistance={result.totalDistanceMiles}
                  totalDurationHours={result.totalDurationHours}
                />
              </div>
            </div>

            {/* Bottom Row: ELD Logs — full width */}
            <EldLogSheets dailyLogs={result.dailyLogs} />
          </div>
        ) : (
          <div className="text-center py-20 bg-white border border-[#1A1A1A] hover:shadow-none shadow-[4px_4px_0px_#1A1A1A] p-6">
            <Compass className="h-10 w-10 text-slate-500 mx-auto mb-3 animate-spin" />
            <h3 className="font-serif italic font-bold text-lg text-slate-800 mb-1">Starting dispatch simulator...</h3>
            <p className="text-xs text-slate-500">Loading default truck configuration and routing database.</p>
          </div>
        )}

      </main>

      {/* 3. Footer branding */}
      <footer className="bg-[#1A1A1A] text-white/60 text-xs py-8 border-t-2 border-[#1A1A1A] mt-12 bg-cover">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <p>© 2026 E-DOT Dispatch Terminal. Certified in compliance with § 395.22, ELD requirements.</p>
          <div className="flex items-center gap-1.5 text-[11px] text-white/80">
            <ShieldCheck className="h-4 w-4 text-[#FF6B00]" />
            <span className="font-bold uppercase tracking-widest text-[9px]">Secure E-DOT Inspect Dataset Transfer</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
