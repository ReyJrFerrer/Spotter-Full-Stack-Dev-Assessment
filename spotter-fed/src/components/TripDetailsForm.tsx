/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { TripInputs } from '../types';
import { MapPin, Truck, Compass, Calendar, Clock, RotateCcw } from 'lucide-react';
import LocationAutocomplete from './LocationAutocomplete';
import { US_CITIES } from '../constants/usCities';

interface Props {
  onSubmit: (inputs: TripInputs) => void;
  isLoading: boolean;
}

const PRESET_TRIPS = [
  { name: "La to Vegas Corridor", curr: "Los Angeles, CA", pick: "Las Vegas, NV", drop: "Salt Lake City, UT" },
  { name: "Midwest Route", curr: "Chicago, IL", pick: "Denver, CO", drop: "Dallas, TX" },
  { name: "East Coast Carrier", curr: "Boston, MA", pick: "New York, NY", drop: "Atlanta, GA" }
];

const AUTOCOMPLETE_URL = `${(import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')}/api/locations/autocomplete/`;

export default function TripDetailsForm({ onSubmit, isLoading }: Props) {
  const [currentLocation, setCurrentLocation] = useState('Los Angeles, CA');
  const [pickupLocation, setPickupLocation] = useState('Las Vegas, NV');
  const [dropoffLocation, setDropoffLocation] = useState('Salt Lake City, UT');
  const [currentCycleUsed, setCurrentCycleUsed] = useState(15.5);
  const [carrierName, setCarrierName] = useState('Swift Logistical Transit Group');
  const [tractorNumber, setTractorNumber] = useState('TRK-9801C');
  const [trailerNumber, setTrailerNumber] = useState('TRL-552A');
  const [startTime, setStartTime] = useState(() => {
    const d = new Date();
    // format as yyyy-MM-ddTHH:mm
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${dd}T08:00`;
  });

  const handlePreset = (preset: typeof PRESET_TRIPS[0]) => {
    setCurrentLocation(preset.curr);
    setPickupLocation(preset.pick);
    setDropoffLocation(preset.drop);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      currentLocation,
      pickupLocation,
      dropoffLocation,
      currentCycleUsed,
      carrierName,
      tractorNumber,
      trailerNumber,
      startTime: new Date(startTime).toISOString()
    });
  };

  return (
    <div id="trip-input-dashboard" className="bg-white border-2 border-[#1A1A1A] p-6 shadow-[6px_6px_0px_#1A1A1A] transition-all">
      <div className="flex items-center gap-2 mb-6 border-b-2 border-[#1A1A1A] pb-4">
        <Truck className="h-5 w-5 text-[#FD5368]" />
        <h2 className="text-sm font-bold uppercase tracking-widest text-[#1A1A1A]">1. Dispatch Parameters & HOS Setup</h2>
      </div>

      <div className="mb-6">
        <label className="text-[10px] font-bold text-[#1A1A1A] uppercase tracking-wider block mb-2 opacity-70">Preset Corridors:</label>
        <div className="flex flex-wrap gap-2">
          {PRESET_TRIPS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              id={`preset-btn-${idx}`}
              onClick={() => handlePreset(p)}
              className="text-xs bg-[#E8E4DF] hover:bg-[#1A1A1A] hover:text-white border border-[#1A1A1A] text-[#1A1A1A] font-bold py-1.5 px-4 transition-all duration-200 cursor-pointer text-center"
            >
              {p.name.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleFormSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Current Location */}
          <LocationAutocomplete
            id="input-current-loc"
            label="Current Base Location"
            icon={<Compass className="h-4 w-4 text-[#FD5368]" />}
            value={currentLocation}
            onChange={setCurrentLocation}
            placeholder="City, State (e.g. Los Angeles, CA)"
            apiUrl={AUTOCOMPLETE_URL}
            staticOptions={US_CITIES}
          />

          {/* Current Cycle Hours */}
          <div>
            <label htmlFor="input-cycle-used" className="text-[10px] font-bold text-[#1A1A1A] uppercase tracking-widest block mb-1">
              Current Cycle Clock Used (hrs)
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Clock className="h-4 w-4 text-[#FD5368]" />
              </span>
              <input
                id="input-cycle-used"
                type="number"
                step="0.25"
                min="0"
                max="70"
                required
                value={currentCycleUsed}
                onChange={(e) => setCurrentCycleUsed(Math.max(0, parseFloat(e.target.value) || 0))}
                className="w-full pl-10 pr-3 py-2.5 text-sm bg-[#F4F1ED]/40 hover:bg-[#F4F1ED]/65 focus:bg-white border border-[#1A1A1A] text-[#1A1A1A] font-mono rounded-none outline-none transition-all focus:ring-1 focus:ring-[#1A1A1A]"
              />
            </div>
            <p className="text-[10px] text-[#1A1A1A]/60 font-medium mt-1">Deducted from the FMCSA 70-hour/8-day clock limit</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Pickup Location */}
          <LocationAutocomplete
            id="input-pickup-loc"
            label="Pickup Point"
            icon={<MapPin className="h-4 w-4 text-[#FD5368]" />}
            value={pickupLocation}
            onChange={setPickupLocation}
            placeholder="City, State (e.g. Las Vegas, NV)"
            apiUrl={AUTOCOMPLETE_URL}
            staticOptions={US_CITIES}
          />

          {/* Dropoff Location */}
          <LocationAutocomplete
            id="input-dropoff-loc"
            label="Drop-off Point"
            icon={<MapPin className="h-4 w-4 text-[#FD5368]" />}
            value={dropoffLocation}
            onChange={setDropoffLocation}
            placeholder="City, State (e.g. Salt Lake City, UT)"
            apiUrl={AUTOCOMPLETE_URL}
            staticOptions={US_CITIES}
          />
        </div>

        {/* Departure Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 border-t-2 border-[#1A1A1A]/10 pt-5 mt-2">
          <div>
            <label htmlFor="input-carrier" className="text-[10px] font-bold text-[#1A1A1A] uppercase tracking-widest block mb-1">Carrier Name</label>
            <input
              id="input-carrier"
              type="text"
              required
              value={carrierName}
              onChange={(e) => setCarrierName(e.target.value)}
              className="w-full px-3 py-2.5 text-xs bg-[#F4F1ED]/40 border border-[#1A1A1A] text-[#1A1A1A] rounded-none outline-none focus:bg-white font-medium"
            />
          </div>

          <div>
            <label htmlFor="input-tractor" className="text-[10px] font-bold text-[#1A1A1A] uppercase tracking-widest block mb-1">Tractor / Truck #</label>
            <input
              id="input-tractor"
              type="text"
              required
              value={tractorNumber}
              onChange={(e) => setTractorNumber(e.target.value)}
              className="w-full px-3 py-2.5 text-xs bg-[#F4F1ED]/40 border border-[#1A1A1A] text-[#1A1A1A] rounded-none outline-none focus:bg-white font-mono"
            />
          </div>

          <div>
            <label htmlFor="input-trailer" className="text-[10px] font-bold text-[#1A1A1A] uppercase tracking-widest block mb-1">Trailer #</label>
            <input
              id="input-trailer"
              type="text"
              required
              value={trailerNumber}
              onChange={(e) => setTrailerNumber(e.target.value)}
              className="w-full px-3 py-2.5 text-xs bg-[#F4F1ED]/40 border border-[#1A1A1A] text-[#1A1A1A] rounded-none outline-none focus:bg-white font-mono"
            />
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-t-2 border-[#1A1A1A] pt-5">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-[#FD5368]" />
            <input
              id="input-start-date"
              type="datetime-local"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="text-xs font-bold text-[#1A1A1A] bg-[#E8E4DF] border border-[#1A1A1A] rounded-none px-3 py-2 outline-none font-mono"
            />
          </div>

          <button
            id="btn-dispatch-route"
            type="submit"
            disabled={isLoading}
            className="w-full md:w-auto bg-[#1A1A1A] hover:bg-black text-white font-bold uppercase tracking-widest text-xs py-3.5 px-6 border border-[#1A1A1A] hover:border-black transition-all shadow-[4px_4px_0px_#FD5368] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px] duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analyzing Route & Resets...
              </>
            ) : (
              <>
                <Compass className="h-4 w-4" />
                Calculate Route & Generate Logs
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
