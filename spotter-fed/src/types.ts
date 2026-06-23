/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export enum DutyStatus {
  OFF = 'OFF', // Off Duty
  SB = 'SB',   // Sleeper Berth
  D = 'D',     // Driving
  ON = 'ON'    // On Duty (Not Driving)
}

export interface GeocodedLocation {
  label: string;
  city: string;
  state: string;
  lat: number;
  lng: number;
}

export interface RouteLeg {
  from: GeocodedLocation;
  to: GeocodedLocation;
  distanceMiles: number;
  durationHours: number;
}

export interface TripInputs {
  currentLocation: string;
  pickupLocation: string;
  dropoffLocation: string;
  currentCycleUsed: number;
  carrierName: string;
  tractorNumber: string;
  trailerNumber: string;
  startTime: string; // ISO string or format
}

export interface ItineraryItem {
  id: string;
  status: DutyStatus;
  activityName: string; // e.g. "Pre-Trip Inspection", "Driving", "Fueling Stop", "Sleeper Berth Reset"
  locationName: string; // e.g. "Topeka, KS"
  startTime: string;    // ISO string
  endTime: string;      // ISO string
  durationHours: number;
  distanceMiles: number;
  coordinates: [number, number]; // [lat, lng]
  remarks?: string;
}

export interface DailyLogSheet {
  dateString: string; // e.g. "2026-06-21"
  dateLabel: string;  // e.g. "Sunday, Jun 21, 2026"
  totalMilesDriven: number;
  tractorNumber: string;
  trailerNumber: string;
  carrierName: string;
  
  // Array of status blocks for this 24-hour day (00:00 to 24:00)
  // Each block has a start/end as fraction of hours in the day (0 to 24)
  timeline: {
    status: DutyStatus;
    startHour: number; // 0 to 24
    endHour: number;   // 0 to 24
    locationName: string;
    remarks?: string;
  }[];
  
  // Calculated totals for the 4 rows (sums must total 24.0)
  totals: {
    OFF: number;
    SB: number;
    D: number;
    ON: number;
  };
  
  // Remarks for status transitions
  remarks: {
    timeLabel: string; // e.g., "08:15 AM"
    status: DutyStatus;
    location: string;
    remarksText: string;
  }[];
}

export interface TripGenerationResult {
  current: GeocodedLocation;
  pickup: GeocodedLocation;
  dropoff: GeocodedLocation;
  routeCoordinates: [number, number][];
  legs: RouteLeg[];
  totalDistanceMiles: number;
  totalDurationHours: number;
  itinerary: ItineraryItem[];
  dailyLogs: DailyLogSheet[];
}
