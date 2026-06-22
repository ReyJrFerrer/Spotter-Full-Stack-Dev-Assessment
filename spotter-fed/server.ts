/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import express from 'express';
import path from 'path';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI, Type } from '@google/genai';
import dotenv from 'dotenv';
import { simulateTrip } from './src/utils/hosSimulator';
import { GeocodedLocation } from './src/types';

// Load environment variables
dotenv.config();

const app = express();
app.use(express.json());

const PORT = 3000;

// Initialize GoogleGenAI SDK safely
let ai: GoogleGenAI | null = null;
const api_key = process.env.GEMINI_API_KEY;

if (api_key && api_key !== "MY_GEMINI_API_KEY") {
  ai = new GoogleGenAI({
    apiKey: api_key,
    httpOptions: {
      headers: {
        'User-Agent': 'aistudio-build',
      },
    },
  });
}

// Mock Cities database for ultra-resilient local fallback
const MOCK_CITIES: Record<string, { city: string, state: string, lat: number, lng: number }> = {
  "san diego": { city: "San Diego", state: "CA", lat: 32.7157, lng: -117.1611 },
  "los angeles": { city: "Los Angeles", state: "CA", lat: 34.0522, lng: -118.2437 },
  "las vegas": { city: "Las Vegas", state: "NV", lat: 36.1716, lng: -115.1398 },
  "phoenix": { city: "Phoenix", state: "AZ", lat: 33.4484, lng: -112.0740 },
  "salt lake city": { city: "Salt Lake City", state: "UT", lat: 40.7608, lng: -111.8910 },
  "denver": { city: "Denver", state: "CO", lat: 39.7392, lng: -104.9903 },
  "seattle": { city: "Seattle", state: "WA", lat: 47.6062, lng: -122.3321 },
  "dallas": { city: "Dallas", state: "TX", lat: 32.7767, lng: -96.7970 },
  "houston": { city: "Houston", state: "TX", lat: 29.7604, lng: -95.3698 },
  "chicago": { city: "Chicago", state: "IL", lat: 41.8781, lng: -87.6298 },
  "new york": { city: "New York", state: "NY", lat: 40.7128, lng: -74.0060 },
  "boston": { city: "Boston", state: "MA", lat: 42.3601, lng: -71.0589 },
  "atlanta": { city: "Atlanta", state: "GA", lat: 33.7490, lng: -84.3880 },
  "miami": { city: "Miami", state: "FL", lat: 25.7617, lng: -80.1918 }
};

function lookupMockLocation(query: string, defaultCity: string, defLat: number, defLng: number, defState: string): GeocodedLocation {
  const qClean = query.toLowerCase().trim();
  for (const entry of Object.keys(MOCK_CITIES)) {
    if (qClean.includes(entry)) {
      const mc = MOCK_CITIES[entry];
      return {
        label: `${mc.city}, ${mc.state}`,
        city: mc.city,
        state: mc.state,
        lat: mc.lat,
        lng: mc.lng
      };
    }
  }
  // Generic geocode fallback based on query
  return {
    label: query ? `${query} (Fallback)` : `${defaultCity}, ${defState}`,
    city: defaultCity,
    state: defState,
    lat: defLat,
    lng: defLng
  };
}

// Generate default coordinates to connect the fallbacks smoothly on Leaflet
function generateInterpolatedRoute(start: GeocodedLocation, pickup: GeocodedLocation, dropoff: GeocodedLocation): [number, number][] {
  const t: [number, number][] = [];
  const segments = 10;
  
  // Start to Pickup
  for (let i = 0; i <= segments; i++) {
    const f = i / segments;
    t.push([
      start.lat + (pickup.lat - start.lat) * f,
      start.lng + (pickup.lng - start.lng) * f
    ]);
  }
  
  // Pickup to Dropoff
  for (let i = 1; i <= segments; i++) {
    const f = i / segments;
    t.push([
      pickup.lat + (dropoff.lat - pickup.lat) * f,
      pickup.lng + (dropoff.lng - pickup.lng) * f
    ]);
  }
  return t;
}

// API Health route
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', using_gemini: !!ai });
});

// Full commercial log generation endpoint
app.post('/api/generate-trip', async (req, res) => {
  try {
    const {
      currentLocation,
      pickupLocation,
      dropoffLocation,
      currentCycleUsed,
      carrierName = "Global Logistics Express LLC",
      tractorNumber = "TRK-22401",
      trailerNumber = "TRL-9981A",
      startTime = new Date().toISOString()
    } = req.body;

    const cycleUsedNum = parseFloat(currentCycleUsed) || 0;

    let geodata: {
      current: GeocodedLocation,
      pickup: GeocodedLocation,
      dropoff: GeocodedLocation,
      milesCurrentToPickup: number,
      milesPickupToDropoff: number,
      routeCoordinates: [number, number][]
    } | null = null;

    if (ai) {
      try {
        const queryPrompt = `
          The truck driver wants to compute a trip log starting at: "${currentLocation}",
          unloading at: "${pickupLocation}", and finishing/dropping off at: "${dropoffLocation}".
          
          You are an expert geocoder and navigator. Perform the following items:
          1. Geocode each of these three landmarks into real City Name, State abbreviation, Latitude (number), and Longitude (number).
          2. Calculate highly accurate driving road mileage distance from current to pickup, and pickup to drop-off.
          3. Generate a highway corridor path tracing list of 15 contiguous Lat/Lng coordinates connecting these three locations, following actual major US highways where possible.
          
          Provide a strictly validated JSON response adhering to the response schema.
        `;

        const response = await ai.models.generateContent({
          model: 'gemini-3.5-flash',
          contents: queryPrompt,
          config: {
            responseMimeType: 'application/json',
            responseSchema: {
              type: Type.OBJECT,
              properties: {
                current: {
                  type: Type.OBJECT,
                  properties: {
                    label: { type: Type.STRING },
                    city: { type: Type.STRING },
                    state: { type: Type.STRING },
                    lat: { type: Type.NUMBER },
                    lng: { type: Type.NUMBER }
                  },
                  required: ["label", "city", "state", "lat", "lng"]
                },
                pickup: {
                  type: Type.OBJECT,
                  properties: {
                    label: { type: Type.STRING },
                    city: { type: Type.STRING },
                    state: { type: Type.STRING },
                    lat: { type: Type.NUMBER },
                    lng: { type: Type.NUMBER }
                  },
                  required: ["label", "city", "state", "lat", "lng"]
                },
                dropoff: {
                  type: Type.OBJECT,
                  properties: {
                    label: { type: Type.STRING },
                    city: { type: Type.STRING },
                    state: { type: Type.STRING },
                    lat: { type: Type.NUMBER },
                    lng: { type: Type.NUMBER }
                  },
                  required: ["label", "city", "state", "lat", "lng"]
                },
                milesCurrentToPickup: { type: Type.INTEGER },
                milesPickupToDropoff: { type: Type.INTEGER },
                routeCoordinates: {
                  type: Type.ARRAY,
                  items: {
                    type: Type.ARRAY,
                    items: { type: Type.NUMBER }
                  }
                }
              },
              required: ["current", "pickup", "dropoff", "milesCurrentToPickup", "milesPickupToDropoff", "routeCoordinates"]
            }
          }
        });

        const textResponse = response.text;
        if (textResponse) {
          const parsed = JSON.parse(textResponse.trim());
          geodata = parsed;
        }
      } catch (geminiError) {
        console.error("Gemini routing API call failed, triggering local fallback:", geminiError);
      }
    }

    // Execute Local Fallback if Gemini key is missing or failed
    if (!geodata) {
      console.log("Using deterministic local geocoding logic.");
      const currentGeo = lookupMockLocation(currentLocation, "Los Angeles", 34.0522, -118.2437, "CA");
      const pickupGeo = lookupMockLocation(pickupLocation, "Las Vegas", 36.1716, -115.1398, "NV");
      const dropoffGeo = lookupMockLocation(dropoffLocation, "Salt Lake City", 40.7608, -111.8910, "UT");
      
      // Calculate realistic Euclidean-equivalent mileages
      const dx1 = (pickupGeo.lat - currentGeo.lat) * 60;
      const dy1 = (pickupGeo.lng - currentGeo.lng) * 50;
      const milesCurrentToPickup = Math.max(50, Math.round(Math.sqrt(dx1 * dx1 + dy1 * dy1) * 1.2));

      const dx2 = (dropoffGeo.lat - pickupGeo.lat) * 60;
      const dy2 = (dropoffGeo.lng - pickupGeo.lng) * 50;
      const milesPickupToDropoff = Math.max(50, Math.round(Math.sqrt(dx2 * dx2 + dy2 * dy2) * 1.2));

      const routeCoordinates = generateInterpolatedRoute(currentGeo, pickupGeo, dropoffGeo);

      geodata = {
        current: currentGeo,
        pickup: pickupGeo,
        dropoff: dropoffGeo,
        milesCurrentToPickup,
        milesPickupToDropoff,
        routeCoordinates
      };
    }

    // Execute standard mathematical HOS Log simulation
    const simulationResult = simulateTrip(
      geodata!.current,
      geodata!.pickup,
      geodata!.dropoff,
      cycleUsedNum,
      startTime,
      carrierName,
      tractorNumber,
      trailerNumber,
      geodata!.routeCoordinates
    );

    res.json({
      success: true,
      data: {
        ...simulationResult,
        usingGemini: !!ai
      }
    });

  } catch (error: any) {
    console.error("Express generate trip failure:", error);
    res.status(500).json({
      success: false,
      message: error.message || "An error occurred during route scheduling."
    });
  }
});

// Configure Vite middleware for development or Static Assets for production
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
    console.log("Vite Development Server middleware mounted.");
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
    console.log("Serving static production files from dist/.");
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server listening on port http://0.0.0.0:${PORT}`);
  });
}

startServer();
