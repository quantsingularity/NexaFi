import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MobileProviders, useAuth } from './contexts/MobileContext';
import MobileHomepage from './components/MobileHomepage';
import MobileAuthPage from './components/MobileAuthPage';
import MobileLayout from './components/MobileLayout';
import MobileDashboard from './components/MobileDashboard';
import MobileAccountingModule from './components/MobileAccountingModule';
import './App.css';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/auth" replace />;
};

// App Routes Component
const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<MobileHomepage />} />
      <Route path="/auth" element={
        isAuthenticated ? <Navigate to="/dashboard" replace /> : <MobileAuthPage />
      } />
      
      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <MobileLayout>
            <MobileDashboard />
          </MobileLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/accounting" element={
        <ProtectedRoute>
          <MobileLayout>
            <MobileAccountingModule />
          </MobileLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/payments" element={
        <ProtectedRoute>
          <MobileLayout>
            <div className="p-4">
              <h1 className="text-2xl font-bold">Payments</h1>
              <p className="text-gray-600">Mobile payments module coming soon!</p>
            </div>
          </MobileLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/ai-insights" element={
        <ProtectedRoute>
          <MobileLayout>
            <div className="p-4">
              <h1 className="text-2xl font-bold">AI Insights</h1>
              <p className="text-gray-600">Mobile AI insights module coming soon!</p>
            </div>
          </MobileLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/settings" element={
        <ProtectedRoute>
          <MobileLayout>
            <div className="p-4">
              <h1 className="text-2xl font-bold">Settings</h1>
              <p className="text-gray-600">Mobile settings module coming soon!</p>
            </div>
          </MobileLayout>
        </ProtectedRoute>
      } />
      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <MobileProviders>
      <Router>
        <div className="App">
          <AppRoutes />
        </div>
      </Router>
    </MobileProviders>
  );
}

export default App;

