/**
 * J.A.R.V.I.S. DATA CONFIGURATION
 * ================================
 * External data source for dashboard
 * Import via <script src="jarvis_data.js"></script>
 */

window.JARVIS_DATA = {
    systemName: 'J.A.R.V.I.S.',
    version: '4.2.1',
    
    status: {
        network: true,
        database: true,
        ai_module: true,
        comms: true,
    },
    
    activities: [
        { time: '23:45', message: 'System diagnostics completed successfully' },
        { time: '23:42', message: 'All neural pathways online and stable' },
        { time: '23:40', message: 'Security protocols: GREEN' },
        { time: '23:38', message: 'Network latency optimal: 8ms' },
        { time: '23:35', message: 'Database replication synchronized' },
        { time: '23:30', message: 'Deep learning models loaded and cached' },
    ],
    
    metrics: [
        { label: 'CPU Usage', value: 28, unit: '%' },
        { label: 'Memory Load', value: 52, unit: '%' },
        { label: 'Network Speed', value: 94, unit: 'Mbps' },
        { label: 'Response Time', value: 8, unit: 'ms' },
        { label: 'AI Processing', value: 76, unit: '%' },
        { label: 'Cache Hit Rate', value: 87, unit: '%' },
    ],
    
    priorities: [
        '🔴 Critical: Review threat assessment reports',
        '🟡 Important: Verify security clearances',
        '🟢 Standard: Process daily system logs',
        '🔵 Scheduled: Run weekly optimization tasks',
    ],
    
    ticker: '█ System Online █ All Networks Active █ Neural Network: Ready █ Security: GREEN █ Latest Update: 23:45 UTC'
};
