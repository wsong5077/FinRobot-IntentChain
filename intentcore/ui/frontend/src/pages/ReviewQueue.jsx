import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Clock, AlertTriangle, TrendingUp, DollarSign } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { intentCoreAPI } from '../utils/api';

export default function ReviewQueue() {
  const { data: reviews, isLoading, error, refetch } = useQuery({
    queryKey: ['pendingReviews'],
    queryFn: () => intentCoreAPI.getPendingReviews().then(res => res.data),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card bg-danger-50 border border-danger-200">
        <p className="text-danger-800">Error loading reviews: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Review Queue</h2>
          <p className="text-gray-500 mt-1">
            {reviews?.length || 0} pending decision{reviews?.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn-secondary"
        >
          Refresh
        </button>
      </div>

      {/* Reviews */}
      {reviews && reviews.length === 0 ? (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-success-50 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-success-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900">All caught up!</h3>
          <p className="text-gray-500 mt-2">No pending reviews at the moment.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews?.map((review) => (
            <ReviewCard key={review.queue_id} review={review} />
          ))}
        </div>
      )}
    </div>
  );
}

function ReviewCard({ review }) {
  const chain = review.chain;
  const action = chain.selected_action;
  const params = action.parameters || {};

  // Extract trade amount
  const tradeAmount = params.amount || params.value || params.quantity;
  const symbol = params.symbol || params.asset || 'N/A';

  // Priority badge
  const priorityColors = {
    urgent: 'bg-danger-100 text-danger-800 border-danger-200',
    high: 'bg-warning-100 text-warning-800 border-warning-200',
    normal: 'bg-primary-100 text-primary-800 border-primary-200',
    low: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  return (
    <Link to={`/review/${chain.chain_id}`} className="block">
      <div className="card hover:shadow-lg transition-shadow cursor-pointer border border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center space-x-3 mb-3">
              <span className={`badge border ${priorityColors[review.priority]}`}>
                {review.priority.toUpperCase()}
              </span>
              <span className="text-sm text-gray-500">
                {chain.agent_role}
              </span>
              <span className="text-sm text-gray-400">
                <Clock className="w-4 h-4 inline mr-1" />
                {formatDistanceToNow(new Date(review.queued_at), { addSuffix: true })}
              </span>
            </div>

            {/* Task */}
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {chain.task}
            </h3>

            {/* Action Summary */}
            <div className="flex items-center space-x-4 mb-3">
              <div className="flex items-center text-gray-700">
                <TrendingUp className="w-5 h-5 mr-2 text-primary-600" />
                <span className="font-medium">{action.function || 'Action'}</span>
              </div>
              {symbol && (
                <div className="text-gray-600">
                  <span className="font-mono font-semibold">{symbol}</span>
                </div>
              )}
              {tradeAmount && (
                <div className="flex items-center text-gray-700">
                  <DollarSign className="w-5 h-5 mr-1 text-green-600" />
                  <span className="font-semibold">{formatAmount(tradeAmount)}</span>
                </div>
              )}
            </div>

            {/* Situation snippet */}
            <p className="text-gray-600 text-sm line-clamp-2">
              {chain.situation || 'No situation description'}
            </p>

            {/* Completeness & Warnings */}
            <div className="flex items-center space-x-4 mt-3">
              <div className="text-sm">
                <span className="text-gray-500">Completeness:</span>
                <span className={`ml-2 font-semibold ${
                  chain.completeness_score >= 0.8 ? 'text-success-600' :
                  chain.completeness_score >= 0.6 ? 'text-warning-600' :
                  'text-danger-600'
                }`}>
                  {(chain.completeness_score * 100).toFixed(0)}%
                </span>
              </div>

              {chain.policy_results && chain.policy_results.violations?.length > 0 && (
                <div className="flex items-center text-danger-600 text-sm">
                  <AlertTriangle className="w-4 h-4 mr-1" />
                  <span>{chain.policy_results.violations.length} violation(s)</span>
                </div>
              )}
            </div>
          </div>

          {/* Chevron */}
          <div className="ml-4">
            <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </Link>
  );
}

function formatAmount(amount) {
  if (typeof amount === 'string') {
    return amount;
  }

  const num = parseFloat(amount);
  if (num >= 1_000_000) {
    return `$${(num / 1_000_000).toFixed(1)}M`;
  } else if (num >= 1_000) {
    return `$${(num / 1_000).toFixed(1)}K`;
  }
  return `$${num.toFixed(2)}`;
}
