# Model Monitoring Dashboard

## Overview

A real-time monitoring dashboard for deployed machine learning models displaying key performance metrics and system health indicators.

## Features Implemented

### Core Metrics
1. **Success Rate** - Percentage of successful API calls
   - 7-day trend visualization
   - Min/max range display
   - Status indicator

2. **Total API Calls** - Cumulative count of model invocations
   - 7-day trend
   - Daily average calculation
   - Growth indicator relative to previous period

3. **Error Count** - Number of failed requests
   - 7-day trend
   - Trend direction indicator
   - Min/max range display

4. **Error Rate** - Percentage of errors relative to total calls
   - Health status (Healthy/Caution/Alert)
   - Performance target indicator
   - Visual health bar

5. **Average Response Time** - Model latency in milliseconds
   - 7-day trend with min/max
   - Trend direction

6. **Throughput** - Calls per minute
   - Peak throughput estimate
   - 24h average

### System Health Indicators
- Memory Usage (%)
- CPU Usage (%)
- Uptime (hours)
- Active Sessions

### Visual Design Elements
- **Animated counters** - Numbers animate from 0 to target value (1.2s easing)
- **Sparkline charts** - Micro SVG charts showing 7-day trends
- **Status badges** - Live indicator with pulsing animation
- **Health bars** - Visual progress indicators for percentage-based metrics
- **Trend arrows** - Up/down indicators with color coding (green/red)
- **Color-coded cards** - Different primary colors per metric for quick visual scanning
- **Hover effects** - Cards lift on hover with enhanced shadows
- **Responsive layout** - 3-column grid on desktop, 2 columns on tablet, 1 column on mobile

## File Structure

```
frontend/
├── js/pages/
│   └── monitoring.js          # Monitoring page controller (fake data)
├── css/
│   └── style.css              # Monitoring styles + responsive design
└── index.html                 # Added monitoring nav item + script tag
```

## Design System Integration

The monitoring dashboard integrates with the existing **Industrial Command Center** aesthetic:
- **Fonts**: Bebas Neue (display) + Outfit (body) + JetBrains Mono (data)
- **Colors**: Navy/turquoise base with semantic status colors
- **Spacing**: Consistent padding and gap system
- **Shadows**: Layered shadow system for depth

## Mock Data Structure

Currently using fake data generator `generateSampleMetrics()` that produces:
```javascript
{
  successRate: number,
  successRateHistory: [number],      // 7 days
  successRateTrend: number,           // % change

  totalCalls: number,
  callsHistory: [number],             // 7 days
  callsGrowth: number,                // % change

  totalErrors: number,
  errorsHistory: [number],            // 7 days
  errorsTrend: number,                // % change

  errorRate: number,                  // percentage

  avgLatency: number,                 // ms
  latencyHistory: [number],           // 7 days
  latencyTrend: number,               // ms change

  throughput: number,                 // calls/min
  throughputTrend: number,            // % change

  systemHealth: {
    memory: number,                   // %
    cpu: number,                      // %
    uptime: number,                   // hours
    activeSessions: number
  }
}
```

## Backend Integration (TODO)

To connect real data, modify `MonitoringPage`:

1. **Replace model loading** - Update `loadDeployedModels()` to call actual API:
   ```javascript
   const models = await API.models.listDeployed();
   ```

2. **Replace metrics loading** - Update `loadMonitoringData()` to fetch real metrics:
   ```javascript
   const metrics = await API.models.getMetrics(modelId, {
     timeWindow: '7days',
     granularity: 'daily'
   });
   ```

3. **Expected API endpoints**:
   - `GET /api/models/deployed` - List deployed models
   - `GET /api/models/{id}/metrics?days=7` - Get metrics for model
   - `GET /api/models/{id}/system-health` - Get system health

4. **Metric fields expected from backend**:
   - `success_rate: float` (0-100)
   - `total_calls: int`
   - `error_count: int`
   - `avg_latency_ms: int`
   - `throughput_per_minute: float`
   - `7d_trends: dict` - Historical data for sparklines
   - `system_health: dict` - Memory, CPU, uptime, sessions

## Styling Reference

Key CSS classes for customization:

- `.monitoring-grid` - Main metrics container
- `.metric-card` - Individual metric card
- `.metric-card-primary` - Success rate card (green accent)
- `.metric-card-secondary` - Calls card (orange accent)
- `.metric-card-danger` - Error count card (red accent)
- `.metric-card-warning` - Error rate card (orange accent)
- `.metric-card-tertiary` - Latency card (cyan accent)
- `.metric-card-info` - Throughput card (violet accent)
- `.monitoring-system-health` - System health section
- `.health-items-grid` - System health metrics grid

## Animation Effects

- **Pulse animation**: Status badge live indicator (2s loop)
- **Number counter**: Ease-out-cubic from 0 to value (1.2s)
- **Card hover**: Translate Y with shadow enhancement
- **Trend animation**: Smooth width expansion for bars

## Responsive Breakpoints

- **Desktop** (1200px+): 3-column metric grid
- **Tablet** (900px): 2-column metric grid
- **Mobile** (600px): 1-column metric grid + 2-column system health grid

## Future Enhancements

1. **Real-time metric updates** - WebSocket connection for live data
2. **Custom time windows** - Select 1d, 7d, 30d, 90d
3. **Metric alerts** - Alert when error rate exceeds threshold
4. **Export/download** - CSV/JSON export of metrics
5. **Comparison mode** - Compare metrics across multiple models
6. **Historical drilling** - Click on date to view detailed metrics
7. **Custom dashboards** - Rearrange/pin important metrics
8. **Dark mode** - Uses existing dark theme system
