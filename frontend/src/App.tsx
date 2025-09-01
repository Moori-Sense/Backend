import { useState, useEffect } from 'react';
import type { DashboardData } from './types';
import { dashboardApi, simulationApi } from './api';
import MooringLineCard from './components/MooringLineCard';
import WeatherDisplay from './components/WeatherDisplay';
import TensionChart from './components/TensionChart';
import ShipTopView from './components/ShipTopView';
import CriticalAlertModal from './components/CriticalAlertModal';
import './App.css';

function App() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [selectedLineId, setSelectedLineId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataGenerated, setDataGenerated] = useState(false);
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [simulationLoading, setSimulationLoading] = useState(false);
  
  // Critical Alert Modal 상태
  const [showCriticalAlert, setShowCriticalAlert] = useState(false);
  const [criticalLines, setCriticalLines] = useState<any[]>([]);

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
      
      // 자동 위험 감지 제거됨 - 키보드 입력으로만 알림 트리거
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

  const startSimulation = async () => {
    try {
      setSimulationLoading(true);
      await simulationApi.startSimulation();
      setSimulationRunning(true);
      setError(null);
    } catch (err) {
      console.error('Failed to start simulation:', err);
      setError('시뮬레이션 시작 실패');
    } finally {
      setSimulationLoading(false);
    }
  };

  const stopSimulation = async () => {
    try {
      setSimulationLoading(true);
      await simulationApi.stopSimulation();
      setSimulationRunning(false);
      setError(null);
    } catch (err) {
      console.error('Failed to stop simulation:', err);
      setError('시뮬레이션 중지 실패');
    } finally {
      setSimulationLoading(false);
    }
  };

  const checkSimulationStatus = async () => {
    try {
      const status = await simulationApi.getSimulationStatus();
      setSimulationRunning(status.simulation.is_running);
    } catch (err) {
      console.error('Failed to check simulation status:', err);
    }
  };

  // 위험 알림 모달 닫기
  const handleCloseCriticalAlert = () => {
    setShowCriticalAlert(false);
  };

  // 키보드 입력으로 알림창 수동 트리거
  const triggerManualAlert = () => {
    // 수동으로 위험 상태 계류줄 시뮬레이션
    if (dashboardData?.mooring_lines) {
      // L2, L6 라인을 위험 상태로 시뮬레이션
      const simulatedCriticalLines = dashboardData.mooring_lines
        .filter(line => ['L2', 'L6'].includes(line.line_id))
        .map(line => ({
          ...line,
          status: 'CRITICAL' as const,
          current_tension: line.max_tension ? line.max_tension * 0.95 : line.reference_tension * 1.9, // 최대 장력의 95%
          tension_percentage: line.max_tension ? (line.max_tension * 0.95 / line.reference_tension * 100) : 190
        }));
      
      if (simulatedCriticalLines.length > 0) {
        setCriticalLines(simulatedCriticalLines);
        setShowCriticalAlert(true);
        
        // 알림 트리거 확인 메시지 (개발자 도구에서 확인용)
        console.log('🚨 Critical Alert Triggered by Keyboard Input:', simulatedCriticalLines.map(line => line.name));
      }
    }
  };



  // 시뮬레이션 상태 주기적 확인
  useEffect(() => {
    checkSimulationStatus();
    const interval = setInterval(checkSimulationStatus, 5000); // 5초마다 확인
    return () => clearInterval(interval);
  }, []);

  // 키보드 이벤트 리스너 설정
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      // 입력 필드에서는 키보드 단축키 비활성화
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return;
      }

      // F9 키: 알림창 트리거 (주요 단축키)
      if (event.key === 'F9') {
        event.preventDefault();
        triggerManualAlert();
        console.log('🚨 F9 키로 위험 알림 트리거됨');
      }
      // 스페이스바: 알림창 트리거 (body 포커스시에만)
      else if (event.code === 'Space' && document.activeElement === document.body) {
        event.preventDefault();
        triggerManualAlert();
        console.log('🚨 스페이스바로 위험 알림 트리거됨');
      }
      // Ctrl + Shift + A: 알림창 트리거 (고급 단축키)
      else if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'a') {
        event.preventDefault();
        triggerManualAlert();
        console.log('🚨 Ctrl+Shift+A로 위험 알림 트리거됨');
      }
      // Escape 키: 알림창 닫기
      else if (event.key === 'Escape' && showCriticalAlert) {
        event.preventDefault();
        handleCloseCriticalAlert();
        console.log('✅ ESC키로 알림창 닫힘');
      }
    };

    // 전역 키보드 이벤트 리스너 등록
    document.addEventListener('keydown', handleKeyPress);
    
    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [dashboardData, showCriticalAlert, triggerManualAlert, handleCloseCriticalAlert]);

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
            <div className="flex gap-2">
              {!dataGenerated && dashboardData?.mooring_lines.length === 0 && (
                <button
                  onClick={generateSampleData}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  샘플 데이터 생성
                </button>
              )}
              {dashboardData?.mooring_lines && dashboardData.mooring_lines.length > 0 && (
                <div className="flex gap-2">
                  {!simulationRunning ? (
                    <button
                      onClick={startSimulation}
                      disabled={simulationLoading}
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                    >
                      {simulationLoading ? '시작 중...' : '🚀 실시간 시뮬레이션 시작'}
                    </button>
                  ) : (
                    <button
                      onClick={stopSimulation}
                      disabled={simulationLoading}
                      className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                    >
                      {simulationLoading ? '중지 중...' : '🛑 시뮬레이션 중지'}
                    </button>
                  )}
                  {simulationRunning && (
                    <span className="px-3 py-2 bg-green-100 text-green-800 rounded text-sm font-medium">
                      🔄 실시간 업데이트 중 (30초 간격)
                    </span>
                  )}
                  
                  {/* 키보드 알림 제어 */}
                  <div className="flex gap-2 ml-4 border-l border-blue-400 pl-4">
                    <button
                      onClick={triggerManualAlert}
                      className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
                    >
                      🚨 알림 트리거
                    </button>
                    <div className="text-xs text-blue-100 self-center">
                      키보드: <span className="font-mono bg-blue-500 px-1 rounded">F9</span> 또는{' '}
                      <span className="font-mono bg-blue-500 px-1 rounded">Space</span>
                    </div>
                  </div>
                </div>
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

            {/* Ship Top View - 8 계류줄 시스템 */}
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-3">선박 계류 상태 (상부 뷰)</h2>
              {!dashboardData.mooring_lines || dashboardData.mooring_lines.length === 0 ? (
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
                <ShipTopView
                  portLines={dashboardData.mooring_lines.filter(line => line.side === 'PORT')}
                  starboardLines={dashboardData.mooring_lines.filter(line => line.side === 'STARBOARD')}
                  onLineClick={setSelectedLineId}
                />
              )}
            </div>

            {/* Mooring Lines Grid (기존 카드 뷰 유지) */}
            <div>
              <h2 className="text-xl font-bold mb-3">계류줄 상세 정보</h2>
              {dashboardData.mooring_lines.length > 0 && (
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

            {/* 키보드 조작 안내 */}
            <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-800 mb-2">⌨️ 키보드 조작</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-blue-600 text-white rounded text-xs font-mono">F9</kbd>
                  <span className="text-gray-700">위험 알림 트리거</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-blue-600 text-white rounded text-xs font-mono">Space</kbd>
                  <span className="text-gray-700">위험 알림 트리거</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-blue-600 text-white rounded text-xs font-mono">ESC</kbd>
                  <span className="text-gray-700">알림창 닫기</span>
                </div>
              </div>
              <p className="text-xs text-blue-600 mt-2">
                💡 외부 입력 장치나 키보드를 통해 위험 상황 알림을 테스트할 수 있습니다
              </p>
            </div>

            {/* System Status */}
            <div className="mt-6 bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-3">시스템 상태</h2>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
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
                <div>
                  <p className="text-gray-600">시뮬레이션</p>
                  <p className={`text-2xl font-bold ${
                    simulationRunning ? 'text-green-600' : 'text-gray-600'
                  }`}>
                    {simulationRunning ? '실행 중' : '중지됨'}
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

      {/* Critical Alert Modal */}
      <CriticalAlertModal
        isOpen={showCriticalAlert}
        criticalLines={criticalLines}
        onClose={handleCloseCriticalAlert}
      />
    </div>
  );
}

export default App;