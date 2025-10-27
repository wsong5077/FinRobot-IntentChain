/**
 * IntentCore API Client
 */

import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const intentCoreAPI = {
  // Reviews
  getPendingReviews: (reviewerId) =>
    api.get('/reviews/pending', { params: { reviewer_id: reviewerId } }),

  submitReviewDecision: (chainId, decision) =>
    api.post(`/reviews/${chainId}/decision`, decision),

  // Chains
  getChain: (chainId) =>
    api.get(`/chains/${chainId}`),

  getChains: (params) =>
    api.get('/chains', { params }),

  // Metrics
  getMetrics: () =>
    api.get('/metrics'),

  getSummaryStats: () =>
    api.get('/metrics/summary'),

  // Execution
  recordExecution: (chainId, execution) =>
    api.post(`/chains/${chainId}/execution`, execution),
};

export default api;
