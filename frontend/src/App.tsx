import { useState, useEffect } from 'react';
import type { DashboardData } from './types';
import { dashboardApi, simulationApi } from './api';
import MooringLineCard from './components/MooringLineCard';
import WeatherDisplay from './components/WeatherDisplay';
import TensionChart from './components/TensionChart';
import './App.css';

function App() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [selectedLineId, setSelectedLineId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataGenerated, setDataGenerated] = useState(false);

  useEffect(() => {
    loadDashboardData();
    // Set up periodic refresh
    const interval = setInterval(loadDashboardData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

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
              <div className="text-sm">
                <span className="bg-green-500 px-2 py-1 rounded">
                  {dashboardData.system_status.system_health}
                </span>
                <span className="ml-3">
                  활성: {dashboardData.system_status.active_lines}/{dashboardData.system_status.total_lines}
                </span>
              </div>
            )}
            {!dataGenerated && dashboardData?.mooring_lines.length === 0 && (
              <button
                onClick={generateSampleData}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                샘플 데이터 생성
              </button>
            )}
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

            {/* Mooring Lines Grid */}
            <div>
              <h2 className="text-xl font-bold mb-3">계류줄 상태</h2>
              {dashboardData.mooring_lines.length === 0 ? (
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                  <p className="text-gray-600 mb-4">계류줄 데이터가 없습니다.</p>
                  {!dataGenerated && (
                    <button
                      onClick={generateSampleData}
                      className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                    >
                      샘플 데이터 생성하기
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {dashboardData.mooring_lines.map((line) => (
                    <MooringLineCard
                      key={line.id}
                      line={line}
                      onClick={setSelectedLineId}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* System Status */}
            <div className="mt-6 bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-3">시스템 상태</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-gray-600">활성 계류줄</p>
                  <p className="text-2xl font-bold text-green-600">
                    {dashboardData.system_status.active_lines}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">전체 계류줄</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {dashboardData.system_status.total_lines}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">위험 경고</p>
                  <p className="text-2xl font-bold text-red-600">
                    {dashboardData.system_status.critical_alerts}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">주의 경고</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {dashboardData.system_status.warning_alerts}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Tension Chart Modal */}
      {selectedLineId && (
        <TensionChart
          lineId={selectedLineId}
          onClose={() => setSelectedLineId(null)}
        />
      )}
    </div>
  );
}

export default App;