# Air Quality Monitoring System

A real-time air quality monitoring system that provides visualization, alerting, and user preference management for PM2.5 measurements.

## Features

- Real-time PM2.5 data visualization on an interactive map
- Configurable alert system based on WHO guidelines
- User preference management for alert notifications
- Historical data tracking and analysis
- Responsive web interface

## Tech Stack

- **Frontend**: React, TypeScript, Leaflet.js
- **Backend**: FastAPI, MongoDB
- **Message Queue**: RabbitMQ
- **Real-time Updates**: MQTT
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- MongoDB
- RabbitMQ
- MQTT Broker (Mosquitto)

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/openaq-visualizer.git
   cd openaq-visualizer
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the development environment:
   ```bash
   docker-compose up -d
   ```

4. Access the applications:
   - Frontend: http://localhost
   - Backend API: http://localhost/api
   - RabbitMQ Management: http://localhost:15672
   - MongoDB: mongodb://localhost:27017

## Testing

### Backend Tests
```bash
cd backend
pip install -r requirements.txt
pytest
```

### Frontend Tests
```bash
cd frontend
npm install
npm test
```

## Deployment

The application is configured for deployment using GitHub Actions. The CI/CD pipeline includes:

1. Testing
   - Unit tests
   - Integration tests
   - Code coverage

2. Building
   - Docker image creation
   - Image tagging
   - Push to GitHub Container Registry

3. Security
   - Vulnerability scanning
   - Dependency checking
   - Container scanning

4. Deployment
   - Automatic deployment to production
   - Zero-downtime updates
   - Rollback capability

## Environment Variables

### Frontend
- `VITE_API_URL`: Backend API URL
- `VITE_MQTT_WS_URL`: MQTT WebSocket URL

### Backend
- `MONGODB_URI`: MongoDB connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `MQTT_BROKER`: MQTT broker URL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAQ for providing the air quality data
- WHO for air quality guidelines
- All contributors and maintainers
