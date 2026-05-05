"use client";

import { useState } from 'react';
import { Upload, Play, Database, Clock, CheckCircle, AlertCircle } from 'lucide-react';

interface TrainingLog {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'error';
}

export default function ModelTrainingPage() {
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [logs, setLogs] = useState<TrainingLog[]>([
    { id: '1', timestamp: '2025-12-09 10:30:00', message: 'Model training initialized', type: 'info' },
    { id: '2', timestamp: '2025-12-09 10:30:15', message: 'Loading training dataset...', type: 'info' },
    { id: '3', timestamp: '2025-12-09 10:35:42', message: 'Training completed successfully', type: 'success' },
    { id: '4', timestamp: '2025-12-09 10:36:00', message: 'Model validated and saved', type: 'success' },
  ]);

  const handleStartTraining = () => {
    setIsTraining(true);
    setTrainingProgress(0);
    
    // Simulate training progress
    const interval = setInterval(() => {
      setTrainingProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsTraining(false);
          const newLog: TrainingLog = {
            id: Date.now().toString(),
            timestamp: new Date().toLocaleString(),
            message: 'Training completed successfully',
            type: 'success',
          };
          setLogs([newLog, ...logs]);
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  const stats = [
    {
      title: 'Training Data Count',
      value: '125,847',
      icon: Database,
      color: 'blue',
    },
    {
      title: 'Last Model Trained',
      value: '2 hours ago',
      icon: Clock,
      color: 'purple',
    },
    {
      title: 'Training Status',
      value: isTraining ? 'In Progress' : 'Ready',
      icon: isTraining ? AlertCircle : CheckCircle,
      color: isTraining ? 'yellow' : 'green',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Model Training</h1>
        <p className="text-gray-600 dark:text-gray-400">Train and manage AI models with your datasets.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const colorClasses = {
            blue: 'from-blue-500 to-blue-600',
            purple: 'from-purple-500 to-purple-600',
            green: 'from-green-500 to-green-600',
            yellow: 'from-yellow-500 to-yellow-600',
          };

          return (
            <div
              key={stat.title}
              className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                    {stat.title}
                  </p>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stat.value}
                  </h3>
                </div>
                <div
                  className={`w-12 h-12 bg-gradient-to-br ${colorClasses[stat.color as keyof typeof colorClasses]} rounded-xl flex items-center justify-center shadow-lg`}
                >
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Training Control */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Training Control</h2>
        
        {/* Upload Dataset */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Upload Training Data
          </label>
          <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-8 text-center hover:border-blue-500 dark:hover:border-blue-500 transition-colors cursor-pointer">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 mb-2">
              Drop your dataset files here, or click to browse
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Supports CSV, JSON, and TXT files (Max 500MB)
            </p>
            <button className="mt-4 px-6 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
              Select Files
            </button>
          </div>
        </div>

        {/* Start Training Button */}
        <div className="mb-6">
          <button
            onClick={handleStartTraining}
            disabled={isTraining}
            className={`w-full px-6 py-4 rounded-xl font-semibold flex items-center justify-center gap-3 transition-all duration-200 ${
              isTraining
                ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg hover:shadow-xl transform hover:scale-[1.02]'
            }`}
          >
            <Play className="w-5 h-5" />
            {isTraining ? 'Training in Progress...' : 'Start Training'}
          </button>
        </div>

        {/* Training Progress */}
        {(isTraining || trainingProgress > 0) && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-gray-700 dark:text-gray-300">Training Progress</span>
              <span className="font-bold text-gray-900 dark:text-white">{trainingProgress}%</span>
            </div>
            <div className="w-full h-3 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500 rounded-full"
                style={{ width: `${trainingProgress}%` }}
              />
            </div>
            {isTraining && (
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                Processing epoch 3/10 - This may take several minutes...
              </p>
            )}
          </div>
        )}
      </div>

      {/* Training Logs */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Training Logs</h2>
          <button className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
            Clear Logs
          </button>
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          <div className="p-6 space-y-3 font-mono text-sm">
            {logs.map((log) => (
              <div
                key={log.id}
                className={`flex items-start gap-3 p-3 rounded-lg ${
                  log.type === 'success'
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : log.type === 'error'
                    ? 'bg-red-50 dark:bg-red-900/20'
                    : 'bg-blue-50 dark:bg-blue-900/20'
                }`}
              >
                {log.type === 'success' ? (
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                ) : log.type === 'error' ? (
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{log.timestamp}</p>
                  <p
                    className={`${
                      log.type === 'success'
                        ? 'text-green-800 dark:text-green-300'
                        : log.type === 'error'
                        ? 'text-red-800 dark:text-red-300'
                        : 'text-blue-800 dark:text-blue-300'
                    }`}
                  >
                    {log.message}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Model Configuration */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Model Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Learning Rate
            </label>
            <input
              type="number"
              defaultValue="0.001"
              step="0.0001"
              className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Batch Size
            </label>
            <input
              type="number"
              defaultValue="32"
              className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Epochs
            </label>
            <input
              type="number"
              defaultValue="10"
              className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Validation Split
            </label>
            <input
              type="number"
              defaultValue="0.2"
              step="0.1"
              className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
