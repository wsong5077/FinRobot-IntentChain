import { useQuery } from '@tanstack/react-query';
import { TrendingUp, CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react';
import { intentCoreAPI } from '../utils/api';

export default function Dashboard() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => intentCoreAPI.getMetrics().then(res => res.data),
    refetchInterval: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const summary = metrics?.summary || {};
  const daily = metrics?.daily || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-500 mt-1">System performance and metrics</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Decisions"
          value={summary.total_decisions || 0}
          icon={<TrendingUp className="w-6 h-6" />}
          color="primary"
        />
        <MetricCard
          title="Approved"
          value={summary.total_approved || 0}
          icon={<CheckCircle className="w-6 h-6" />}
          color="success"
        />
        <MetricCard
          title="Rejected"
          value={summary.total_rejected || 0}
          icon={<XCircle className="w-6 h-6" />}
          color="danger"
        />
        <MetricCard
          title="Reviews Required"
          value={summary.total_reviews || 0}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="warning"
        />
      </div>

      {/* Completeness */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Average Reasoning Completeness</h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1 bg-gray-200 rounded-full h-4">
            <div
              className="bg-success-500 h-4 rounded-full transition-all"
              style={{ width: `${(summary.avg_completeness || 0) * 100}%` }}
            />
          </div>
          <span className="text-2xl font-bold">
            {((summary.avg_completeness || 0) * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Daily Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="pb-2">Date</th>
                <th className="pb-2 text-right">Decisions</th>
                <th className="pb-2 text-right">Reviews</th>
                <th className="pb-2 text-right">Approved</th>
                <th className="pb-2 text-right">Rejected</th>
                <th className="pb-2 text-right">Completeness</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {daily.slice(0, 10).map((day, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2">{day.date}</td>
                  <td className="py-2 text-right">{day.total_decisions || 0}</td>
                  <td className="py-2 text-right">{day.reviews_required || 0}</td>
                  <td className="py-2 text-right text-success-600">{day.approved || 0}</td>
                  <td className="py-2 text-right text-danger-600">{day.rejected || 0}</td>
                  <td className="py-2 text-right">
                    {day.avg_completeness ? `${(day.avg_completeness * 100).toFixed(0)}%` : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, color }) {
  const colors = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    danger: 'bg-danger-50 text-danger-600',
    warning: 'bg-warning-50 text-warning-600',
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-500 text-sm">{title}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
