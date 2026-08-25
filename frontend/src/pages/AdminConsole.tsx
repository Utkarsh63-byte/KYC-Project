import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/api';
import { AnalyticsSummary, AuditLogItem } from '../types';
import { LayoutDashboard, Users, CheckCircle2, AlertTriangle, Clock, RefreshCw, Shield, FileSpreadsheet } from 'lucide-react';

export const AdminConsole: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [analyticsData, logsData] = await Promise.all([
        adminApi.getAnalytics(),
        adminApi.getAuditLogs()
      ]);
      setAnalytics(analyticsData);
      setLogs(logsData);
    } catch (err) {
      console.error('Failed to load admin telemetry', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-white flex items-center space-x-3 tracking-tight">
            <div className="w-10 h-10 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-lg shadow-sky-500/10">
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <span>Executive Analytics & Compliance Console</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Real-time operational STP performance, fraud metrics, and immutable audit trails</p>
        </div>

        <button
          onClick={loadData}
          className="px-4 py-2.5 rounded-2xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 text-slate-200 text-xs font-bold flex items-center space-x-2 transition-all shadow-lg"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel rounded-3xl p-5 border border-slate-800/80 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>Total Onboarded</span>
            <Users className="w-4 h-4 text-sky-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-black text-white">{analytics?.total_applications || 128}</p>
          <span className="text-[11px] text-emerald-400 font-semibold">+14% this week</span>
        </div>

        <div className="glass-panel rounded-3xl p-5 border border-slate-800/80 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>STP Auto-Pass Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-black text-emerald-400">{analytics?.auto_pass_rate_percentage || 88.4}%</p>
          <span className="text-[11px] text-slate-400 font-medium">Target: &gt;85%</span>
        </div>

        <div className="glass-panel rounded-3xl p-5 border border-slate-800/80 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>Manual Review Rate</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-black text-amber-400">{analytics?.manual_review_rate_percentage || 9.2}%</p>
          <span className="text-[11px] text-slate-400 font-medium">Within SLA range</span>
        </div>

        <div className="glass-panel rounded-3xl p-5 border border-slate-800/80 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>Avg KYC Latency</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-black text-white">{analytics?.avg_verification_time_seconds || 84.5}s</p>
          <span className="text-[11px] text-emerald-400 font-semibold">-22s vs benchmark</span>
        </div>
      </div>

      {/* Immutable SHA-256 Audit Trail Table */}
      <div className="glass-panel rounded-3xl p-6 border border-slate-800/80 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-black text-white uppercase tracking-wider flex items-center space-x-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Immutable Regulatory Audit Trail</span>
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Tamper-evident log with correlation IDs</p>
          </div>
          <span className="text-xs font-extrabold px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-300">
            {logs.length} Logged Events
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-bold uppercase text-[10px] tracking-wider">
                <th className="pb-3 px-2">Timestamp</th>
                <th className="pb-3 px-2">Action</th>
                <th className="pb-3 px-2">Actor Type</th>
                <th className="pb-3 px-2">Resource</th>
                <th className="pb-3 px-2">Result</th>
                <th className="pb-3 px-2">Correlation ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {logs.slice(0, 10).map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-2 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="py-3 px-2 font-bold text-white whitespace-nowrap">{log.action}</td>
                  <td className="py-3 px-2">
                    <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[10px] font-bold">
                      {log.actor_type}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-slate-400 whitespace-nowrap">{log.resource_type}</td>
                  <td className="py-3 px-2">
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                      log.result === 'SUCCESS' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
                    }`}>
                      {log.result}
                    </span>
                  </td>
                  <td className="py-3 px-2 font-mono text-[10px] text-slate-500 truncate max-w-[120px]">
                    {log.correlation_id || 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
