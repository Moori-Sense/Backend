import React from 'react';
import type { MooringLineSummary } from '../types';

interface CriticalAlertModalProps {
  isOpen: boolean;
  criticalLines: MooringLineSummary[];
  onClose: () => void;
}

const CriticalAlertModal: React.FC<CriticalAlertModalProps> = ({ 
  isOpen, 
  criticalLines, 
  onClose 
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onClose();
  };

  // 화면 중앙에 고정되는 모달 오버레이
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* 배경 오버레이 */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        onClick={handleConfirm}
      />
      
      {/* 모달 컨텐츠 */}
      <div className="relative bg-white rounded-xl shadow-2xl max-w-md mx-4 p-6 border-4 border-red-500 animate-pulse">
        {/* 위험 아이콘 */}
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <svg 
              className="w-10 h-10 text-red-600" 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path 
                fillRule="evenodd" 
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" 
                clipRule="evenodd" 
              />
            </svg>
          </div>
        </div>

        {/* 알림 제목 */}
        <h2 className="text-xl font-bold text-red-600 text-center mb-4">
          🚨 위험 상황 발생 🚨
        </h2>

        {/* 위험한 계류줄 목록 */}
        <div className="mb-6">
          <p className="text-gray-800 font-semibold mb-3 text-center">
            다음 계류줄에서 위험 상태가 감지되었습니다:
          </p>
          
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {criticalLines.map((line) => (
              <div 
                key={line.id} 
                className="bg-red-50 border border-red-200 rounded-lg p-3"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-bold text-red-700">{line.name}</span>
                    <span className="text-sm text-gray-600 ml-2">
                      ({line.side})
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-red-600">
                      {line.current_tension.toFixed(1)} N
                    </div>
                    <div className="text-xs text-gray-500">
                      위험 임계값 초과
                    </div>
                  </div>
                </div>
                
                {/* 장력 상태 바 */}
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>기준: {line.reference_tension.toFixed(1)}N</span>
                    <span className="text-red-600 font-bold">
                      {line.tension_percentage.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-red-600 h-2 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${Math.min(line.tension_percentage, 100)}%` 
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 조치 안내 */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6">
          <p className="text-sm text-gray-700">
            <span className="font-semibold text-yellow-700">⚠️ 즉시 조치 필요:</span><br/>
            • 계류줄 상태를 즉시 점검하세요<br/>
            • 필요시 추가 계류줄을 설치하세요<br/>
            • 기상 상황을 확인하세요
          </p>
        </div>

        {/* 확인 버튼 */}
        <div className="flex justify-center">
          <button
            onClick={handleConfirm}
            className="px-8 py-3 bg-red-600 text-white font-bold rounded-lg hover:bg-red-700 transition-colors duration-200 focus:outline-none focus:ring-4 focus:ring-red-300"
          >
            ✓ 확인했습니다
          </button>
        </div>

        {/* 닫기 버튼 (우상단) */}
        <button
          onClick={handleConfirm}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path 
              fillRule="evenodd" 
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" 
              clipRule="evenodd" 
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default CriticalAlertModal;