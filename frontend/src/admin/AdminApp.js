import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Ban,
  BarChart3,
  Bell,
  BookOpen,
  Brain,
  CheckCircle,
  ChevronDown,
  Code,
  Cpu,
  Database,
  Download,
  Edit,
  FileText,
  Filter,
  Globe,
  Key,
  LayoutDashboard,
  List,
  Lock,
  Mail,
  MessageSquare,
  Moon,
  Play,
  Plus,
  Save,
  Search,
  Shield,
  Sparkles,
  Sun,
  Trash2,
  TrendingDown,
  TrendingUp,
  Upload,
  User,
  UserPlus,
  Users,
  X,
  Clock,
  Info,
  Settings,
  Bold,
  Italic,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  Cell,
  CartesianGrid,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import './admin.css';

const ADMIN_EMAIL = 'umerazizgujjar009@gmail.com';
const ADMIN_PASSWORD = 'Umer@0900';
const ADMIN_SESSION_KEY = 'admin_authenticated';

const usageData = [
  { date: 'Mon', requests: 1200 },
  { date: 'Tue', requests: 1800 },
  { date: 'Wed', requests: 1600 },
  { date: 'Thu', requests: 2100 },
  { date: 'Fri', requests: 2400 },
  { date: 'Sat', requests: 1900 },
  { date: 'Sun', requests: 1500 },
];

const requestTypeData = [
  { name: 'Text Generation', value: 45, color: '#3b82f6' },
  { name: 'Coding Help', value: 30, color: '#8b5cf6' },
  { name: 'Learning Help', value: 25, color: '#06b6d4' },
];

const recentActivity = [
  { id: 1, user: 'john.doe@example.com', action: 'New Registration', time: '2 mins ago', status: 'success' },
  { id: 2, user: 'sarah.smith@example.com', action: 'Model Update', time: '15 mins ago', status: 'info' },
  { id: 3, user: 'mike.jones@example.com', action: 'Content Flagged', time: '1 hour ago', status: 'warning' },
  { id: 4, user: 'emma.wilson@example.com', action: 'New Registration', time: '2 hours ago', status: 'success' },
  { id: 5, user: 'david.brown@example.com', action: 'API Request', time: '3 hours ago', status: 'info' },
];

const kpiCards = [
  { title: 'Total Users', value: '12,459', change: '+12.5%', trend: 'up', icon: Users, color: 'blue' },
  { title: 'Active Sessions', value: '1,234', change: '+8.2%', trend: 'up', icon: Activity, color: 'green' },
  { title: 'AI Model Status', value: 'Healthy', change: '99.8% uptime', trend: 'up', icon: Cpu, color: 'purple' },
  { title: 'Total Requests', value: '87.5K', change: '-3.1%', trend: 'down', icon: MessageSquare, color: 'cyan' },
];

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/admin/dashboard' },
  { icon: FileText, label: 'Content Management', href: '/admin/dashboard/content' },
  { icon: BarChart3, label: 'Logs & Analytics', href: '/admin/dashboard/analytics' },
  { icon: Settings, label: 'Settings', href: '/admin/dashboard/settings' },
];

const adminInitialUsers = [
  { id: '1', email: 'john.doe@example.com', role: 'Student', status: 'Active', lastLogin: '2025-12-09 10:30 AM' },
  { id: '2', email: 'sarah.smith@example.com', role: 'Admin', status: 'Active', lastLogin: '2025-12-09 09:15 AM' },
  { id: '3', email: 'mike.jones@example.com', role: 'Student', status: 'Blocked', lastLogin: '2025-12-08 03:45 PM' },
  { id: '4', email: 'emma.wilson@example.com', role: 'Student', status: 'Active', lastLogin: '2025-12-09 08:20 AM' },
  { id: '5', email: 'david.brown@example.com', role: 'Student', status: 'Active', lastLogin: '2025-12-09 07:55 AM' },
  { id: '6', email: 'lisa.anderson@example.com', role: 'Admin', status: 'Active', lastLogin: '2025-12-09 11:10 AM' },
  { id: '7', email: 'james.taylor@example.com', role: 'Student', status: 'Active', lastLogin: '2025-12-08 05:30 PM' },
  { id: '8', email: 'maria.garcia@example.com', role: 'Student', status: 'Blocked', lastLogin: '2025-12-07 02:15 PM' },
];

const adminInitialContent = [
  { id: '1', title: 'Introduction to Calculus', category: 'Mathematics', type: 'Lesson', lastUpdated: '2025-12-09', status: 'Published' },
  { id: '2', title: 'Python Basics Tutorial', category: 'Programming', type: 'Lesson', lastUpdated: '2025-12-08', status: 'Published' },
  { id: '3', title: 'Creative Writing Prompt', category: 'AI Prompts', type: 'Prompt', lastUpdated: '2025-12-09', status: 'Published' },
  { id: '4', title: 'Physics Problem Set', category: 'Science', type: 'Exercise', lastUpdated: '2025-12-07', status: 'Draft' },
  { id: '5', title: 'Spanish Vocabulary', category: 'Languages', type: 'Lesson', lastUpdated: '2025-12-09', status: 'Published' },
  { id: '6', title: 'Code Debug Challenge', category: 'Programming', type: 'Exercise', lastUpdated: '2025-12-06', status: 'Published' },
];

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

const systemLogs = [
  { id: '1', timestamp: '2025-12-09 11:45:23', user: 'john.doe@example.com', category: 'API', message: 'API request completed successfully', level: 'success' },
  { id: '2', timestamp: '2025-12-09 11:44:15', user: 'sarah.smith@example.com', category: 'Auth', message: 'User login successful', level: 'info' },
  { id: '3', timestamp: '2025-12-09 11:43:08', user: 'system', category: 'Training', message: 'Model training completed', level: 'success' },
  { id: '4', timestamp: '2025-12-09 11:42:30', user: 'mike.jones@example.com', category: 'API', message: 'Rate limit exceeded', level: 'warning' },
  { id: '5', timestamp: '2025-12-09 11:41:55', user: 'emma.wilson@example.com', category: 'System', message: 'Database connection timeout', level: 'error' },
  { id: '6', timestamp: '2025-12-09 11:40:12', user: 'david.brown@example.com', category: 'Auth', message: 'Password reset requested', level: 'info' },
  { id: '7', timestamp: '2025-12-09 11:39:45', user: 'lisa.anderson@example.com', category: 'API', message: 'Content generation completed', level: 'success' },
  { id: '8', timestamp: '2025-12-09 11:38:22', user: 'james.taylor@example.com', category: 'System', message: 'Cache cleared successfully', level: 'info' },
];

function useAdminTheme() {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light';
    return window.localStorage.getItem('theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    window.localStorage.setItem('theme', theme);
  }, [theme]);

  return {
    theme,
    toggleTheme: () => setTheme((current) => (current === 'light' ? 'dark' : 'light')),
  };
}

function pathToPage(pathname) {
  if (!pathname || pathname === '/admin' || pathname === '/admin/' || pathname === '/admin/login') {
    return 'login';
  }

  if (pathname.startsWith('/admin/dashboard/content')) return 'content';
  if (pathname.startsWith('/admin/dashboard/analytics')) return 'analytics';
  if (pathname.startsWith('/admin/dashboard/settings')) return 'settings';
  return 'dashboard';
}

function AdminLoginPage({ theme, toggleTheme, onNavigate }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.sessionStorage.getItem(ADMIN_SESSION_KEY) === 'true') {
      onNavigate('/admin/dashboard');
    }
  }, [onNavigate]);

  const handleLogin = (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    const normalizedEmail = String(email || '').toLowerCase().trim();
    const normalizedPassword = String(password || '');

    if (normalizedEmail === ADMIN_EMAIL && normalizedPassword === ADMIN_PASSWORD) {
      if (typeof window !== 'undefined') {
        window.sessionStorage.setItem(ADMIN_SESSION_KEY, 'true');
      }
      onNavigate('/admin/dashboard');
      return;
    }

    setError('Invalid admin credentials. Use the configured admin email and password.');
    setIsSubmitting(false);
  };

  return (
    <div className="admin-root admin-login-page">
      <div className="admin-blob blue" />
      <div className="admin-blob purple" />

      <button className="admin-login-toggle" onClick={toggleTheme} aria-label="Toggle theme" type="button">
        {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
      </button>

      <div className="admin-login-card admin-login-card-dark">
        <div className="admin-login-brand">
          <div className="admin-logo">
            <Sparkles size={30} />
          </div>
          <div>
            <h1 className="admin-title">GenCal AI</h1>
            <p className="admin-subtitle">Secure Admin Login</p>
          </div>
        </div>

        <div className="admin-login-copy">
          <h2>Access the admin console</h2>
          <p>Use the dedicated admin credentials to open the dashboard. User login is not accepted here.</p>
        </div>

        <form className="admin-form" onSubmit={handleLogin}>
          {error && <div className="admin-error-banner">{error}</div>}

          <div className="admin-field">
            <label>Email Address</label>
            <div className="admin-input-wrap">
              <Mail size={18} className="admin-icon-left" />
              <input
                className="admin-input with-icon"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="umerazizgujjar009@gmail.com"
                required
                autoComplete="username"
              />
            </div>
          </div>

          <div className="admin-field">
            <label>Password</label>
            <div className="admin-input-wrap">
              <Lock size={18} className="admin-icon-left" />
              <input
                className="admin-input with-icon"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <div className="admin-row-between admin-fine">
            <label className="admin-checkbox-row">
              <input type="checkbox" />
              <span>Remember me</span>
            </label>
              <button type="button" className="admin-link" style={{ border: 0, background: 'transparent', padding: 0 }}>Forgot password?</button>
          </div>

          <button className="admin-btn primary" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Verifying...' : 'Sign In'}
          </button>
        </form>

        <div className="admin-footer-note">Protected by GenCal AI Security</div>

        <div className="admin-signup-help admin-signup-help-right">
          Need help? Contact <a href="mailto:support@gencal.ai" className="admin-link">support@gencal.ai</a>
        </div>
      </div>
    </div>
  );
}

function AdminSidebar({ pathname, onNavigate }) {
  const activePath = pathname || '/admin/dashboard';

  return (
    <aside className="admin-sidebar">
      <div className="admin-sidebar-brand">
        <div className="admin-logo" style={{ width: 34, height: 34, borderRadius: 10 }}>
          <Sparkles size={18} />
        </div>
        <strong style={{ fontSize: 20, background: 'linear-gradient(90deg, #2563eb, #7c3aed)', WebkitBackgroundClip: 'text', color: 'transparent' }}>
          GenCal AI
        </strong>
      </div>

      <nav className="admin-sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePath === item.href;
          return (
            <button
              key={item.href}
              className={`admin-nav-item ${isActive ? 'active' : ''}`}
              type="button"
              onClick={() => onNavigate(item.href)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="admin-sidebar-footer">
        <div className="admin-sidebar-footer-card">
          <div style={{ fontSize: 12, fontWeight: 700, color: '#6b7280' }}>Admin Panel v1.0</div>
          <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>© 2025 GenCal AI</div>
        </div>
      </div>
    </aside>
  );
}

function AdminNavbar({ theme, toggleTheme, onNavigate }) {
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  return (
    <div className="admin-shell-navbar" onClick={(event) => event.stopPropagation()}>
      <div className="admin-navbar-left" style={{ position: 'relative' }}>
        <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
        <input className="admin-search" type="text" placeholder="Search anything..." />
      </div>

      <div className="admin-navbar-right">
        <button className="admin-navbar-action" type="button" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        <button className="admin-navbar-action" type="button" aria-label="Notifications">
          <Bell size={18} />
        </button>

        <div style={{ position: 'relative' }}>
          <button
            className="admin-profile-btn"
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              setProfileMenuOpen((open) => !open);
            }}
          >
            <div className="admin-avatar">A</div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>Admin User</div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>admin@gencal.ai</div>
            </div>
            <ChevronDown size={16} />
          </button>

          {profileMenuOpen && (
            <div className="admin-profile-menu" onClick={(event) => event.stopPropagation()}>
              <button type="button">Profile</button>
              <button type="button">Settings</button>
                <button
                  type="button"
                  onClick={() => {
                    if (typeof window !== 'undefined') {
                      window.sessionStorage.removeItem(ADMIN_SESSION_KEY);
                    }
                    onNavigate('/admin/login');
                  }}
                >
                  Logout
                </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DashboardPage() {
  const [callLogs, setCallLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState('');

  useEffect(() => {
    let active = true;
    const loadCallLogs = async () => {
      setIsLoading(true);
      setDashboardError('');

      try {
        const response = await fetch('/api/call_logs/');
        if (!response.ok) {
          const message = await response.text();
          throw new Error(message || response.statusText || 'Unable to load backend call logs');
        }
        const data = await response.json();
        const records = Array.isArray(data.calls) ? data.calls : [];

        const formatted = records.map((entry) => ({
          ...entry,
          duration: Number(entry.duration) || 0,
          timestamp: entry.timestamp || new Date().toISOString(),
        }));

        if (active) setCallLogs(formatted);
      } catch (error) {
        console.error('Dashboard call log fetch error:', error);
        if (active) setDashboardError('Could not load call logs from the backend.');
      } finally {
        if (active) setIsLoading(false);
      }
    };

    loadCallLogs();
    return () => {
      active = false;
    };
  }, []);

  const formatDuration = (seconds) => {
    const secs = Number(seconds) || 0;
    const mins = Math.floor(secs / 60);
    const remaining = secs % 60;
    return `${mins}:${remaining.toString().padStart(2, '0')}`;
  };

  const totalCalls = callLogs.length;
  const totalDuration = callLogs.reduce((sum, log) => sum + log.duration, 0);
  const averageDuration = totalCalls ? Math.round(totalDuration / totalCalls) : 0;

  const statusCounts = callLogs.reduce((acc, log) => {
    const status = log.call_status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  const statusChartData = Object.entries(statusCounts).map(([name, value], index) => ({
    name,
    value,
    color: ['#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b', '#ec4899'][index % 5],
  }));

  const callCountByDay = callLogs.reduce((acc, log) => {
    const day = new Date(log.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    acc[day] = (acc[day] || 0) + 1;
    return acc;
  }, {});

  const usageChartData = Object.entries(callCountByDay)
    .map(([date, count]) => ({ date, requests: count }))
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <div>
          <h1 className="admin-page-title">Dashboard</h1>
          <p className="admin-page-subtitle">Live call log metrics from the Django backend.</p>
        </div>
      </div>

      <div className="admin-grid-4">
        <div className="admin-card">
          <div className="admin-stat-row" style={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <div className="admin-kpi-title">Total Calls</div>
              <h3 className="admin-kpi-value">{isLoading ? 'Loading…' : totalCalls}</h3>
              <div className="admin-kpi-change" style={{ color: '#16a34a' }}>
                <TrendingUp size={16} />
                <span>{totalCalls > 0 ? `${totalCalls} calls` : 'No calls yet'}</span>
              </div>
            </div>
            <div className="admin-kpi-icon blue"><Activity size={24} /></div>
          </div>
        </div>

        <div className="admin-card">
          <div className="admin-stat-row" style={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <div className="admin-kpi-title">Total Duration</div>
              <h3 className="admin-kpi-value">{isLoading ? 'Loading…' : formatDuration(totalDuration)}</h3>
              <div className="admin-kpi-change" style={{ color: '#22c55e' }}>
                <span>{totalDuration > 0 ? `${totalDuration} sec` : '0 sec'}</span>
              </div>
            </div>
            <div className="admin-kpi-icon purple"><Clock size={24} /></div>
          </div>
        </div>

        <div className="admin-card">
          <div className="admin-stat-row" style={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <div className="admin-kpi-title">Average Duration</div>
              <h3 className="admin-kpi-value">{isLoading ? 'Loading…' : formatDuration(averageDuration)}</h3>
              <div className="admin-kpi-change" style={{ color: '#38bdf8' }}>
                <span>{averageDuration > 0 ? `${averageDuration} sec avg` : 'N/A'}</span>
              </div>
            </div>
            <div className="admin-kpi-icon cyan"><TrendingUp size={24} /></div>
          </div>
        </div>

        <div className="admin-card">
          <div className="admin-stat-row" style={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <div className="admin-kpi-title">Backend Status</div>
              <h3 className="admin-kpi-value">Django</h3>
              <div className="admin-kpi-change" style={{ color: '#84cc16' }}>
                <span>{dashboardError ? 'Error' : 'Connected'}</span>
              </div>
            </div>
            <div className="admin-kpi-icon green"><Database size={24} /></div>
          </div>
        </div>
      </div>

      {dashboardError && (
        <div className="admin-card" style={{ marginTop: 20, borderColor: '#fca5a5', background: 'rgba(254, 202, 202, 0.12)' }}>
          <p style={{ color: '#b91c1c', margin: 0 }}>{dashboardError}</p>
        </div>
      )}

      <div className="admin-grid-3" style={{ marginTop: 20 }}>
        <div className="admin-card" style={{ gridColumn: 'span 2' }}>
          <h2 className="admin-section-title">Calls per Day</h2>
          <div className="admin-chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={usageChartData.length ? usageChartData : [{ date: 'No data', requests: 0 }] }>
                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} />
                <XAxis dataKey="date" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Line type="monotone" dataKey="requests" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="admin-card">
          <h2 className="admin-section-title">Call Status Distribution</h2>
          <div className="admin-chart">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statusChartData.length ? statusChartData : [{ name: 'No data', value: 1, color: '#64748b' }]} cx="50%" cy="50%" labelLine={false} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name}: ${Math.round((percent || 0) * 100)}%`}>
                  {(statusChartData.length ? statusChartData : [{ name: 'No data', value: 1, color: '#64748b' }]).map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: 20 }}>
        <div className="admin-row-between" style={{ marginBottom: 18 }}>
          <h2 className="admin-section-title" style={{ margin: 0 }}>Recent Calls</h2>
        </div>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Caller</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Direction</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: '#9ca3af', padding: '20px' }}>Loading call logs...</td></tr>
              ) : callLogs.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: '#9ca3af', padding: '20px' }}>No call logs available yet.</td></tr>
              ) : (
                callLogs.slice(0, 8).map((log) => (
                  <tr key={log.call_sid || `${log.timestamp}-${log.from_number}`}>
                    <td>{log.from_number || 'Unknown'}</td>
                    <td>{log.call_status || 'Unknown'}</td>
                    <td>{formatDuration(log.duration)}</td>
                    <td>{log.direction || 'N/A'}</td>
                    <td>{new Date(log.timestamp).toLocaleString()}</td>
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

function UsersPage() {
  const [users, setUsers] = useState(adminInitialUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [selectedId, setSelectedId] = useState(null);

  const filteredUsers = useMemo(() => {
    return users.filter((user) => {
      const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesRole = roleFilter === 'All' || user.role === roleFilter;
      const matchesStatus = statusFilter === 'All' || user.status === statusFilter;
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, searchTerm, roleFilter, statusFilter]);

  const toggleStatus = (id) => {
    setUsers((current) => current.map((user) => (user.id === id ? { ...user, status: user.status === 'Active' ? 'Blocked' : 'Active' } : user)));
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header admin-row-between">
        <div>
          <h1 className="admin-page-title">User Management</h1>
          <p className="admin-page-subtitle">Manage and monitor all platform users.</p>
        </div>
        <button className="admin-btn primary" type="button"><UserPlus size={18} style={{ verticalAlign: 'text-bottom' }} /> Add New User</button>
      </div>

      <div className="admin-panel">
        <div className="admin-filters-grid">
          <div style={{ position: 'relative', gridColumn: 'span 2' }}>
            <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
            <input className="admin-input with-icon" style={{ paddingLeft: 42 }} placeholder="Search by email..." value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} />
          </div>
          <div>
            <select className="admin-select" value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
              <option value="All">All Roles</option>
              <option value="Student">Student</option>
              <option value="Admin">Admin</option>
            </select>
          </div>
          <div>
            <select className="admin-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="All">All Status</option>
              <option value="Active">Active</option>
              <option value="Blocked">Blocked</option>
            </select>
          </div>
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: 20 }}>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>User ID</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td>#{user.id}</td>
                  <td>
                    <div className="admin-media-row">
                      <div className="admin-avatar-sm">{user.email.charAt(0).toUpperCase()}</div>
                      <span>{user.email}</span>
                    </div>
                  </td>
                  <td><span className={`admin-badge ${user.role === 'Admin' ? 'purple' : 'blue'}`}>{user.role}</span></td>
                  <td><span className={`admin-badge ${user.status === 'Active' ? 'success' : 'error'}`}>{user.status}</span></td>
                  <td style={{ color: '#6b7280' }}>{user.lastLogin}</td>
                  <td>
                    <div className="admin-inline-actions">
                      <button className="admin-navbar-action" type="button"><Edit size={16} /></button>
                      <button className="admin-navbar-action" type="button" onClick={() => toggleStatus(user.id)}>{user.status === 'Active' ? <Ban size={16} /> : <CheckCircle size={16} />}</button>
                      <button className="admin-navbar-action" type="button" onClick={() => setSelectedId(user.id)}><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="admin-row-between" style={{ marginTop: 18 }}>
          <div style={{ color: '#6b7280' }}>Showing {filteredUsers.length} of {users.length} users</div>
          <div className="admin-chip-row">
            <button className="admin-btn ghost" type="button">Previous</button>
            <button className="admin-btn ghost" type="button">Next</button>
          </div>
        </div>
      </div>

      {selectedId && (
        <div className="admin-modal-backdrop">
          <div className="admin-modal" style={{ width: 420, padding: 24 }}>
            <h3 className="admin-section-title" style={{ marginTop: 0 }}>Delete user?</h3>
            <p className="admin-muted">This is a visual placeholder in the migrated admin shell.</p>
            <div className="admin-inline-actions" style={{ justifyContent: 'flex-end', marginTop: 20 }}>
              <button className="admin-btn ghost" type="button" onClick={() => setSelectedId(null)}>Cancel</button>
              <button className="admin-btn danger" type="button" onClick={() => setSelectedId(null)}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ContentPage() {
  const [items, setItems] = useState(adminInitialContent);
  const [category, setCategory] = useState('All Content');
  const [showEditor, setShowEditor] = useState(false);
  const categories = ['All Content', 'Mathematics', 'Programming', 'Science', 'Languages', 'AI Prompts'];
  const filtered = category === 'All Content' ? items : items.filter((item) => item.category === category);

  const typeIcon = (type) => (type === 'Lesson' ? <BookOpen size={16} /> : type === 'Prompt' ? <FileText size={16} /> : <Code size={16} />);

  return (
    <div className="admin-page">
      <div className="admin-page-header admin-row-between">
        <div>
          <h1 className="admin-page-title">Content Management</h1>
          <p className="admin-page-subtitle">Manage learning materials, prompts, and course content.</p>
        </div>
        <button className="admin-btn primary" type="button" onClick={() => setShowEditor(true)}><Plus size={18} /> Add New Content</button>
      </div>

      <div className="admin-grid-3" style={{ alignItems: 'start' }}>
        <div className="admin-panel">
          <h2 className="admin-section-title">Categories</h2>
          <div className="admin-stack">
            {categories.map((item) => (
              <button key={item} className={`admin-btn ${category === item ? 'primary' : 'ghost'}`} type="button" onClick={() => setCategory(item)}>{item}</button>
            ))}
          </div>
        </div>

        <div className="admin-grid-2" style={{ gridColumn: 'span 2' }}>
          {filtered.map((item) => (
            <div key={item.id} className="admin-card">
              <div className="admin-card-head" style={{ justifyContent: 'flex-start', gap: 14, marginBottom: 18 }}>
                <div className="admin-type-icon">{typeIcon(item.type)}</div>
                <div>
                  <h3 style={{ margin: 0 }}>{item.title}</h3>
                  <div className="admin-muted" style={{ fontSize: 12 }}>{item.category}</div>
                </div>
              </div>
              <div className="admin-badge-row" style={{ marginBottom: 18 }}>
                <span className={`admin-badge ${item.type === 'Lesson' ? 'blue' : item.type === 'Prompt' ? 'purple' : 'cyan'}`}>{item.type}</span>
                <span className={`admin-badge ${item.status === 'Published' ? 'success' : 'warning'}`}>{item.status}</span>
              </div>
              <div className="admin-row-between" style={{ alignItems: 'center' }}>
                <span className="admin-muted">Updated: {item.lastUpdated}</span>
                <div className="admin-inline-actions">
                  <button className="admin-navbar-action" type="button"><Edit size={16} /></button>
                  <button className="admin-navbar-action" type="button" onClick={() => setItems((current) => current.filter((entry) => entry.id !== item.id))}><Trash2 size={16} /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {showEditor && (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <div className="admin-modal-head" style={{ padding: 24, borderBottom: '1px solid #e5e7eb' }}>
              <h3 className="admin-section-title" style={{ margin: 0 }}>Create New Content</h3>
              <button className="admin-navbar-action" type="button" onClick={() => setShowEditor(false)}><X size={16} /></button>
            </div>
            <div style={{ padding: 24 }}>
              <div className="admin-card" style={{ marginBottom: 18 }}>
                <div className="admin-row-between" style={{ justifyContent: 'flex-start', gap: 10, marginBottom: 12 }}>
                  <button className="admin-navbar-action" type="button"><Bold size={14} /></button>
                  <button className="admin-navbar-action" type="button"><Italic size={14} /></button>
                  <button className="admin-navbar-action" type="button"><List size={14} /></button>
                </div>
                <textarea className="admin-textarea" rows={6} defaultValue="# Sample content\n\nEdit your content here..." />
              </div>
              <div className="admin-inline-actions" style={{ justifyContent: 'flex-end' }}>
                <button className="admin-btn ghost" type="button" onClick={() => setShowEditor(false)}>Cancel</button>
                <button className="admin-btn primary" type="button" onClick={() => setShowEditor(false)}>Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TrainingPage() {
  const [isTraining, setIsTraining] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([
    { id: '1', timestamp: '2025-12-09 10:30:00', message: 'Model training initialized', type: 'info' },
    { id: '2', timestamp: '2025-12-09 10:30:15', message: 'Loading training dataset...', type: 'info' },
    { id: '3', timestamp: '2025-12-09 10:35:42', message: 'Training completed successfully', type: 'success' },
    { id: '4', timestamp: '2025-12-09 10:36:00', message: 'Model validated and saved', type: 'success' },
  ]);

  useEffect(() => {
    if (!isTraining) return undefined;
    const timer = window.setInterval(() => {
      setProgress((current) => {
        if (current >= 100) {
          window.clearInterval(timer);
          setIsTraining(false);
          setLogs((currentLogs) => [
            { id: Date.now().toString(), timestamp: new Date().toLocaleString(), message: 'Training completed successfully', type: 'success' },
            ...currentLogs,
          ]);
          return 100;
        }
        return current + 10;
      });
    }, 500);
    return () => window.clearInterval(timer);
  }, [isTraining]);

  const stats = [
    { title: 'Training Data Count', value: '125,847', icon: Database, color: 'blue' },
    { title: 'Last Model Trained', value: '2 hours ago', icon: Clock, color: 'purple' },
    { title: 'Training Status', value: isTraining ? 'In Progress' : 'Ready', icon: isTraining ? AlertCircle : CheckCircle, color: isTraining ? 'cyan' : 'green' },
  ];

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h1 className="admin-page-title">Model Training</h1>
        <p className="admin-page-subtitle">Train and manage AI models with your datasets.</p>
      </div>

      <div className="admin-grid-3">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div className="admin-card" key={stat.title}>
              <div className="admin-stat-top">
                <div>
                  <div className="admin-kpi-title">{stat.title}</div>
                  <h3 className="admin-kpi-value" style={{ fontSize: 24 }}>{stat.value}</h3>
                </div>
                <div className={`admin-kpi-icon ${stat.color}`}><Icon size={24} /></div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="admin-card" style={{ marginTop: 20 }}>
        <h2 className="admin-section-title">Training Control</h2>
        <div className="admin-panel" style={{ marginBottom: 18 }}>
          <Upload size={34} style={{ display: 'block', margin: '0 auto 12px', color: '#9ca3af' }} />
          <div style={{ textAlign: 'center', color: '#6b7280' }}>Drop your dataset files here, or click to browse</div>
          <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: 13, marginTop: 8 }}>Supports CSV, JSON, and TXT files (Max 500MB)</div>
        </div>
        <button className="admin-btn primary" type="button" onClick={() => setIsTraining(true)} disabled={isTraining} style={{ width: '100%' }}>
          <Play size={18} /> {isTraining ? 'Training in Progress...' : 'Start Training'}
        </button>
        {(isTraining || progress > 0) && (
          <div style={{ marginTop: 18 }}>
            <div className="admin-row-between" style={{ marginBottom: 10 }}><span>Training Progress</span><strong>{progress}%</strong></div>
            <div className="admin-progress-bar"><div className="admin-progress-fill" style={{ width: `${progress}%` }} /></div>
          </div>
        )}
      </div>

      <div className="admin-card" style={{ marginTop: 20 }}>
        <div className="admin-row-between" style={{ marginBottom: 18 }}>
          <h2 className="admin-section-title" style={{ margin: 0 }}>Training Logs</h2>
          <button className="admin-btn ghost" type="button">Clear Logs</button>
        </div>
        <div className="admin-stack">
          {logs.map((log) => (
            <div key={log.id} className={`admin-log ${log.type}`}>
              {log.type === 'success' ? <CheckCircle size={18} color="#16a34a" /> : log.type === 'error' ? <AlertCircle size={18} color="#dc2626" /> : <Info size={18} color="#2563eb" />}
              <div>
                <div className="admin-muted" style={{ fontSize: 12 }}>{log.timestamp}</div>
                <div>{log.message}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AnalyticsPage() {
  const logs = systemLogs;
  const [category, setCategory] = useState('All');
  const [level, setLevel] = useState('All');
  const [dateFilter, setDateFilter] = useState('today');

  const filteredLogs = useMemo(() => logs.filter((log) => (category === 'All' || log.category === category) && (level === 'All' || log.level === level)), [logs, category, level]);

  const levelIcon = (logLevel) => {
    if (logLevel === 'success') return <CheckCircle size={18} />;
    if (logLevel === 'warning') return <AlertTriangle size={18} />;
    if (logLevel === 'error') return <AlertTriangle size={18} />;
    return <Info size={18} />;
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header admin-row-between">
        <div>
          <h1 className="admin-page-title">Logs & Analytics</h1>
          <p className="admin-page-subtitle">Monitor system activities and analyze usage patterns.</p>
        </div>
        <button className="admin-btn primary" type="button"><Download size={18} /> Export Logs</button>
      </div>

      <div className="admin-grid-4">
        <div className="admin-card"><div className="admin-kpi-title">System Status</div><div className="admin-kpi-value" style={{ fontSize: 24, color: '#16a34a' }}>Healthy</div></div>
        <div className="admin-card"><div className="admin-kpi-title">Uptime</div><div className="admin-kpi-value" style={{ fontSize: 24 }}>99.8%</div></div>
        <div className="admin-card"><div className="admin-kpi-title">Warnings</div><div className="admin-kpi-value" style={{ fontSize: 24 }}>12</div></div>
        <div className="admin-card"><div className="admin-kpi-title">Errors</div><div className="admin-kpi-value" style={{ fontSize: 24 }}>3</div></div>
      </div>

      <div className="admin-grid-2" style={{ marginTop: 20 }}>
        <div className="admin-card">
          <h2 className="admin-section-title">Peak Usage Hours</h2>
          <div className="admin-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={peakUsageData}><CartesianGrid strokeDasharray="3 3" opacity={0.15} /><XAxis dataKey="hour" /><YAxis /><Tooltip /><Line type="monotone" dataKey="requests" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} /></LineChart></ResponsiveContainer></div>
        </div>
        <div className="admin-card">
          <h2 className="admin-section-title">Most Common Queries</h2>
          <div className="admin-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={queryTypeData}><CartesianGrid strokeDasharray="3 3" opacity={0.15} /><XAxis dataKey="type" /><YAxis /><Tooltip /><Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]} /></BarChart></ResponsiveContainer></div>
        </div>
      </div>

      <div className="admin-panel" style={{ marginTop: 20 }}>
        <div className="admin-filters-grid">
          <div>
            <label className="admin-field"><span style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>Date Range</span></label>
            <select className="admin-select" value={dateFilter} onChange={(event) => setDateFilter(event.target.value)}>
              <option value="today">Today</option>
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
          <div>
            <label className="admin-field"><span style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>Category</span></label>
            <select className="admin-select" value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="All">All Categories</option>
              <option value="API">API</option>
              <option value="Auth">Authentication</option>
              <option value="Training">Training</option>
              <option value="System">System</option>
            </select>
          </div>
          <div>
            <label className="admin-field"><span style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>Log Level</span></label>
            <select className="admin-select" value={level} onChange={(event) => setLevel(event.target.value)}>
              <option value="All">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="success">Success</option>
            </select>
          </div>
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: 20 }}>
        <div className="admin-row-between" style={{ marginBottom: 18 }}>
          <h2 className="admin-section-title" style={{ margin: 0 }}>System Logs</h2>
          <div className="admin-chip-row"><Filter size={16} /> <span className="admin-muted">{filteredLogs.length} records</span></div>
        </div>
        <div className="admin-stack">
          {filteredLogs.map((log) => (
            <div key={log.id} className={`admin-log ${log.level}`}>
              {levelIcon(log.level)}
              <div style={{ flex: 1 }}>
                <div className="admin-muted" style={{ fontSize: 12 }}>{log.timestamp} · {log.user}</div>
                <div>{log.message}</div>
              </div>
              <span className={`admin-badge ${log.level}`}>{log.category}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');
  const tabs = [
    { id: 'general', label: 'General', icon: Globe },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'api', label: 'API Keys', icon: Key },
  ];

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h1 className="admin-page-title">Settings</h1>
        <p className="admin-page-subtitle">Manage your account and system preferences.</p>
      </div>

      <div className="admin-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="admin-tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button key={tab.id} type="button" className={`admin-tab-button ${activeTab === tab.id ? 'active' : ''}`} onClick={() => setActiveTab(tab.id)}>
                <Icon size={16} style={{ verticalAlign: 'text-bottom', marginRight: 8 }} />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div style={{ padding: 24 }}>
          {activeTab === 'general' && (
            <div className="admin-stack">
              <div>
                <h3>General Settings</h3>
                <div className="admin-stack">
                  <input className="admin-input" defaultValue="GenCal AI" />
                  <input className="admin-input" defaultValue="support@gencal.ai" />
                  <select className="admin-select"><option>UTC (GMT+0:00)</option><option>EST (GMT-5:00)</option><option>PST (GMT-8:00)</option><option>JST (GMT+9:00)</option></select>
                  <div className="admin-row-between"><div><strong>Maintenance Mode</strong><div className="admin-muted">Temporarily disable user access</div></div><input type="checkbox" /></div>
                </div>
              </div>
              <button className="admin-btn primary" type="button"><Save size={16} /> Save Changes</button>
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="admin-stack">
              <h3>Admin Profile</h3>
              <div className="admin-media-row">
                <div className="admin-avatar" style={{ width: 80, height: 80, fontSize: 30 }}>A</div>
                <button className="admin-btn ghost" type="button">Change Avatar</button>
              </div>
              <div className="admin-grid-2">
                <input className="admin-input" defaultValue="Admin" />
                <input className="admin-input" defaultValue="User" />
              </div>
              <input className="admin-input" defaultValue="admin@gencal.ai" />
              <textarea className="admin-textarea" rows={4} defaultValue="System administrator for GenCal AI platform." />
              <button className="admin-btn primary" type="button"><Save size={16} /> Update Profile</button>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="admin-stack">
              <h3>Security Settings</h3>
              <input className="admin-input" type="password" placeholder="Current Password" />
              <input className="admin-input" type="password" placeholder="New Password" />
              <input className="admin-input" type="password" placeholder="Confirm New Password" />
              <button className="admin-btn primary" type="button">Update Password</button>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="admin-stack">
              <h3>Notifications</h3>
              <div className="admin-row-between"><span>Email Alerts</span><input type="checkbox" defaultChecked /></div>
              <div className="admin-row-between"><span>Security Alerts</span><input type="checkbox" defaultChecked /></div>
              <div className="admin-row-between"><span>Weekly Digest</span><input type="checkbox" defaultChecked /></div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="admin-stack">
              <h3>API Keys</h3>
              <div className="admin-card" style={{ padding: 16 }}>
                <div className="admin-row-between"><strong>Production Key</strong><span className="admin-muted">2025-12-01</span></div>
                <div className="admin-muted">sk_prod_••••••••••••••••</div>
              </div>
              <div className="admin-card" style={{ padding: 16 }}>
                <div className="admin-row-between"><strong>Development Key</strong><span className="admin-muted">2025-12-05</span></div>
                <div className="admin-muted">sk_dev_••••••••••••••••</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DashboardShell({ pathname, onNavigate, theme, toggleTheme }) {
  const route = pathToPage(pathname);

  return (
    <div className="admin-root admin-shell">
      <AdminSidebar pathname={pathname} onNavigate={onNavigate} />
      <AdminNavbar theme={theme} toggleTheme={toggleTheme} onNavigate={onNavigate} />
      <div className="admin-content">
        {route === 'dashboard' && <DashboardPage />}
        {route === 'users' && <UsersPage />}
        {route === 'content' && <ContentPage />}
        {route === 'training' && <TrainingPage />}
        {route === 'analytics' && <AnalyticsPage />}
        {route === 'settings' && <SettingsPage />}
      </div>
    </div>
  );
}

export default function AdminApp({ pathname = '/admin', onNavigate = () => {} }) {
  const themeApi = useAdminTheme();
  const route = pathToPage(pathname);

  if (route === 'login') {
    return <AdminLoginPage theme={themeApi.theme} toggleTheme={themeApi.toggleTheme} onNavigate={onNavigate} />;
  }

  return <DashboardShell pathname={pathname} onNavigate={onNavigate} theme={themeApi.theme} toggleTheme={themeApi.toggleTheme} />;
}
