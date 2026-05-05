"use client";

import { useState } from 'react';
import { Filter, Download, Activity, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

interface SystemLog {
  id: string;
  timestamp: string;
  user: string;
  category: 'API' | 'Auth' | 'Training' | 'System';
  message: string;
  level: 'info' | 'warning' | 'error' | 'success';
}

const peakUsageData = [
  { hour: '00:00', requests: 120 },
  { hour: '03:00', requests: 80 },
  { hour: '06:00', requests: 150 },
  { hour: '09:00', requests: 450 },
  { hour: '12:00', requests: 680 },
  { hour: '15:00', requests: 720 },
  { hour: '18:00', requests: 590 },
  { hour: '21:00', requests: 380 },
];

const queryTypeData = [
  { type: 'Math Help', count: 342 },
  { type: 'Code Debug', count: 287 },
  { type: 'Essay Writing', count: 198 },
  { type: 'Translation', count: 165 },
  { type: 'Other', count: 142 },
];

const systemLogs: SystemLog[] = [
  { id: '1', timestamp: '2025-12-09 11:45:23', user: 'john.doe@example.com', category: 'API', message: 'API request completed successfully', level: 'success' },
  { id: '2', timestamp: '2025-12-09 11:44:15', user: 'sarah.smith@example.com', category: 'Auth', message: 'User login successful', level: 'info' },
  { id: '3', timestamp: '2025-12-09 11:43:08', user: 'system', category: 'Training', message: 'Model training completed', level: 'success' },
  { id: '4', timestamp: '2025-12-09 11:42:30', user: 'mike.jones@example.com', category: 'API', message: 'Rate limit exceeded', level: 'warning' },
  { id: '5', timestamp: '2025-12-09 11:41:55', user: 'emma.wilson@example.com', category: 'System', message: 'Database connection timeout', level: 'error' },
  { id: '6', timestamp: '2025-12-09 11:40:12', user: 'david.brown@example.com', category: 'Auth', message: 'Password reset requested', level: 'info' },
  { id: '7', timestamp: '2025-12-09 11:39:45', user: 'lisa.anderson@example.com', category: 'API', message: 'Content generation completed', level: 'success' },
  { id: '8', timestamp: '2025-12-09 11:38:22', user: 'james.taylor@example.com', category: 'System', message: 'Cache cleared successfully', level: 'info' },
];

export default function LogsAnalyticsPage() {
  const [logs, setLogs] = useState<SystemLog[]>(systemLogs);
  const [filterCategory, setFilterCategory] = useState<'All' | 'API' | 'Auth' | 'Training' | 'System'>('All');
  const [filterLevel, setFilterLevel] = useState<'All' | 'info' | 'warning' | 'error' | 'success'>('All');
  const [dateFilter, setDateFilter] = useState('today');

  const filteredLogs = logs.filter((log) => {
    const matchesCategory = filterCategory === 'All' || log.category === filterCategory;
    const matchesLevel = filterLevel === 'All' || log.level === filterLevel;
    return matchesCategory && matchesLevel;
  });

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Logs & Analytics</h1>
          <p className="text-gray-600 dark:text-gray-400">Monitor system activities and analyze usage patterns.</p>
        </div>
        <button className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 flex items-center gap-2">
          <Download className="w-5 h-5" />
          Export Logs
        </button>
      </div>

      {/* System Health Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">System Status</span>
          </div>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">Healthy</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Uptime</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">99.8%</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Warnings</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">12</p>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Errors</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">3</p>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Peak Usage Hours */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Peak Usage Hours</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={peakUsageData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="hour" stroke="#6b7280" style={{ fontSize: '12px' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Line
                type="monotone"
                dataKey="requests"
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ fill: '#3b82f6', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Most Common User Queries */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Most Common Queries</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={queryTypeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="type" stroke="#6b7280" style={{ fontSize: '12px' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Date Range
            </label>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            >
              <option value="today">Today</option>
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Category
            </label>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value as typeof filterCategory)}
                className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
              >
                <option value="All">All Categories</option>
                <option value="API">API</option>
                <option value="Auth">Authentication</option>
                <option value="Training">Training</option>
                <option value="System">System</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Log Level
            </label>
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(e.target.value as typeof filterLevel)}
              className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            >
              <option value="All">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="success">Success</option>
            </select>
          </div>
        </div>
      </div>

      {/* System Logs Table */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">System Logs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Level
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {log.timestamp}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {log.user}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                      {log.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {log.message}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div
                      className={`flex items-center gap-2 ${
                        log.level === 'success'
                          ? 'text-green-600 dark:text-green-400'
                          : log.level === 'error'
                          ? 'text-red-600 dark:text-red-400'
                          : log.level === 'warning'
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-blue-600 dark:text-blue-400'
                      }`}
                    >
                      {getLevelIcon(log.level)}
                      <span className="text-xs font-semibold uppercase">{log.level}</span>
                    </div>
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
