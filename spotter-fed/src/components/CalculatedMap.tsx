/**
 * @license
 * SPDX-License-Identifier: Apache-2.5
 */

import React, { useEffect, useRef, useState } from 'react';
import { GeocodedLocation, ItineraryItem, DutyStatus } from '../types';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Home, Package, Flag, Moon, Coffee, Fuel, RotateCcw, ShieldCheck, Info, Map as MapIcon } from 'lucide-react';
import { renderToStaticMarkup } from 'react-dom/server';

interface Props {
  start: GeocodedLocation;
  pickup: GeocodedLocation;
  dropoff: GeocodedLocation;
  itinerary: ItineraryItem[];
  routeCoordinates: [number, number][];
}

const iconSvg = (icon: React.ReactElement) => renderToStaticMarkup(icon);

const US_BOUNDS: L.LatLngBoundsExpression = [
  [24.0, -126.0],
  [50.0, -65.0]
];

const createDivIcon = (color: string, label: string, badgeSvg?: string) => {
  return L.divIcon({
    html: `
      <div class="flex flex-col items-center select-none" style="transform: translateY(-50%)">
        <div class="bg-white px-1.5 py-0.5 border border-[#1A1A1A] text-[9px] font-bold text-[#1A1A1A] whitespace-nowrap mb-1 shadow-[2px_2px_0px_#1A1A1A]">
          ${label}
        </div>
        <div class="relative flex items-center justify-center">
          <div class="h-6 w-6 rounded-none flex items-center justify-center text-white border border-[#1A1A1A] shadow-[2px_2px_0px_#1A1A1A]" style="background-color: ${color}">
            ${badgeSvg ? badgeSvg : `<span class="text-[9px] font-extrabold">${label.charAt(0)}</span>`}
          </div>
        </div>
      </div>
    `,
    className: 'custom-map-marker-html',
    iconSize: [40, 48],
    iconAnchor: [20, 24]
  });
};

export default function CalculatedMap({ start, pickup, dropoff, itinerary, routeCoordinates }: Props) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const polylineRef = useRef<L.Polyline | null>(null);
  const markerLayerRef = useRef<L.FeatureGroup | null>(null);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Map with custom coordinates if map does not exist
    if (!mapRef.current) {
      try {
        mapRef.current = L.map(mapContainerRef.current, {
          center: [pickup.lat, pickup.lng],
          zoom: 6,
          zoomControl: true,
          attributionControl: false,
          maxBounds: US_BOUNDS,
          maxBoundsViscosity: 0.15,
          minZoom: 3
        });

        // Premium Light Desaturated Map Tiles for Editorial Vibe
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
          maxZoom: 19
        }).addTo(mapRef.current);

        markerLayerRef.current = L.featureGroup().addTo(mapRef.current);
      } catch (err: any) {
        setMapError("Failed to initialize Leaflet Map. Click 'Recenter' to refresh.");
      }
    }

    const map = mapRef.current;
    const markerLayer = markerLayerRef.current;
    if (!map || !markerLayer) return;

    // Reset previous layer items
    markerLayer.clearLayers();
    if (polylineRef.current) {
      polylineRef.current.remove();
    }

    try {
      // 1. Draw Polyline Trajectory
      if (routeCoordinates && routeCoordinates.length > 0) {
        polylineRef.current = L.polyline(routeCoordinates, {
          color: '#1A1A1A',
          weight: 3,
          opacity: 0.9,
          dashArray: '5, 5'
        }).addTo(map);
      }

      // 2. Add Primary Milestones Markers
      L.marker([start.lat, start.lng], {
        icon: createDivIcon('#E8E4DF', 'START', iconSvg(<Home size={14} className="text-[#FD5368]" />))
      }).bindPopup(`<b>Start Base Location</b><br/>${start.label}`).addTo(markerLayer);

      L.marker([pickup.lat, pickup.lng], {
        icon: createDivIcon('#1A1A1A', 'PICKUP', iconSvg(<Package size={14} className="text-[#FD5368]" />))
      }).bindPopup(`<b>Pickup Location (1h Load)</b><br/>${pickup.label}`).addTo(markerLayer);

      L.marker([dropoff.lat, dropoff.lng], {
        icon: createDivIcon('#7139ea', 'DROPOFF', iconSvg(<Flag size={14} className="text-[#FD5368]" />))
      }).bindPopup(`<b>Final Dropoff (1h Unload)</b><br/>${dropoff.label}`).addTo(markerLayer);

      // 3. Add En-Route calculated HOS Stops and Fuel Marks
      itinerary.forEach((item) => {
        const [lat, lng] = item.coordinates;
        // Avoid packing identical coordinates exactly on top of primary landmarks
        const isPrimary = (Math.abs(lat - start.lat) < 0.05 && Math.abs(lng - start.lng) < 0.05) ||
                          (Math.abs(lat - pickup.lat) < 0.05 && Math.abs(lng - pickup.lng) < 0.05) ||
                          (Math.abs(lat - dropoff.lat) < 0.05 && Math.abs(lng - dropoff.lng) < 0.05);

        if (isPrimary && item.status !== DutyStatus.SB) return;

        if (item.status === DutyStatus.SB && item.activityName.includes("10-Hour")) {
          L.marker([lat, lng], {
            icon: createDivIcon('#1A1A1A', 'RESET', iconSvg(<Moon size={14} className="text-[#FD5368]" />))
          }).bindPopup(`<b>HOS Sleep Restart (10 hrs)</b><br/>Location: ${item.locationName}<br/>Start: ${new Date(item.startTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`).addTo(markerLayer);
        } else if (item.status === DutyStatus.OFF && item.activityName.includes("30-Minute")) {
          L.marker([lat, lng], {
            icon: createDivIcon('#E8E4DF', 'BREAK', iconSvg(<Coffee size={14} className="text-[#FD5368]" />))
          }).bindPopup(`<b>Mandatory Rest Break (30 min)</b><br/>Location: ${item.locationName}`).addTo(markerLayer);
        } else if (item.status === DutyStatus.ON && item.activityName.includes("Fueling")) {
          L.marker([lat, lng], {
            icon: createDivIcon('#7139ea', 'FUEL', iconSvg(<Fuel size={14} className="text-[#FD5368]" />))
          }).bindPopup(`<b>Fueling Stop (30 min)</b><br/>Location: ${item.locationName}`).addTo(markerLayer);
        } else if (item.status === DutyStatus.OFF && item.activityName.includes("34-Hour")) {
          L.marker([lat, lng], {
            icon: createDivIcon('#1A1A1A', 'RESTART', iconSvg(<RotateCcw size={14} className="text-[#FD5368]" />))
          }).bindPopup(`<b>34-Hour Weekly Cycle Reset</b><br/>Location: ${item.locationName}`).addTo(markerLayer);
        }
      });

      // Fit map view to cover all milestones
      const bounds = markerLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    } catch (e) {
      console.error(e);
    }
  }, [start, pickup, dropoff, itinerary, routeCoordinates]);

  const handleRecenter = () => {
    if (mapRef.current && markerLayerRef.current) {
      const bounds = markerLayerRef.current.getBounds();
      if (bounds.isValid()) {
        mapRef.current.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  };

  return (
    <div id="results-map-panel" className="bg-white border-2 border-[#1A1A1A] p-6 shadow-[6px_6px_0px_#133658] flex flex-col h-full">
      <div className="flex items-center justify-between border-b-2 border-[#1A1A1A] pb-4 mb-4">
        <div className="flex items-center gap-2">
          <MapIcon className="h-5 w-5 text-[#FD5368]" />
          <h2 className="text-xs font-bold uppercase tracking-widest text-[#1A1A1A]">2. Interactive Commercial Truck Route</h2>
        </div>
        <button
          id="btn-map-recenter"
          onClick={handleRecenter}
          className="text-xs bg-[#E8E4DF] hover:bg-[#1A1A1A] hover:text-white border border-[#1A1A1A] text-[#1A1A1A] font-bold py-1 px-3 transition-all cursor-pointer"
        >
          RECENTER
        </button>
      </div>

      {mapError && (
        <div className="bg-amber-50 border border-amber-300 p-3 text-xs text-amber-900 mb-3 flex items-start gap-2">
          <Info className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{mapError}</span>
        </div>
      )}

      {/* Actual Tile Map wrapper */}
      <div className="relative flex-1 w-full border border-[#1A1A1A] min-h-[380px]">
        <div
          ref={mapContainerRef}
          id="leaflet-route-map-elem"
          className="absolute inset-0 w-full h-full bg-[#F4F1ED] z-10"
        />
        
        {/* Visual Legends overlay */}
        <div className="absolute bottom-3 right-3 bg-white px-3 py-2.5 border border-[#1A1A1A] shadow-[3px_3px_0px_#133658] z-40 text-[9px] uppercase font-bold tracking-wider space-y-1.5 min-w-[155px]">
          <h4 className="font-extrabold text-[#1A1A1A] border-b border-[#1A1A1A]/10 pb-1">Legend Marks:</h4>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#E8E4DF] border border-[#1A1A1A] inline-block shrink-0"></span>
            <span className="text-[#1A1A1A] opacity-75">Start Base</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#1A1A1A] border border-[#1A1A1A] inline-block shrink-0"></span>
            <span className="text-[#1A1A1A] opacity-75">Cargo Pickup (1h)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#7139ea] border border-[#1A1A1A] inline-block shrink-0"></span>
            <span className="text-[#1A1A1A] opacity-75">Cargo Dropoff</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#1A1A1A] border border-[#1A1A1A] inline-block shrink-0"></span>
            <span className="text-[#1A1A1A] opacity-75">10h Sleep Restart</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#E8E4DF] border border-[#1A1A1A] inline-block shrink-0"></span>
            <span className="text-[#1A1A1A] opacity-75">30m Rest Break</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#7139ea] border border-[#1A1A1A] inline-block shrink-0"></span>
            <span className="text-[#1A1A1A] opacity-75">Fueling stops</span>
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2 text-[10px] text-[#1A1A1A]/70 uppercase tracking-wider font-bold bg-[#E8E4DF]/60 p-3 border border-[#1A1A1A]/20">
        <ShieldCheck className="h-4 w-4 text-[#FD5368] shrink-0" />
        <span>Stops comply with standard FMCSA 11h driving / 14h window rules.</span>
      </div>
    </div>
  );
}
