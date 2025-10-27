import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Edit, AlertTriangle, TrendingUp, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { intentCoreAPI } from '../utils/api';

export default function ReviewDetail() {
  const { chainId } = useParams();
  const navigate = useNavigate();
  const [decision, setDecision] = useState('');
  const [rationale, setRationale] = useState('');
  const [showModification, setShowModification] = useState(false);

  const { data: chain, isLoading } = useQuery({
    queryKey: ['chain', chainId],
    queryFn: () => intentCoreAPI.getChain(chainId).then(res => res.data),
  });

  const submitDecisionMutation = useMutation({
    mutationFn: (decisionData) =>
      intentCoreAPI.submitReviewDecision(chainId, decisionData),
    onSuccess: () => {
      navigate('/');
    },
  });

  const handleSubmit = () => {
    if (!decision || !rationale) {
      alert('Please select a decision and provide rationale');
      return;
    }

    submitDecisionMutation.mutate({
      reviewer_id: 'sarah_chen', // In production, get from auth
      decision: decision,
      rationale: rationale,
      modification: showModification ? {} : null, // TODO: Implement modification UI
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!chain) {
    return (
      <div className="card">
        <p className="text-danger-600">Chain not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/')}
              className="text-gray-500 hover:text-gray-700"
            >
              ← Back to Queue
            </button>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mt-2">Review Decision</h2>
          <p className="text-gray-500 mt-1">{chain.agent_role}</p>
        </div>
        <div className="text-right text-sm text-gray-500">
          <div>Chain ID: {chain.chain_id.slice(0, 8)}</div>
          <div className="flex items-center justify-end mt-1">
            <Clock className="w-4 h-4 mr-1" />
            {formatDistanceToNow(new Date(chain.timestamp), { addSuffix: true })}
          </div>
        </div>
      </div>

      {/* Task */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-2">Task</h3>
        <p className="text-gray-700">{chain.task}</p>
      </div>

      {/* Proposed Action */}
      <div className="card border-2 border-primary-200 bg-primary-50">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-3">
              <TrendingUp className="w-6 h-6 text-primary-600" />
              <h3 className="text-lg font-semibold">Proposed Action</h3>
            </div>

            <div className="bg-white rounded-lg p-4 space-y-3">
              <div>
                <span className="text-sm text-gray-500">Function:</span>
                <span className="ml-2 font-mono font-semibold text-gray-900">
                  {chain.selected_action.function}
                </span>
              </div>

              {chain.selected_action.parameters && (
                <div>
                  <span className="text-sm text-gray-500">Parameters:</span>
                  <pre className="mt-2 bg-gray-50 p-3 rounded text-sm font-mono overflow-x-auto">
                    {JSON.stringify(chain.selected_action.parameters, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Reasoning */}
      <div className="grid grid-cols-2 gap-6">
        {/* Situation */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-3">Situation</h3>
          <p className="text-gray-700 whitespace-pre-wrap">{chain.situation || 'Not provided'}</p>
        </div>

        {/* Analysis */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-3">Quantitative Analysis</h3>
          <div className="space-y-2">
            {chain.quantitative_analysis.amounts?.length > 0 && (
              <div>
                <span className="text-sm text-gray-500">Amounts:</span>
                <div className="mt-1 space-x-2">
                  {chain.quantitative_analysis.amounts.map((amt, i) => (
                    <span key={i} className="inline-block bg-green-50 text-green-700 px-2 py-1 rounded text-sm font-mono">
                      {amt}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {chain.quantitative_analysis.percentages?.length > 0 && (
              <div>
                <span className="text-sm text-gray-500">Changes:</span>
                <div className="mt-1 space-x-2">
                  {chain.quantitative_analysis.percentages.map((pct, i) => (
                    <span key={i} className="inline-block bg-blue-50 text-blue-700 px-2 py-1 rounded text-sm font-mono">
                      {pct}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {Object.keys(chain.quantitative_analysis.metrics || {}).length > 0 && (
              <div>
                <span className="text-sm text-gray-500">Metrics:</span>
                <pre className="mt-1 bg-gray-50 p-2 rounded text-xs font-mono">
                  {JSON.stringify(chain.quantitative_analysis.metrics, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Rationale */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-3">Rationale</h3>
          <p className="text-gray-700 whitespace-pre-wrap">{chain.rationale || 'Not provided'}</p>
        </div>

        {/* Risks */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-warning-600" />
            Identified Risks
          </h3>
          {chain.risks && chain.risks.length > 0 ? (
            <ul className="space-y-2">
              {chain.risks.map((risk, i) => (
                <li key={i} className="flex items-start">
                  <span className="text-danger-500 mr-2">•</span>
                  <span className="text-gray-700">{risk}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 italic">No risks identified</p>
          )}
        </div>
      </div>

      {/* Policy Results */}
      {chain.policy_results && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-3">Policy Checks</h3>
          <div className="space-y-2">
            {chain.policy_results.violations?.length > 0 && (
              <div className="bg-danger-50 border border-danger-200 rounded-lg p-3">
                <h4 className="font-semibold text-danger-800 mb-2">Violations</h4>
                <ul className="space-y-1">
                  {chain.policy_results.violations.map((v, i) => (
                    <li key={i} className="text-danger-700 text-sm">• {v}</li>
                  ))}
                </ul>
              </div>
            )}
            {chain.policy_results.warnings?.length > 0 && (
              <div className="bg-warning-50 border border-warning-200 rounded-lg p-3">
                <h4 className="font-semibold text-warning-800 mb-2">Warnings</h4>
                <ul className="space-y-1">
                  {chain.policy_results.warnings.map((w, i) => (
                    <li key={i} className="text-warning-700 text-sm">• {w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Completeness */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-3">Reasoning Completeness</h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1 bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${
                chain.completeness_score >= 0.8 ? 'bg-success-500' :
                chain.completeness_score >= 0.6 ? 'bg-warning-500' :
                'bg-danger-500'
              }`}
              style={{ width: `${chain.completeness_score * 100}%` }}
            />
          </div>
          <span className="text-lg font-bold">
            {(chain.completeness_score * 100).toFixed(0)}%
          </span>
        </div>
        {chain.missing_components && chain.missing_components.length > 0 && (
          <div className="mt-3 text-sm text-gray-600">
            <span className="font-medium">Missing:</span> {chain.missing_components.join(', ')}
          </div>
        )}
      </div>

      {/* Decision Form */}
      <div className="card bg-gray-50 border-2 border-gray-300">
        <h3 className="text-lg font-semibold mb-4">Your Decision</h3>

        <div className="space-y-4">
          {/* Decision Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={() => setDecision('approved')}
              className={`flex-1 py-3 px-4 rounded-lg border-2 transition-all ${
                decision === 'approved'
                  ? 'bg-success-50 border-success-500 text-success-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:border-success-300'
              }`}
            >
              <CheckCircle className="w-5 h-5 inline mr-2" />
              Approve
            </button>
            <button
              onClick={() => setDecision('rejected')}
              className={`flex-1 py-3 px-4 rounded-lg border-2 transition-all ${
                decision === 'rejected'
                  ? 'bg-danger-50 border-danger-500 text-danger-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:border-danger-300'
              }`}
            >
              <XCircle className="w-5 h-5 inline mr-2" />
              Reject
            </button>
            <button
              onClick={() => { setDecision('modified'); setShowModification(true); }}
              className={`flex-1 py-3 px-4 rounded-lg border-2 transition-all ${
                decision === 'modified'
                  ? 'bg-warning-50 border-warning-500 text-warning-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:border-warning-300'
              }`}
            >
              <Edit className="w-5 h-5 inline mr-2" />
              Modify
            </button>
          </div>

          {/* Rationale */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rationale (required)
            </label>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Explain your decision..."
            />
          </div>

          {/* Submit */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => navigate('/')}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!decision || !rationale || submitDecisionMutation.isPending}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitDecisionMutation.isPending ? 'Submitting...' : 'Submit Decision'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
