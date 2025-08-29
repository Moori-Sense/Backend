import { useState, useEffect } from 'react';
import type { DashboardData, MooringLineSummary } from './types';
import { dashboardApi, simulationApi } from './api';
import WeatherDisplay from './components/WeatherDisplay';
import TensionChart from './components/TensionChart';
import ShipTopView from './components/ShipTopView';
import './App.css';

function App() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [selectedLineId, setSelectedLineId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataGenerated, setDataGenerated] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    loadDashboardData();
    connectWebSocket();
    
    // Set up periodic refresh as fallback
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'dashboard_update' || message.type === 'sensor_data_update') {
            loadDashboardData(); // Refresh dashboard when updates received
          }
        } catch (err) {
          console.error('WebSocket message parse error:', err);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
      
    } catch (err) {
      console.error('WebSocket connection failed:', err);
    }
  };

  const loadDashboardData = async () => {
    try {
      const data = await dashboardApi.getDashboard();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const generateSampleData = async () => {
    try {
      setLoading(true);
      await simulationApi.generateSampleData();
      setDataGenerated(true);
      await loadDashboardData();
    } catch (err) {
      console.error('Failed to generate sample data:', err);
      setError('Failed to generate sample data');
    } finally {
      setLoading(false);
    }
  };

  const processTestData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/simulation/process-test-data', { method: 'POST' });
      if (response.ok) {
        const result = await response.json();
        console.log('Test data processed:', result);
        setDataGenerated(true);
        await loadDashboardData();
      } else {
        throw new Error('Failed to process test data');
      }
    } catch (err) {
      console.error('Failed to process test data:', err);
      setError('Failed to process test data');
    } finally {
      setLoading(false);
    }
  };

  // 계류줄을 좌현/우현으로 분류
  const groupMooringLines = (lines: MooringLineSummary[]) => {
    const portLines = lines.filter(line => 
      line.position?.includes('PORT') || line.line_id?.startsWith('L0') || line.line_id?.startsWith('L2') || 
      line.line_id?.startsWith('L4') || line.line_id?.startsWith('L6')
    );
    const starboardLines = lines.filter(line => 
      line.position?.includes('STARBOARD') || line.line_id?.startsWith('L1') || line.line_id?.startsWith('L3') || 
      line.line_id?.startsWith('L5') || line.line_id?.startsWith('L7')
    );
    
    return { portLines, starboardLines };
  };

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadDashboardData}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">선박 계류줄 모니터링 시스템</h1>
            <p className="text-blue-100 text-sm mt-1">실시간 장력 및 수명 관리</p>
          </div>
          <div className="flex items-center gap-4">
            {dashboardData && (
              <div className="text-sm flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    wsConnected ? 'bg-green-400' : 'bg-red-400'
                  }`}></div>
                  <span className="text-sm">
                    {wsConnected ? 'LIVE' : 'OFFLINE'}
                  </span>
                </div>
                <span className="bg-green-500 px-2 py-1 rounded">
                  {dashboardData.system_status.system_health}
                </span>
                <span>
                  활성: {dashboardData.system_status.active_lines}/{dashboardData.system_status.total_lines}
                </span>
              </div>
            )}
            <div className="flex gap-2">
              {!dataGenerated && dashboardData?.mooring_lines.length === 0 && (
                <>
                  <button
                    onClick={generateSampleData}
                    className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                  >
                    샘플 데이터
                  </button>
                  <button
                    onClick={processTestData}
                    className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                  >
                    실제 데이터 처리
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto p-4">
        {dashboardData && (
          <>
            {/* Alerts Section */}
            {dashboardData.active_alerts.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-bold mb-3">활성 경고</h2>
                <div className="space-y-2">
                  {dashboardData.active_alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`p-3 rounded-lg border-l-4 ${
                        alert.severity === 'CRITICAL'
                          ? 'bg-red-50 border-red-500'
                          : alert.severity === 'HIGH'
                          ? 'bg-orange-50 border-orange-500'
                          : 'bg-yellow-50 border-yellow-500'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className={`text-sm font-semibold ${
                            alert.severity === 'CRITICAL' ? 'text-red-600' :
                            alert.severity === 'HIGH' ? 'text-orange-600' : 'text-yellow-600'
                          }`}>
                            [{alert.severity}]
                          </span>
                          <p className="text-gray-700 mt-1">{alert.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(alert.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weather Section */}
            <div className="mb-6">
              <WeatherDisplay weather={dashboardData.current_weather} />
            </div>

            {/* Ship Top View Layout */}
            <div>
              {dashboardData.mooring_lines.length === 0 ? (
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                  <p className="text-gray-600 mb-4">계류줄 데이터가 없습니다.</p>
                  <p className="text-sm text-gray-500 mb-6">
                    실제 센서 데이터를 처리하거나 샘플 데이터를 생성해보세요.
                  </p>
                  {!dataGenerated && (
                    <div className="flex gap-4 justify-center">
                      <button
                        onClick={processTestData}
                        className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                      >
                        📊 실제 센서 데이터 처리
                      </button>
                      <button
                        onClick={generateSampleData}
                        className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600"
                      >
                        🎲 샘플 데이터 생성
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                (() => {
                  const { portLines, starboardLines } = groupMooringLines(dashboardData.mooring_lines);
                  return (
                    <ShipTopView
                      portLines={portLines}
                      starboardLines={starboardLines}
                      onLineClick={setSelectedLineId}
                    />
                  );
                })()
              )}
            </div>

            {/* Real-time Data Info */}
            {dashboardData.mooring_lines.length > 0 && (
              <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 border border-blue-200">
                <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-2 ${
                    wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  }`}></div>
                  실시간 모니터링 상태
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600 text-sm">연결 상태</p>
                    <p className={`text-lg font-bold ${
                      wsConnected ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {wsConnected ? 'LIVE' : 'OFFLINE'}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600 text-sm">활성 계류줄</p>
                    <p className="text-lg font-bold text-green-600">
                      {dashboardData.system_status.active_lines}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600 text-sm">전체 계류줄</p>
                    <p className="text-lg font-bold text-blue-600">
                      {dashboardData.system_status.total_lines}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600 text-sm">위험 경고</p>
                    <p className="text-lg font-bold text-red-600">
                      {dashboardData.system_status.critical_alerts}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600 text-sm">주의 경고</p>
                    <p className="text-lg font-bold text-yellow-600">
                      {dashboardData.system_status.warning_alerts}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Tension Chart Modal */}
      {selectedLineId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <TensionChart
              lineId={selectedLineId}
              onClose={() => setSelectedLineId(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;