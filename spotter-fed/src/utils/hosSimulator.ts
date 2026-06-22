/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { DutyStatus, GeocodedLocation, ItineraryItem, DailyLogSheet, RouteLeg, TripGenerationResult } from '../types';

/**
 * Rounds a number of hours to the nearest 15 minutes (0.25 hours).
 */
export function roundToQuarterHour(hours: number): number {
  return Math.round(hours * 4) / 4;
}

/**
 * Formats a date format to local time representation.
 */
export function formatTimeLabel(date: Date): string {
  let hh = date.getHours();
  const mm = date.getMinutes();
  const ampm = hh >= 12 ? 'PM' : 'AM';
  hh = hh % 12;
  hh = hh ? hh : 12; // 0 should be 12
  const mmStr = mm < 10 ? '0' + mm : mm;
  return `${hh}:${mmStr} ${ampm}`;
}

export function formatDateLabel(date: Date): string {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${days[date.getDay()]}, ${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

export function formatDateString(date: Date): string {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

/**
 * Helper to interpolate between two coordinates based on fraction.
 */
function interpolateCoordinates(
  coord1: [number, number],
  coord2: [number, number],
  fraction: number
): [number, number] {
  const lat = coord1[0] + (coord2[0] - coord1[0]) * fraction;
  const lng = coord1[1] + (coord2[1] - coord1[1]) * fraction;
  return [lat, lng];
}

/**
 * HOS Simulator Engine
 */
export function simulateTrip(
  current: GeocodedLocation,
  pickup: GeocodedLocation,
  dropoff: GeocodedLocation,
  currentCycleUsed: number,
  startTimeIso: string,
  carrierName: string,
  tractorNumber: string,
  trailerNumber: string,
  routeCoordinates: [number, number][]
): TripGenerationResult {
  
  const startDateTime = new Date(startTimeIso);
  let currentTime = new Date(startDateTime.getTime());
  
  // Driving Speed average
  const AVERAGE_SPEED_MPH = 60;
  
  // Leg 1: Current to Pickup (Deadhead or Initial leg)
  // Let's estimate distance from coordinates or fallback
  const latDiff1 = pickup.lat - current.lat;
  const lngDiff1 = pickup.lng - current.lng;
  const dist1 = Math.max(20, Math.round(Math.sqrt(latDiff1 * latDiff1 + lngDiff1 * lngDiff1) * 55)); // rough estimate if not provided
  
  // Leg 2: Pickup to Dropoff (Loaded leg)
  const latDiff2 = dropoff.lat - pickup.lat;
  const lngDiff2 = dropoff.lng - pickup.lng;
  const dist2 = Math.max(30, Math.round(Math.sqrt(latDiff2 * latDiff2 + lngDiff2 * lngDiff2) * 55));
  
  const legs: RouteLeg[] = [
    { from: current, to: pickup, distanceMiles: dist1, durationHours: roundToQuarterHour(dist1 / AVERAGE_SPEED_MPH) },
    { from: pickup, to: dropoff, distanceMiles: dist2, durationHours: roundToQuarterHour(dist2 / AVERAGE_SPEED_MPH) }
  ];
  
  // Readjust duration to always be at least 0.25 hours
  legs[0].durationHours = Math.max(0.25, legs[0].durationHours);
  legs[1].durationHours = Math.max(0.25, legs[1].durationHours);
  
  const totalDistanceMiles = dist1 + dist2;
  const totalDurationHours = legs[0].durationHours + legs[1].durationHours;
  
  // Itinerary accumulation
  const itinerary: ItineraryItem[] = [];
  
  // Internal HOS Tracking state
  let accumDrivingToday = 0;              // limit: 11 hrs
  let elapsedDutyWindowToday = 0;          // limit: 14 hrs
  let continuousDrivingSinceBreak = 0;     // limit: 8 hrs
  let totalCycleHoursUsed = currentCycleUsed; // limit: 70 hrs (cumulative across trip)
  let milesSinceFueling = 0;
  
  let currentCoordinates: [number, number] = [current.lat, current.lng];
  
  let itemCounter = 1;
  const addItinerary = (
    status: DutyStatus,
    activityName: string,
    locationName: string,
    durationHours: number,
    distanceMiles: number,
    coords: [number, number],
    remarks?: string
  ) => {
    const sTime = new Date(currentTime.getTime());
    const endTimeMs = currentTime.getTime() + durationHours * 60 * 60 * 1000;
    currentTime = new Date(endTimeMs);
    const eTime = new Date(currentTime.getTime());
    
    itinerary.push({
      id: `item-${itemCounter++}`,
      status,
      activityName,
      locationName,
      startTime: sTime.toISOString(),
      endTime: eTime.toISOString(),
      durationHours,
      distanceMiles,
      coordinates: coords,
      remarks: remarks || `${activityName} in ${locationName}`
    });
    
    // Update clocks based on status
    if (status === DutyStatus.D) {
      accumDrivingToday += durationHours;
      continuousDrivingSinceBreak += durationHours;
      totalCycleHoursUsed += durationHours;
      elapsedDutyWindowToday += durationHours;
      milesSinceFueling += distanceMiles;
    } else if (status === DutyStatus.ON) {
      elapsedDutyWindowToday += durationHours;
      totalCycleHoursUsed += durationHours;
    } else if (status === DutyStatus.OFF || status === DutyStatus.SB) {
      // Off duty / Sleeper berth resets driving bounds if consecutive duration is at least 10h
      // For 30 min break, standard off-duty handles it
    }
  };
  
  // Trigger a 10 Hours HOS Daily Reset
  const triggerTenHourReset = (location: string, coords: [number, number], reason: string) => {
    addItinerary(
      DutyStatus.SB,
      "10-Hour Daily Reset Break",
      location,
      10.0,
      0,
      coords,
      `HOS Reset: 10 hrs consecutive Sleeper Berth (${reason})`
    );
    accumDrivingToday = 0;
    elapsedDutyWindowToday = 0;
    continuousDrivingSinceBreak = 0;
  };

  // Trigger a 30 Minutes Break
  const triggerThirtyMinBreak = (location: string, coords: [number, number], reason: string) => {
    addItinerary(
      DutyStatus.OFF,
      "30-Minute Rest Break",
      location,
      0.5,
      0,
      coords,
      `Mandatory 30-min consecutive break (${reason})`
    );
    continuousDrivingSinceBreak = 0;
  };

  // Trigger 34 Hours Restart
  const trigger34HourRestart = (location: string, coords: [number, number]) => {
    addItinerary(
      DutyStatus.OFF,
      "34-Hour Weekly Cycle Reset",
      location,
      34.0,
      0,
      coords,
      "34-Hour consecutive Off-Duty cycle reset (70-hour clock restored)"
    );
    totalCycleHoursUsed = 0; // reset commercial cycle
    accumDrivingToday = 0;
    elapsedDutyWindowToday = 0;
    continuousDrivingSinceBreak = 0;
  };
  
  // --- INITIATE TRIP ---
  
  // 1. Pre-trip inspection at Current location
  addItinerary(
    DutyStatus.ON,
    "Pre-Trip Inspection",
    `${current.city}, ${current.state}`,
    0.25, // 15 mins
    0,
    currentCoordinates,
    "15-min Post/Pre-Trip Commercial Vehicle Inspection"
  );
  
  // 2. Leg 1 Simulator: Current to Pickup
  let leg1MilesLeft = dist1;
  let leg1CoordsStart = [current.lat, current.lng] as [number, number];
  let leg1CoordsEnd = [pickup.lat, pickup.lng] as [number, number];
  
  while (leg1MilesLeft > 0) {
    // Check cycle hours left
    if (totalCycleHoursUsed >= 70) {
      const activeLoc = `${current.city}, ${current.state}`;
      trigger34HourRestart(activeLoc, leg1CoordsStart);
    }
    
    // Check daily duty window or driving limit
    if (elapsedDutyWindowToday >= 14 || accumDrivingToday >= 11) {
      const fractionDriven = (dist1 - leg1MilesLeft) / dist1;
      const currentLocCoords = interpolateCoordinates(leg1CoordsStart, leg1CoordsEnd, fractionDriven);
      const locLabel = `En-Route (${current.city} to ${pickup.city})`;
      triggerTenHourReset(locLabel, currentLocCoords, elapsedDutyWindowToday >= 14 ? "14hr Duty Limit" : "11hr Driving Limit");
    }
    
    // Check 8-hour consecutive driving limit
    if (continuousDrivingSinceBreak >= 8) {
      const fractionDriven = (dist1 - leg1MilesLeft) / dist1;
      const currentLocCoords = interpolateCoordinates(leg1CoordsStart, leg1CoordsEnd, fractionDriven);
      const locLabel = `En-Route Rest Area (${current.city} to ${pickup.city})`;
      triggerThirtyMinBreak(locLabel, currentLocCoords, "8-hour continuous driving threshold");
    }
    
    // Check fueling stops
    if (milesSinceFueling >= 1000) {
      const fractionDriven = (dist1 - leg1MilesLeft) / dist1;
      const currentLocCoords = interpolateCoordinates(leg1CoordsStart, leg1CoordsEnd, fractionDriven);
      addItinerary(
        DutyStatus.ON,
        "Commercial Vehicle Fueling Stop",
        `En-Route Truck Plaza`,
        0.5, // 30-min hook for fueling
        0,
        currentLocCoords,
        "Refueling commercial vehicle"
      );
      milesSinceFueling = 0;
    }
    
    // Determine driving step length
    // Drive at most till next limit, or 2 hours
    const maxDrivingHoursLeftToday = 11 - accumDrivingToday;
    const maxDutyHoursLeftToday = 14 - elapsedDutyWindowToday;
    const maxDrivingHoursLeftBreak = 8 - continuousDrivingSinceBreak;
    
    const maxHoursPossible = Math.min(2.0, maxDrivingHoursLeftToday, maxDutyHoursLeftToday, maxDrivingHoursLeftBreak);
    
    if (maxHoursPossible <= 0) {
      // If we are strictly blocked, we must take a reset
      const fractionDriven = (dist1 - leg1MilesLeft) / dist1;
      const currentLocCoords = interpolateCoordinates(leg1CoordsStart, leg1CoordsEnd, fractionDriven);
      const locLabel = `En-Route Safety Stop`;
      triggerTenHourReset(locLabel, currentLocCoords, "Safety Threshold");
      continue;
    }
    
    const milesPotential = maxHoursPossible * AVERAGE_SPEED_MPH;
    const milesToDrive = Math.min(leg1MilesLeft, milesPotential);
    const drivingTimeHours = roundToQuarterHour(milesToDrive / AVERAGE_SPEED_MPH);
    
    const resolvedHours = drivingTimeHours > 0 ? drivingTimeHours : 0.25;
    const fractionStart = (dist1 - leg1MilesLeft) / dist1;
    leg1MilesLeft -= milesToDrive;
    const fractionEnd = (dist1 - leg1MilesLeft) / dist1;
    
    const midpointCoords = interpolateCoordinates(leg1CoordsStart, leg1CoordsEnd, (fractionStart + fractionEnd) / 2);
    
    addItinerary(
      DutyStatus.D,
      "Driving",
      `I-15 Corridor (En Route)`,
      resolvedHours,
      milesToDrive,
      midpointCoords,
      `Driving Commercial Truck en route to Pickup (${Math.round(milesToDrive)} miles)`
    );
  }
  
  // Set position to Pickup
  currentCoordinates = [pickup.lat, pickup.lng];
  
  // Mandatory 1-hour loading/inspection at Pickup
  // Check if we can schedule it today or need reset first
  if (elapsedDutyWindowToday >= 14) {
    triggerTenHourReset(`${pickup.city}, ${pickup.state}`, currentCoordinates, "14h limit prior to loading");
  }
  
  addItinerary(
    DutyStatus.ON,
    "Cargo Loading & Inspection",
    `${pickup.city}, ${pickup.state}`,
    1.0, // 1h loading
    0,
    currentCoordinates,
    "Scheduled 1-hour Cargo Loading, Securement and Manifest Inspection"
  );
  
  // 3. Leg 2 Simulator: Pickup to Dropoff
  let leg2MilesLeft = dist2;
  let leg2CoordsStart = [pickup.lat, pickup.lng] as [number, number];
  let leg2CoordsEnd = [dropoff.lat, dropoff.lng] as [number, number];
  
  while (leg2MilesLeft > 0) {
    // Check cycle hours left
    if (totalCycleHoursUsed >= 70) {
      trigger34HourRestart(`${pickup.city}, ${pickup.state}`, leg2CoordsStart);
    }
    
    // Check daily duty window or driving limit
    if (elapsedDutyWindowToday >= 14 || accumDrivingToday >= 11) {
      const fractionDriven = (dist2 - leg2MilesLeft) / dist2;
      const currentLocCoords = interpolateCoordinates(leg2CoordsStart, leg2CoordsEnd, fractionDriven);
      const locLabel = `En-Route (${pickup.city} to ${dropoff.city})`;
      triggerTenHourReset(locLabel, currentLocCoords, elapsedDutyWindowToday >= 14 ? "14hr Duty Limit" : "11hr Driving Limit");
    }
    
    // Check 8-hour consecutive driving limit
    if (continuousDrivingSinceBreak >= 8) {
      const fractionDriven = (dist2 - leg2MilesLeft) / dist2;
      const currentLocCoords = interpolateCoordinates(leg2CoordsStart, leg2CoordsEnd, fractionDriven);
      const locLabel = `En-Route Safety Rest Stop`;
      triggerThirtyMinBreak(locLabel, currentLocCoords, "8-hour continuous driving threshold");
    }
    
    // Check fueling stops
    if (milesSinceFueling >= 1000) {
      const fractionDriven = (dist2 - leg2MilesLeft) / dist2;
      const currentLocCoords = interpolateCoordinates(leg2CoordsStart, leg2CoordsEnd, fractionDriven);
      addItinerary(
        DutyStatus.ON,
        "Commercial Vehicle Fueling Stop",
        `En-Route Plaza`,
        0.5,
        0,
        currentLocCoords,
        "Refueling commercial vehicle"
      );
      milesSinceFueling = 0;
    }
    
    // Determine driving step length
    const maxDrivingHoursLeftToday = 11 - accumDrivingToday;
    const maxDutyHoursLeftToday = 14 - elapsedDutyWindowToday;
    const maxDrivingHoursLeftBreak = 8 - continuousDrivingSinceBreak;
    
    const maxHoursPossible = Math.min(2.0, maxDrivingHoursLeftToday, maxDutyHoursLeftToday, maxDrivingHoursLeftBreak);
    
    if (maxHoursPossible <= 0) {
      const fractionDriven = (dist2 - leg2MilesLeft) / dist2;
      const currentLocCoords = interpolateCoordinates(leg2CoordsStart, leg2CoordsEnd, fractionDriven);
      const locLabel = `En-Route Safety Stop`;
      triggerTenHourReset(locLabel, currentLocCoords, "Safety Threshold");
      continue;
    }
    
    const milesPotential = maxHoursPossible * AVERAGE_SPEED_MPH;
    const milesToDrive = Math.min(leg2MilesLeft, milesPotential);
    const drivingTimeHours = roundToQuarterHour(milesToDrive / AVERAGE_SPEED_MPH);
    
    const resolvedHours = drivingTimeHours > 0 ? drivingTimeHours : 0.25;
    const fractionStart = (dist2 - leg2MilesLeft) / dist2;
    leg2MilesLeft -= milesToDrive;
    const fractionEnd = (dist2 - leg2MilesLeft) / dist2;
    
    const midpointCoords = interpolateCoordinates(leg2CoordsStart, leg2CoordsEnd, (fractionStart + fractionEnd) / 2);
    
    addItinerary(
      DutyStatus.D,
      "Driving",
      `Highway Interstate corridor`,
      resolvedHours,
      milesToDrive,
      midpointCoords,
      `Driving Commercial Truck loaded, en route to Destination (${Math.round(milesToDrive)} miles)`
    );
  }
  
  // Set position to Dropoff
  currentCoordinates = [dropoff.lat, dropoff.lng];
  
  // Mandatory 1-hour unload and post-trip at Dropoff
  if (elapsedDutyWindowToday >= 14) {
    triggerTenHourReset(`${dropoff.city}, ${dropoff.state}`, currentCoordinates, "14h limit prior to unloading");
  }
  
  addItinerary(
    DutyStatus.ON,
    "Cargo Unloading & Post-Trip Inspection",
    `${dropoff.city}, ${dropoff.state}`,
    1.0, // 1h loading
    0,
    currentCoordinates,
    "Cargo discharge and final Post-Trip vehicle evaluation"
  );
  
  // --- SEGMENT INTO GREGORIAN 24-HOUR DAILY LOGS ---
  // We need to partition the detailed itinerary into daily sheets starting at 00:00 (Midnight) and ending at 24:00 (Midnight)
  const dailyLogs: DailyLogSheet[] = [];
  
  const tripStartMs = startDateTime.getTime();
  const tripEndMs = currentTime.getTime();
  
  // Find all Gregorian calendar dates of interest, starting from the day of departure to the final arrival
  const currentDateRef = new Date(startDateTime.getFullYear(), startDateTime.getMonth(), startDateTime.getDate());
  const endDateRef = new Date(currentTime.getFullYear(), currentTime.getMonth(), currentTime.getDate());
  
  // Iterate date-by-date
  const listDates: Date[] = [];
  const tempDate = new Date(currentDateRef.getTime());
  while (tempDate.getTime() <= endDateRef.getTime()) {
    listDates.push(new Date(tempDate.getTime()));
    tempDate.setDate(tempDate.getDate() + 1);
  }
  
  // For each Gregorian Date, we find the HOS events intersecting it and map them to fractional hours [0, 24]
  listDates.forEach((targetDate) => {
    const nextDate = new Date(targetDate.getTime());
    nextDate.setDate(nextDate.getDate() + 1);
    
    const targetDateStartMs = targetDate.getTime();
    const targetDateEndMs = nextDate.getTime();
    
    // Filter and clip itinerary items that fall within this Gregorian date
    const dayTimeline: {
      status: DutyStatus;
      startHour: number;
      endHour: number;
      locationName: string;
      remarks?: string;
    }[] = [];
    
    const dayRemarks: {
      timeLabel: string;
      status: DutyStatus;
      location: string;
      remarksText: string;
    }[] = [];
    
    let milesDrivenToday = 0;
    
    // We must track a continuous line spanning exactly 0.0 to 24.0.
    // So any time gap on this calendar day must be filled with OFF duty state (e.g. before trip starts or after trip ends)
    let lastMappedHour = 0.0;
    
    itinerary.forEach((item) => {
      const itemStart = new Date(item.startTime);
      const itemEnd = new Date(item.endTime);
      const itemStartMs = itemStart.getTime();
      const itemEndMs = itemEnd.getTime();
      
      // Check if item overlaps with this Gregorian day
      if (itemEndMs <= targetDateStartMs || itemStartMs >= targetDateEndMs) {
        return; // No overlap
      }
      
      // Calculate intersection bounds in milliseconds
      const overlapStartMs = Math.max(targetDateStartMs, itemStartMs);
      const overlapEndMs = Math.min(targetDateEndMs, itemEndMs);
      
      // Convert intersection bounds to fractional hours of the day (0.0 to 24.0)
      const startHourRaw = (overlapStartMs - targetDateStartMs) / (1000 * 60 * 60);
      const endHourRaw = (overlapEndMs - targetDateStartMs) / (1000 * 60 * 60);
      
      // Round to nearest quarter hour to prevent rendering float visual artifacts
      const startHour = roundToQuarterHour(startHourRaw);
      const endHour = roundToQuarterHour(endHourRaw);
      
      if (endHour <= startHour) {
        return; // rounds to nothing
      }
      
      // If there is any gap between the last mapped hour and this event start, fill with OFF DUTY
      if (startHour > lastMappedHour) {
        dayTimeline.push({
          status: DutyStatus.OFF,
          startHour: lastMappedHour,
          endHour: startHour,
          locationName: item.locationName,
          remarks: "Off Duty"
        });
      }
      
      // Push the clipped event
      dayTimeline.push({
        status: item.status,
        startHour,
        endHour,
        locationName: item.locationName,
        remarks: item.remarks
      });
      
      // Calculate miles driven on this day
      if (item.status === DutyStatus.D) {
        const itemDurationMs = itemEndMs - itemStartMs;
        const overlapDurationMs = overlapEndMs - overlapStartMs;
        const fractionIntersect = overlapDurationMs / itemDurationMs;
        milesDrivenToday += item.distanceMiles * fractionIntersect;
      }
      
      // Add remark if status transition starts on this Gregorian day and it's a distinct event
      if (itemStartMs >= targetDateStartMs && itemStartMs < targetDateEndMs) {
        const timeLabel = formatTimeLabel(itemStart);
        dayRemarks.push({
          timeLabel,
          status: item.status,
          location: item.locationName,
          remarksText: item.remarks || `${item.activityName}`
        });
      }
      
      lastMappedHour = endHour;
    });
    
    // Fill remaining gap at the end till Midnight with OFF DUTY
    if (lastMappedHour < 24.0) {
      dayTimeline.push({
        status: DutyStatus.OFF,
        startHour: lastMappedHour,
        endHour: 24.0,
        locationName: itinerary[itinerary.length - 1]?.locationName || `${dropoff.city}, ${dropoff.state}`,
        remarks: "Off Duty (Trip complete or idle)"
      });
    }
    
    // Calculate total hours for each status
    let offSum = 0;
    let sbSum = 0;
    let dSum = 0;
    let onSum = 0;
    
    dayTimeline.forEach(b => {
      const dur = b.endHour - b.startHour;
      if (b.status === DutyStatus.OFF) offSum += dur;
      else if (b.status === DutyStatus.SB) sbSum += dur;
      else if (b.status === DutyStatus.D) dSum += dur;
      else if (b.status === DutyStatus.ON) onSum += dur;
    });
    
    // Sanity adjustment: clean mathematically to sum up to exactly 24.0 hours due to potential rounding edge cases
    const totalListed = offSum + sbSum + dSum + onSum;
    if (Math.abs(totalListed - 24.0) > 0.001) {
      const diff = 24.0 - totalListed;
      // adjust OFF sum
      offSum += diff;
      // adjust last timeline element's end hour to exactly 24.0
      if (dayTimeline.length > 0) {
        dayTimeline[dayTimeline.length - 1].endHour = 24.0;
      }
    }
    
    dailyLogs.push({
      dateString: formatDateString(targetDate),
      dateLabel: formatDateLabel(targetDate),
      totalMilesDriven: Math.round(milesDrivenToday),
      tractorNumber,
      trailerNumber,
      carrierName,
      timeline: dayTimeline,
      totals: {
        OFF: roundToQuarterHour(offSum),
        SB: roundToQuarterHour(sbSum),
        D: roundToQuarterHour(dSum),
        ON: roundToQuarterHour(onSum)
      },
      remarks: dayRemarks
    });
  });
  
  return {
    current,
    pickup,
    dropoff,
    legs,
    totalDistanceMiles: Math.round(totalDistanceMiles),
    totalDurationHours: roundToQuarterHour(totalDurationHours),
    itinerary,
    dailyLogs
  };
}
