**Project Context**
This project is a full-stack web application (built with Django and React) that serves as an AI-powered route and Electronic Logging Device (ELD) log generator for property-carrying commercial truck drivers. Aligning with the identity as a modern, AI-native fleet management platform, the system moves away from clunky legacy interfaces. It accepts specific trip details, calculates an optimized route with legally compliant stops, and dynamically outputs map instructions along with visually drawn daily log sheets based on strict FMCSA Hours of Service (HOS) regulations.

### **Updated UI/UX Specifications for Frontend**

**Global Design System & Theming**
*   **Component Framework:** Base the entire user interface on Material UI (MUI). Utilize modular, card-based layouts that allow distinct sections (like inputs, maps, and logs) to be cleanly separated, easily reorganized, or collapsed. 
*   **Typography:** Implement a clean, highly legible sans-serif font such as Inter or Roboto. You must use **tabular lining** for all numerical data (e.g., cycle hours used, log sheet hour totals, daily mileage) to ensure digits do not shift horizontally as values change.
*   **Color Palette:**
    *   **Primary:** High-trust tech blues to communicate reliability and stability throughout the core dashboard structure.
    *   **Accent:** Electric blue or subtle neon purple to highlight AI-driven insights (e.g., badges indicating a route is "AI Optimized").
    *   **Functional (Critical for ELD):** 
        *   Vibrant Green: Active driving or compliant status.
        *   High-visibility Amber/Orange: Nearing HOS violation limits (e.g., approaching the 11-hour driving limit or 14-hour window).
        *   Crimson Red: Violation alerts or mandatory maintenance/rest stops.
*   **Theme Toggling:** 
    *   **Light Mode:** A crisp, data-dense view optimized for a dispatcher's web dashboard.
    *   **True Dark Mode (Required):** An absolute necessity for the driver-facing view to prevent cabin glare and protect night vision. Utilize deep grays (e.g., #121212) rather than pure black to minimize eye strain.

**Input Dashboard (Trip Details Form)**
*   **Modular Layout:** Encase the input form within a distinct MUI card.
*   **Required Fields:** Clear, tabular-lined input fields for:
    *   Current location
    *   Pickup location
    *   Dropoff location
    *   Current Cycle Used (in hours)
*   **Action Mechanism:** A prominent call-to-action button utilizing the primary tech blue, triggering the AI routing and log generation logic.

**Results Dashboard 1: Map and Route Itinerary**
*   **Interactive Map Card:** A dedicated card containing a free map API to visually trace the driving route. Apply the AI-accent colors (electric blue/purple) to the drawn route line to emphasize that the path is algorithmically optimized.
*   **Dynamic Stop Callouts:** Visually highlight required stops using the functional color palette:
    *   1-hour stops for pickup and drop-off (Blue).
    *   Forced fueling stops every 1,000 miles (Blue or Green).
    *   Mandatory HOS rests (30-minute breaks, 10-hour resets) flagged with Amber or Red depending on the urgency of the limit.
*   **Step-by-Step Itinerary:** A collapsible chronological list detailing the exact times and locations for driving, stopping, and resting.

**Results Dashboard 2: ELD Daily Log Sheets**
*   **Multiple Sheets & Pagination:** Generate multiple daily log sheets within stacked MUI cards if the calculated trip extends beyond a single 24-hour period.
*   **The 24-Hour Graph Grid:** Faithfully recreate the standard 24-hour log grid layout:
    *   **Time Axis:** Midnight to Midnight across the top, utilizing vertical markers for hours and 15-minute increments.
    *   **Duty Status Rows:** Four distinct horizontal rows: **Off Duty**, **Sleeper Berth**, **Driving**, and **On Duty (Not Driving)**.
*   **Dynamic Line Drawing (Color-Coded):** Draw continuous, solid lines to represent time spent in statuses and vertical drops/rises for status changes. Enhance this output by applying the functional color palette to the lines (e.g., Vibrant Green for the "Driving" line, Crimson Red or Amber for mandatory "Off Duty" resets).
*   **Header Information:** Include standard metadata fields at the top of the card (Date, Total Miles Driving Today, Truck/Trailer Number, Carrier Name).
*   **Remarks Section:** Positioned below the grid, automatically populating the city and State abbreviation alongside a 45-degree flag mark whenever a change of duty status occurs. 
*   **Daily Totals:** A vertical column on the far right utilizing tabular lining to calculate the total hours spent in each of the four duty statuses, ensuring they sum to exactly 24 hours.