import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { intentCoreAPI } from '../utils/api';

export default function History() {
  const { data: chains, isLoading } = useQuery({
    queryKey: ['chains'],
    queryFn: () => intentCoreAPI.getChains({ limit: 50 }).then(res => res.data),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Decision History</h2>
        <p className="text-gray-500 mt-1">Past agent decisions and reviews</p>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="pb-3">Time</th>
                <th className="pb-3">Agent</th>
                <th className="pb-3">Task</th>
                <th className="pb-3">Action</th>
                <th className="pb-3">Decision</th>
                <th className="pb-3">Reviewer</th>
                <th className="pb-3 text-right">Completeness</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {chains && chains.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    No decisions yet
                  </td>
                </tr>
              ) : (
                chains?.map((chain) => (
                  <tr key={chain.chain_id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-3">
                      <div className="flex items-center text-gray-600">
                        <Clock className="w-4 h-4 mr-1" />
                        {formatDistanceToNow(new Date(chain.timestamp), { addSuffix: true })}
                      </div>
                    </td>
                    <td className="py-3 text-gray-700">{chain.agent_role}</td>
                    <td className="py-3 text-gray-700 max-w-xs truncate" title={chain.task}>
                      {chain.task}
                    </td>
                    <td className="py-3">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {chain.selected_action?.function || 'N/A'}
                      </code>
                    </td>
                    <td className="py-3">
                      {chain.human_decision === 'approved' && (
                        <span className="badge-success">
                          <CheckCircle className="w-3 h-3 inline mr-1" />
                          Approved
                        </span>
                      )}
                      {chain.human_decision === 'rejected' && (
                        <span className="badge-danger">
                          <XCircle className="w-3 h-3 inline mr-1" />
                          Rejected
                        </span>
                      )}
                      {!chain.human_decision && chain.governance_decision === 'approved' && (
                        <span className="badge-primary">Auto-approved</span>
                      )}
                      {!chain.human_decision && chain.requires_review && (
                        <span className="badge-warning">Pending</span>
                      )}
                    </td>
                    <td className="py-3 text-gray-600">
                      {chain.reviewer_id || '-'}
                    </td>
                    <td className="py-3 text-right">
                      <span className={`font-semibold ${
                        chain.completeness_score >= 0.8 ? 'text-success-600' :
                        chain.completeness_score >= 0.6 ? 'text-warning-600' :
                        'text-danger-600'
                      }`}>
                        {(chain.completeness_score * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
