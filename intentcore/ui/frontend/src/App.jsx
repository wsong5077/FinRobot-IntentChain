import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { LayoutDashboard, CheckSquare, BarChart3 } from 'lucide-react';
import ReviewQueue from './pages/ReviewQueue';
import ReviewDetail from './pages/ReviewDetail';
import Dashboard from './pages/Dashboard';
import History from './pages/History';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <LayoutDashboard className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">IntentCore</h1>
                  <p className="text-xs text-gray-500">AI Agent Governance</p>
                </div>
              </div>

              <nav className="flex space-x-6">
                <Link
                  to="/"
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Review Queue
                </Link>
                <Link
                  to="/history"
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  History
                </Link>
                <Link
                  to="/dashboard"
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                >
                  Dashboard
                </Link>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<ReviewQueue />} />
            <Route path="/review/:chainId" element={<ReviewDetail />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
