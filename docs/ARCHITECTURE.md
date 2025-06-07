# OpenAQ Visualizer Architecture Documentation

## 1. Data Source: OpenAQ API

### 1.1 Overview
The OpenAQ API provides real-time and historical air quality data from monitoring stations worldwide. Our system specifically focuses on PM2.5 (fine particulate matter) measurements.

### 1.2 API Details
- Base URL: https://api.openaq.org/v3
- Endpoint: /parameters/2/latest (PM2.5 measurements)
- Rate Limits: 1000 requests per day
- Data Format: JSON
- Update Frequency: Varies by station (typically 1-60 minutes)

### 1.3 Data Structure
```json
{
  "results": [
    {
      "coordinates": {
        "latitude": float,
        "longitude": float
      },
      "value": float,
      "unit": string,
      "date": {
        "utc": string (ISO 8601)
      }
    }
  ]
}
```

### 1.4 Data Quality Considerations
- Missing values are common
- Units may vary (µg/m³, ppm)
- Timestamps may be delayed
- Station coverage varies by region

## 2. Storage Architecture

### 2.1 MongoDB Schema
```javascript
// latest_pm25 collection
{
  lat: float,
  lon: float,
  pm25: float,
  unit: string,
  timestamp: string (ISO 8601)
}
```

### 2.2 Data Flow
1. Ingest Service
   - Fetches data from OpenAQ API
   - Publishes to RabbitMQ "raw_data" exchange
   - Runs every 60 seconds

2. Batch Consumer
   - Consumes from "raw_data" exchange
   - Updates MongoDB with latest readings
   - Maintains one document per location

3. Real-time Processor
   - Consumes from "raw_data" exchange
   - Evaluates PM2.5 thresholds
   - Generates alerts when thresholds exceeded

### 2.3 Data Retention
- Latest readings: Kept indefinitely
- Historical data: Not currently stored
- Alert history: Not currently stored

## 3. Processing Logic

### 3.1 PM2.5 Threshold Detection
Current implementation uses a fixed threshold of 15 µg/m³, based on WHO guidelines.

### 3.2 Event Generation
Events are generated when:
- PM2.5 exceeds threshold
- New data point is received
- Location has valid coordinates

### 3.3 Data Normalization
- Coordinates are validated
- Units are preserved
- Timestamps are standardized to UTC

### 3.4 Error Handling
- API failures: Retry after 60 seconds
- Invalid data: Skip and log
- Connection issues: Automatic reconnection

## 4. Alert System

### 4.1 Current Implementation
- Simple threshold-based alerts
- Published to RabbitMQ "alerts" exchange
- Forwarded to MQTT for real-time updates
- Basic console notification

### 4.2 Alert Format
```json
{
  "lat": float,
  "lon": float,
  "pm25": float,
  "unit": string,
  "timestamp": string
}
```

### 4.3 Threshold Options
1. WHO Guidelines
   - 24-hour mean: 15 µg/m³
   - Annual mean: 5 µg/m³

2. EPA Standards
   - 24-hour mean: 35 µg/m³
   - Annual mean: 12 µg/m³

3. EU Standards
   - 24-hour mean: 25 µg/m³
   - Annual mean: 20 µg/m³

## 5. System Components

### 5.1 Ingest Service
- Python-based
- Fetches OpenAQ data
- Publishes to RabbitMQ
- Error handling and retries

### 5.2 Batch Consumer
- Python-based
- Updates MongoDB
- Maintains latest readings
- Handles data validation

### 5.3 Real-time Processor
- Python-based
- Evaluates thresholds
- Generates alerts
- Publishes to MQTT

### 5.4 Notifier Service
- Python-based
- Consumes alerts
- Currently console-only
- Ready for extension

### 5.5 Backend API
- FastAPI-based
- Serves latest readings
- CORS enabled
- MongoDB integration

### 5.6 Frontend
- React-based
- Real-time map visualization
- MQTT integration
- Responsive design

## 6. Data Flows

### 6.1 Real-time Flow
```
OpenAQ API → Ingest → RabbitMQ → Real-time Processor → Alerts → MQTT → Frontend
```

### 6.2 Batch Flow
```
OpenAQ API → Ingest → RabbitMQ → Batch Consumer → MongoDB → Backend API → Frontend
```

### 6.3 Alert Flow
```
Real-time Processor → RabbitMQ → Notifier → (Future: Email/SMS/Web)
```

## 7. Future Enhancements

### 7.1 Alert System
- Configurable thresholds
- Multiple severity levels
- Alert persistence
- Acknowledgment system
- Delivery preferences

### 7.2 Business Model
- Subscription levels
- Location-based filtering
- Custom alert rules
- Alert aggregation
- Reporting system

### 7.3 Analysis Features
- Historical data storage
- Trend detection
- Statistical analysis
- Custom dashboards
- Export capabilities 