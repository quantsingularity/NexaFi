# NexaFi Mobile Frontend

Enterprise-grade mobile-optimized frontend for the NexaFi financial platform built with React, Vite, and Tailwind CSS.

## 🚀 Features

- **Complete Financial Management Suite**
  - Real-time dashboard with financial metrics
  - Full accounting module with journal entries and reports
  - Payment processing with transaction history
  - AI-powered insights and predictions
  - Interactive AI chat assistant
  - Comprehensive user settings

- **Production-Ready**
  - Error boundaries for graceful error handling
  - Offline support with intelligent caching
  - Responsive design optimized for mobile devices
  - Protected routes with authentication
  - Real-time connectivity status
  - Comprehensive error handling

- **Developer Experience**
  - Hot module replacement (HMR)
  - ESLint configuration
  - Modern React patterns (hooks, context)
  - Component-based architecture
  - Comprehensive test coverage

## 📋 Prerequisites

- Node.js 18+ or npm 9+
- Backend API running (default: `http://localhost:5000`)
- Modern web browser with ES6+ support

## 🛠️ Installation

1. **Clone the repository** (if not already done)

   ```bash
   cd mobile-frontend
   ```

2. **Install dependencies**

   ```bash
   npm install --legacy-peer-deps
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env to match your backend URL if different from localhost:5000
   ```

## 🏃 Running the Application

### Development Mode

```bash
npm run dev
```

The application will start on `http://localhost:5173` (or the next available port).

### Production Build

```bash
npm run build
```

Built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 🧪 Testing

### Run all tests

```bash
npm test
```

### Run tests in watch mode

```bash
npm test -- --watch
```

### Run tests with coverage

```bash
npm test -- --coverage
```

## 📁 Project Structure

```
mobile-frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/              # Reusable UI components (shadcn/ui)
│   │   ├── MobileDashboard.jsx
│   │   ├── MobileAccountingModule.jsx
│   │   ├── MobilePaymentsModule.jsx
│   │   ├── MobileAIInsightsModule.jsx
│   │   ├── MobileSettingsModule.jsx
│   │   ├── MobileAuthPage.jsx
│   │   ├── MobileHomepage.jsx
│   │   ├── MobileLayout.jsx
│   │   └── ErrorBoundary.jsx
│   ├── contexts/            # React contexts
│   │   └── MobileContext.jsx
│   ├── lib/                 # Utilities and API client
│   │   ├── mobileApi.js
│   │   └── utils.js
│   ├── hooks/               # Custom React hooks
│   │   └── use-mobile.js
│   ├── assets/              # Static assets
│   ├── App.jsx              # Main app component
│   ├── App.css              # App styles
│   ├── index.css            # Global styles
│   └── main.jsx             # App entry point
├── public/                  # Public static files
├── tests/                   # Test files
├── .env.example             # Environment template
├── .env                     # Environment configuration
├── package.json             # Dependencies
├── vite.config.js           # Vite configuration
├── eslint.config.js         # ESLint configuration
├── components.json          # shadcn/ui configuration
└── README.md                # This file
```

## 🔌 Backend Integration

### API Endpoints Used

The mobile frontend integrates with the following backend endpoints:

#### Authentication

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile

#### Dashboard

- `GET /api/v1/dashboard` - Get dashboard data
- `GET /api/v1/dashboard/financial-summary` - Get financial summary

#### Accounting

- `GET /api/v1/accounts` - List accounts
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/journal-entries` - List journal entries
- `POST /api/v1/journal-entries` - Create journal entry
- `GET /api/v1/reports/:type` - Get financial reports

#### Payments

- `GET /api/v1/payment-methods` - List payment methods
- `POST /api/v1/payment-methods` - Add payment method
- `GET /api/v1/transactions` - List transactions
- `POST /api/v1/transactions` - Create transaction
- `GET /api/v1/wallets` - List wallets

#### AI Services

- `GET /api/v1/insights` - Get AI insights
- `GET /api/v1/chat/sessions` - List chat sessions
- `POST /api/v1/chat/sessions/:id/messages` - Send chat message
- `POST /api/v1/predictions/:type` - Generate prediction

### Starting the Backend

Before running the mobile frontend, ensure the backend is running:

```bash
cd ../backend
python3 api-gateway/src/main.py
```

The API Gateway should be available at `http://localhost:5000`.

## 🎨 Styling

This project uses:

- **Tailwind CSS 4.x** for utility-first styling
- **shadcn/ui** for accessible, customizable components
- **Framer Motion** for animations
- **Lucide React** for icons

## 🔒 Authentication Flow

1. User navigates to `/auth`
2. User enters credentials (login) or registration info (signup)
3. Frontend sends credentials to backend `/api/v1/auth/login` or `/api/v1/auth/register`
4. Backend returns JWT token and user data
5. Token is stored in localStorage
6. Token is included in all subsequent API requests
7. On logout, token is removed and user is redirected to auth page

## 📱 Responsive Design

The application is optimized for:

- Mobile devices (320px - 767px)
- Tablets (768px - 1023px)
- Desktop (1024px+)

All components are touch-friendly and mobile-first.

## 🌐 Offline Support

The application includes offline capabilities:

- Automatic detection of online/offline status
- Visual indicators when offline
- Cached data for offline viewing
- Queued actions that sync when back online

## 🐛 Error Handling

Comprehensive error handling at multiple levels:

- **Error Boundaries**: Catch React component errors
- **API Error Handling**: Retry logic, timeout handling
- **User Feedback**: Toast notifications for all operations
- **Graceful Degradation**: Fallback UI when features unavailable

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:5000
VITE_API_TIMEOUT=30000
VITE_ENABLE_OFFLINE_MODE=true
VITE_ENABLE_PWA=true
VITE_DEV_MODE=true
VITE_LOG_LEVEL=debug
```

### Changing API URL

To point to a different backend:

1. Edit `.env`:

   ```env
   VITE_API_BASE_URL=https://your-backend-url.com
   ```

2. Restart the development server

## 📊 Performance

- First Contentful Paint (FCP): < 1.5s
- Time to Interactive (TTI): < 3.5s
- Lighthouse Score: 90+

## 🧩 Component Library

This project uses [shadcn/ui](https://ui.shadcn.com/) for base components. To add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

## 🤝 Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## 📝 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm test` - Run tests
- `npm test -- --watch` - Run tests in watch mode
- `npm test -- --coverage` - Run tests with coverage

## 🔐 Security

- All API requests include authentication tokens
- Passwords are never stored in localStorage
- HTTPS enforced in production
- Input validation on all forms
- XSS protection via React
- CSRF tokens for state-changing operations

## 📄 License

MIT License - see LICENSE file for details
