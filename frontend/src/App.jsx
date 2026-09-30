import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ShieldAlert, Activity, Globe, Shield, Search, Database } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const MOCK_STATS = {
  total_domains: 5,
  analyzed_domains: 1,
  high_risk_domains: 0,
  classification: {
    legitimate: 1,
    suspicious: 1,
    pending: 3
  }
}

const chartData = [
  { name: 'Mon', domains: 4, blocked: 0 },
  { name: 'Tue', domains: 7, blocked: 1 },
  { name: 'Wed', domains: 5, blocked: 0 },
  { name: 'Thu', domains: 12, blocked: 3 },
  { name: 'Fri', domains: 18, blocked: 5 },
  { name: 'Sat', domains: 14, blocked: 2 },
  { name: 'Sun', domains: 5, blocked: 0 },
]

function StatCard({ title, value, icon: Icon, bgClass, textClass, delay }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="bg-card border border-border p-6 rounded-2xl shadow-lg flex items-center space-x-4 hover:border-primary/50 transition-colors"
    >
      <div className={`p-4 rounded-xl ${bgClass}`}>
        <Icon className={`w-8 h-8 ${textClass}`} />
      </div>
      <div>
        <p className="text-gray-400 text-sm font-medium uppercase tracking-wider">{title}</p>
        <h3 className="text-3xl font-bold text-white mt-1">{value}</h3>
      </div>
    </motion.div>
  )
}

function App() {
  const [stats, setStats] = useState(MOCK_STATS)

  return (
    <div className="min-h-screen bg-background text-white p-8 font-sans">
      {/* Header */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-12"
      >
        <div className="flex items-center space-x-3">
          <div className="bg-primary/20 p-3 rounded-lg border border-primary/30 shadow-[0_0_15px_rgba(37,99,235,0.5)]">
            <ShieldAlert className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              AGY Threat Intelligence
            </h1>
            <p className="text-sm text-gray-400">Cybersecurity Research Platform</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" />
            <input 
              type="text" 
              placeholder="Search domain or IP..." 
              className="bg-card border border-border rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-primary/50 transition-colors w-64 text-white"
            />
          </div>
          <button className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-medium transition-colors shadow-[0_0_15px_rgba(37,99,235,0.4)]">
            Analyze New Domain
          </button>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto space-y-8">
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard 
            title="Total Domains" 
            value={stats.total_domains} 
            icon={Globe} 
            bgClass="bg-blue-500/20"
            textClass="text-blue-400"
            delay={0.1} 
          />
          <StatCard 
            title="Analyzed" 
            value={stats.analyzed_domains} 
            icon={Activity} 
            bgClass="bg-purple-500/20"
            textClass="text-purple-400" 
            delay={0.2} 
          />
          <StatCard 
            title="Suspicious / Risk" 
            value={stats.classification.suspicious} 
            icon={ShieldAlert} 
            bgClass="bg-yellow-500/20"
            textClass="text-yellow-400" 
            delay={0.3} 
          />
          <StatCard 
            title="High Risk (Blocked)" 
            value={stats.high_risk_domains} 
            icon={Shield} 
            bgClass="bg-red-500/20"
            textClass="text-red-400" 
            delay={0.4} 
          />
        </div>

        {/* Charts and Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="lg:col-span-2 bg-card border border-border rounded-2xl p-6 h-96 relative overflow-hidden"
          >
            <h3 className="text-lg font-medium text-gray-300 mb-4">Traffic & Threats Analyzed</h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorDomains" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#4b5563" />
                  <YAxis stroke="#4b5563" />
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }} />
                  <Area type="monotone" dataKey="domains" stroke="#3b82f6" fillOpacity={1} fill="url(#colorDomains)" />
                  <Area type="monotone" dataKey="blocked" stroke="#ef4444" fillOpacity={1} fill="url(#colorBlocked)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 }}
            className="bg-card border border-border rounded-2xl p-6 h-96"
          >
            <h3 className="text-lg font-medium text-gray-300 mb-6">Recent Activity</h3>
            <div className="space-y-4">
              {[
                { domain: 'google.com', status: 'LEGITIMATE', time: '10 mins ago', color: 'text-green-500' },
                { domain: 'suspicious-test.xyz', status: 'SUSPICIOUS', time: '1 hr ago', color: 'text-yellow-500' },
                { domain: 'test1.com', status: 'PENDING', time: '2 hrs ago', color: 'text-gray-500' },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between border-b border-border/50 pb-4 last:border-0">
                  <div>
                    <p className="font-medium">{item.domain}</p>
                    <p className="text-xs text-gray-500">{item.time}</p>
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded bg-background border border-border ${item.color}`}>
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  )
}

export default App
