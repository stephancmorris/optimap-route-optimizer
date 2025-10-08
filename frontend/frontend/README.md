# OptiMap Frontend - Route Visualization Interface

React-based user interface for OptiMap route optimization, featuring interactive mapping with Leaflet.

## 🔧 Technology Stack

- **React** 19.1.1 - UI framework
- **Vite** 7.1.7 - Build tool and dev server
- **React-Leaflet** 5.0.0 - Interactive mapping library
- **Leaflet** 1.9.4 - Open-source map rendering
- **ESLint** 9.37.0 - Code linting
- **Prettier** 3.6.2 - Code formatting

## 📋 Prerequisites

- **Node.js 18+** (tested with Node 22.15.0)
- **npm 10+** (tested with npm 10.9.2)

## 🚀 Quick Start

```bash
npm install
cp .env.example .env
npm run dev
```

Visit http://localhost:5173

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   ├── services/         # API client (api.js)
│   └── hooks/            # Custom React hooks
├── .env                  # Environment config
├── vite.config.js        # Vite + proxy config
└── package.json          # Dependencies
```

## 🛠️ Scripts

- `npm run dev` - Start dev server
- `npm run build` - Build for production
- `npm run lint` - Lint code
- `npm run format` - Format with Prettier

## 🔌 API Configuration

Set backend URL in `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```
