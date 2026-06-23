import {
  DutyStatus,
  TripGenerationResult,
  GeocodedLocation,
  RouteLeg,
  ItineraryItem,
  DailyLogSheet,
} from '../types';

function mapLocation(loc: any): GeocodedLocation {
  return {
    label: loc.label,
    city: loc.city,
    state: loc.state,
    lat: loc.lat,
    lng: loc.lng,
  };
}

function mapLeg(leg: any): RouteLeg {
  return {
    from: mapLocation(leg.from_location),
    to: mapLocation(leg.to_location),
    distanceMiles: leg.distance_miles,
    durationHours: leg.duration_hours,
  };
}

function mapItineraryItem(item: any): ItineraryItem {
  return {
    id: item.id,
    status: item.status as DutyStatus,
    activityName: item.activity_name,
    locationName: item.location_name,
    startTime: item.start_time,
    endTime: item.end_time,
    durationHours: item.duration_hours,
    distanceMiles: item.distance_miles,
    coordinates: [item.coordinates[0], item.coordinates[1]],
    remarks: item.remarks,
  };
}

function mapTimelineBlock(block: any): {
  status: DutyStatus;
  startHour: number;
  endHour: number;
  locationName: string;
  remarks?: string;
} {
  return {
    status: block.status as DutyStatus,
    startHour: block.start_hour,
    endHour: block.end_hour,
    locationName: block.location_name,
    remarks: block.remarks,
  };
}

function mapDailyLogRemarks(remark: any): {
  timeLabel: string;
  status: DutyStatus;
  location: string;
  remarksText: string;
} {
  return {
    timeLabel: remark.time_label,
    status: remark.status as DutyStatus,
    location: remark.location,
    remarksText: remark.remarks_text,
  };
}

function mapDailyLog(log: any): DailyLogSheet {
  return {
    dateString: log.date_string,
    dateLabel: log.date_label,
    totalMilesDriven: log.total_miles_driven,
    tractorNumber: log.tractor_number,
    trailerNumber: log.trailer_number,
    carrierName: log.carrier_name,
    timeline: log.timeline.map(mapTimelineBlock),
    totals: {
      OFF: log.totals.OFF,
      SB: log.totals.SB,
      D: log.totals.D,
      ON: log.totals.ON,
    },
    remarks: log.remarks.map(mapDailyLogRemarks),
  };
}

export function mapBackendResponse(data: any): TripGenerationResult {
  return {
    routeCoordinates: (data.route_geometry || []).map(
      (coord: [number, number]) => [coord[0], coord[1]] as [number, number]
    ),
    current: mapLocation(data.current),
    pickup: mapLocation(data.pickup),
    dropoff: mapLocation(data.dropoff),
    legs: (data.legs || []).map(mapLeg),
    totalDistanceMiles: data.total_distance_miles,
    totalDurationHours: data.total_duration_hours,
    itinerary: (data.itinerary || []).map(mapItineraryItem),
    dailyLogs: (data.daily_logs || []).map(mapDailyLog),
  };
}

export function mergeUserMetadata(
  result: TripGenerationResult,
  carrierName: string,
  tractorNumber: string,
  trailerNumber: string
): TripGenerationResult {
  return {
    ...result,
    dailyLogs: result.dailyLogs.map((log) => ({
      ...log,
      carrierName: carrierName || log.carrierName,
      tractorNumber: tractorNumber || log.tractorNumber,
      trailerNumber: trailerNumber || log.trailerNumber,
    })),
  };
}
