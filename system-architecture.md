**Project Description**
This project is a full-stack web application built with Django and React that serves as an AI-powered route and Electronic Logging Device (ELD) log generator for property-carrying commercial truck drivers. The system accepts specific trip inputs (current location, pickup location, dropoff location, and current cycle hours used), integrates a free Map API, and applies strict Federal Motor Carrier Safety Administration (FMCSA) Hours of Service (HOS) rules to calculate an optimized route with mandatory scheduled stops. The application outputs visual step-by-step route instructions and dynamically drawn 24-hour ELD daily log sheets.

***

### **System Architecture Specifications**

**1. Frontend Architecture (React)**
*   **Framework & State Management:** The client-side application is a React Single Page Application (SPA) that manages user interfaces and application state. It uses the `axios` library to make asynchronous HTTP requests to the backend API.
*   **Component Framework:** The UI is constructed using Material UI (MUI) to create a modular, card-based layout that cleanly separates the input forms, interactive maps, and log visualizations. 
*   **Typography & Theming:** The frontend implements tabular lining for all numerical data to prevent horizontal shifting. It features a theme toggle between a data-dense Light Mode and a required True Dark Mode (utilizing deep grays like #121212) to prevent cabin glare for drivers.
*   **Dynamic Visual Rendering:** The frontend includes an ELD Log Grid component that takes the JSON timeline data from the backend and dynamically draws solid continuous lines across a standard 24-hour grid to represent time spent in Off Duty, Sleeper Berth, Driving, and On Duty statuses.

**2. Backend Architecture (Django)**
*   **Framework & API:** The server-side engine is built with Python's Django framework and the Django REST Framework (DRF). It is responsible for handling business logic and exposing RESTful API endpoints for the React frontend to consume.
*   **Routing Integration:** The backend communicates with a free Map API to calculate the driving distance, route path, and estimated driving time between the inputted locations.
*   **HOS Algorithm Engine:** The backend houses the core computational logic that iteratively schedules the trip based strictly on FMCSA constraints:
    *   Injecting 1 hour of on-duty time for pickup and 1 hour for drop-off.
    *   Forcing a fueling stop at least once every 1,000 miles.
    *   Enforcing an 11-hour driving limit and a 14-hour consecutive driving window, followed by a mandatory 10-hour off-duty reset.
    *   Mandating a 30-minute consecutive rest break after 8 cumulative hours of driving.
    *   Tracking cumulative on-duty/driving hours against the user's current cycle used to enforce the 70-hour/8-day limit.
*   **Data Serialization:** The DRF serializers convert the complex calculated itinerary, stop locations, and specific 15-minute increment logbook grid coordinates into structured JSON responses. 

**3. Inter-System Communication & Deployment**
*   **Cross-Origin Resource Sharing (CORS):** To allow the separated React and Django applications to communicate securely during development and production, the backend configures `django-cors-headers` to whitelist frontend API requests.
*   **Deployment Configuration:** Deploy the application through vercel