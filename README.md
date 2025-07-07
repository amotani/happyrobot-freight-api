# HappyRobot Inbound Carrier API

A production-ready FastAPI application for managing inbound carrier engagement and load management for the HappyRobot platform.

## Features

- 🚚 **Carrier Verification**: Integrated FMCSA API for MC number verification
- 📦 **Load Management**: Complete load search and management for voice agents
- 🤝 **Negotiation Handling**: Advanced negotiation tracking with transfer failure support
- 📞 **Webhook Support**: Handle real-time events from HappyRobot platform
- 🔐 **API Security**: Bearer token authentication with configurable HTTPS
- 📊 **Analytics Dashboard**: Modern shadcn/ui dashboard with real-time metrics
- 📈 **Call Analytics**: Extract insights from carrier interactions and sentiment analysis
- 🏗️ **Production Ready**: Deployed on Render with SQLite persistence

## Live Deployment

- **API**: `https://freight-carrier-api.onrender.com`
- **Dashboard**: `https://freight-carrier-api.onrender.com/static/dashboard/index.html`
- **API Docs**: `https://freight-carrier-api.onrender.com/docs`
- **Health Check**: `https://freight-carrier-api.onrender.com/health`

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### 1. Clone and Setup

```bash
git clone https://github.com/amotani/freight-carrier-api.git
cd happyrobotpy
```

### 2. Environment Configuration

Create a `.env` file with the following variables:

```bash
# API Security (REQUIRED)
HAPPYROBOT_API_KEY=your-production-api-key

# Application Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=WARNING

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security
REQUIRE_HTTPS=false

# FMCSA API Configuration
FMCSA_API_KEY=your-fmcsa-api-key
FMCSA_BASE_URL=https://mobile.fmcsa.dot.gov/qc/services
```

### 3. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### 4. Docker Deployment

```bash
# Build and run with Docker
docker build -t happyrobot-api .
docker run -p 8000:8000 -e HAPPYROBOT_API_KEY=your-api-key happyrobot-api
```

### 5. Testing with ngrok (Optional)

```bash
# Install ngrok and expose your local server
ngrok http 8000

# Use the ngrok URL for webhook endpoints in HappyRobot platform
# Example: https://abc123.ngrok.io/webhook/carrier-engagement
```

## API Documentation

Once running, access the interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication

All endpoints (except health checks and dashboard config) require a Bearer token:

```bash
curl -H "Authorization: Bearer your-happyrobot-api-key" \
     http://localhost:8000/loads/for-voice-agent
```

## Core Endpoints

### Voice Agent Endpoints

**GET** `/loads/for-voice-agent` - Get loads optimized for AI voice agents
**GET** `/loads/{load_id}/for-voice-agent` - Get detailed load info for voice agents
**GET** `/verify-carrier/{mc_number}` - Verify carrier eligibility

### Webhook Endpoint

**POST** `/webhook/carrier-engagement`

Main webhook for handling HappyRobot platform events.

**Event Types:**

- `carrier_call_initiated` - New carrier call started
- `load_interest_expressed` - Carrier interested in a load
- `negotiation_offer` - Carrier makes counter offer
- `agreement_reached` - Successful negotiation
- `negotiation_declined` - Carrier declined offer
- `transfer_failed` - Sales transfer failed (operational issue)
- `call_ended` - Call completion and analytics

**Example Request:**

```json
{
  "event_type": "carrier_call_initiated",
  "carrier_info": {
    "mc_number": "123456",
    "company_name": "ABC Trucking",
    "phone_number": "+1234567890"
  },
  "timestamp": "2024-12-19T10:00:00Z"
}
```

### Analytics Dashboard

**GET** `/dashboard/config` - Get dashboard configuration (no auth required)
**GET** `/dashboard/analytics` - Get comprehensive analytics data
**GET** `/dashboard/status` - Get system status information

Access the dashboard at: `/static/dashboard/index.html`

## Analytics Dashboard

### Features

- **Modern UI**: shadcn/ui inspired design with Tailwind CSS
- **Real-time Metrics**: Auto-refreshes every 30 seconds
- **Key Metrics**: Total calls, success rate, negotiation rounds, rate differences
- **Visual Charts**: Call outcomes and carrier sentiment analysis
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Secure**: No hardcoded API keys, fetches config dynamically

### Metrics Tracked

- Call success rates (complete vs partial success)
- AI negotiation performance vs operational success
- Carrier sentiment analysis (positive, negative, interested)
- Negotiation rounds and rate differences
- Transfer failure tracking and classification

## Workflow Integration

### 1. HappyRobot Platform Setup

1. Configure your inbound campaign in HappyRobot
2. Set webhook URL to: `https://freight-carrier-api.onrender.com/webhook/carrier-engagement`
3. Configure authentication headers with your API key

### 2. Call Flow

1. **Carrier calls** → Webhook: `carrier_call_initiated`
2. **MC verification** → FMCSA API check
3. **Load search** → Return available loads optimized for voice
4. **Interest expressed** → Webhook: `load_interest_expressed`
5. **Negotiation** → Multiple `negotiation_offer` events with rate limits
6. **Agreement** → Webhook: `agreement_reached`
7. **Transfer** → Hand off to sales team or handle `transfer_failed`
8. **Call end** → Webhook: `call_ended` with complete analytics

## Production Deployment

### Render Deployment (Current)

The application is deployed on Render with the following configuration:

**Environment Variables:**

```bash
HAPPYROBOT_API_KEY=your-production-api-key
ENVIRONMENT=production
LOG_LEVEL=WARNING
REQUIRE_HTTPS=true
FMCSA_API_KEY=your-fmcsa-api-key
```

**Deployment URL:** `https://freight-carrier-api.onrender.com`

### Alternative Cloud Providers

The application is ready for deployment to:

- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **Fly.io**
- **Railway**
- **Heroku**

## Monitoring and Analytics

### Health Checks

- **GET** `/health` - Application health status
- **GET** `/` - Basic application info with timestamp

### Analytics Features

The system automatically tracks and analyzes:

- **Call Outcomes**: Success vs failure classification
- **Success Types**: Complete success vs partial success (transfer failures)
- **Carrier Sentiment**: Positive, negative, interested sentiment analysis
- **Negotiation Metrics**: Average rounds, rate differences
- **Performance Trends**: Historical performance tracking
- **Transfer Failures**: Operational vs AI failure classification

### Database

- **SQLite**: Persistent analytics storage
- **In-Memory**: Sample load and carrier data
- **Automatic**: Database initialization on startup

## Security Features

✅ **Bearer Token Authentication**: Configurable API key security  
✅ **HTTPS Support**: Enforced in production with REQUIRE_HTTPS  
✅ **Environment Variables**: All sensitive data externalized  
✅ **Input Validation**: Pydantic models for all endpoints  
✅ **Error Handling**: Comprehensive logging and error responses  
✅ **CORS Configuration**: Configurable cross-origin settings  
✅ **Production Logging**: WARNING level default for production

## Development

### Current Code Structure

```
├── main.py                          # FastAPI application
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container configuration
├── README.md                        # This file

├── src/
│   ├── auth/
│   │   └── authentication.py       # API key auth and security
│   ├── database/
│   │   └── storage.py              # SQLite and data management
│   ├── handlers/
│   │   └── webhook_handler.py      # Webhook event processing
│   ├── models/
│   │   ├── carrier.py              # Carrier data models
│   │   ├── load.py                 # Load data models
│   │   ├── negotiation.py          # Negotiation models
│   │   └── webhook.py              # Webhook payload models
│   ├── routes/
│   │   ├── carriers.py             # Carrier verification endpoints
│   │   ├── dashboard.py            # Analytics dashboard endpoints
│   │   ├── loads.py                # Load management endpoints
│   │   └── webhook.py              # Webhook endpoints
│   └── services/
│       ├── analytics.py            # Call analytics and sentiment
│       ├── fmcsa.py                # FMCSA carrier verification
│       ├── load_service.py         # Load search and matching
│       └── startup.py              # Application initialization
└── static/
    └── dashboard/
        └── index.html              # Analytics dashboard UI
```

### Adding New Features

1. **New endpoints**: Add to appropriate route module in `src/routes/`
2. **Data models**: Create Pydantic models in `src/models/`
3. **Business logic**: Add service functions in `src/services/`
4. **Database changes**: Update schema in `src/database/storage.py`

## API Testing

### Example API Calls

**Verify Carrier:**

```bash
curl -H "Authorization: Bearer your-api-key" \
     https://freight-carrier-api.onrender.com/verify-carrier/123456
```

**Get Loads for Voice Agent:**

```bash
curl -H "Authorization: Bearer your-api-key" \
     https://freight-carrier-api.onrender.com/loads/for-voice-agent
```

**Send Webhook Event:**

```bash
curl -X POST https://freight-carrier-api.onrender.com/webhook/carrier-engagement \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-api-key" \
     -d '{
       "event_type": "carrier_call_initiated",
       "carrier_info": {
         "mc_number": "123456",
         "company_name": "Test Carrier"
       }
     }'
```

## Troubleshooting

### Common Issues

1. **Authentication errors**: Check `HAPPYROBOT_API_KEY` environment variable
2. **FMCSA API failures**: Verify `FMCSA_API_KEY` configuration
3. **Dashboard not loading**: Check `/dashboard/config` endpoint
4. **Webhook not receiving events**: Verify URL and authentication headers
5. **Database errors**: Ensure write permissions for SQLite file

### Logs

**Local Development:**

```bash
# Logs appear in terminal when running python main.py
```

**Production (Render):**

```bash
# View logs in Render dashboard or via CLI
render logs <service-id>
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test locally
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is part of the HappyRobot technical challenge.

---

## Documentation

- **API Documentation**: Available at `/docs` endpoint when running
- **Dashboard**: Modern analytics interface at `/static/dashboard/index.html`

For questions and support, contact the development team.
