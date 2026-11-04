import { useState, useEffect } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || '/api';

/**
 * Shared Hook for Unified KPIs.
 * Single source of truth for all components (App header, LiveDashboard, Analytics, etc.)
 */
export function useUnifiedKpis(pollIntervalMs = 0) {
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchKpis = async () => {
    try {
      const res = await axios.get(`${API}/v1/kpis`);
      setKpis(res.data);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKpis();
    if (pollIntervalMs > 0) {
      const timer = setInterval(fetchKpis, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [pollIntervalMs]);

  return { kpis, loading, error, lastUpdated, refreshKpis: fetchKpis };
}
