import React from 'react';
import type { MooringLineSummary } from '../types';

interface ShipTopViewProps {
  portLines: MooringLineSummary[];
  starboardLines: MooringLineSummary[];
  onLineClick: (lineId: number) => void;
}

const ShipTopView: React.FC<ShipTopViewProps> = ({ 
  portLines, 
  starboardLines, 
  onLineClick 
}) => {
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'NORMAL': return 'bg-green-500 hover:bg-green-600';
      case 'WARNING': return 'bg-yellow-500 hover:bg-yellow-600';
      case 'CRITICAL': return 'bg-red-500 hover:bg-red-600';
      default: return 'bg-gray-500 hover:bg-gray-600';
    }
  };

  const MooringLineButton: React.FC<{ 
    line: MooringLineSummary; 
    position: 'port' | 'starboard';
    index: number;
  }> = ({ line }) => (
    <button
      onClick={() => onLineClick(line.id)}
      className={`
        relative w-16 h-8 rounded-lg text-white text-xs font-bold
        transition-all duration-200 transform hover:scale-105
        shadow-lg border-2 border-white/30
        ${getStatusColor(line.status)}
      `}
      title={`${line.name}\n장력: ${line.current_tension.toFixed(2)}N\n기준: ${line.reference_tension.toFixed(2)}N\n상태: ${line.status}`}
    >
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[10px]">{line.line_id}</span>
        <span className="text-[8px] opacity-90">
          {line.current_tension.toFixed(1)}N
        </span>
      </div>
      
      {/* 장력 상태 표시 */}
      <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-white">
        <div className={`w-full h-full rounded-full ${
          line.tension_percentage > 120 ? 'bg-red-500' :
          line.tension_percentage > 100 ? 'bg-yellow-500' : 'bg-green-500'
        }`}></div>
      </div>
    </button>
  );

  return (
    <div className="bg-white rounded-xl shadow-lg p-8">
      <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
        선박 계류줄 배치도 (상단뷰)
      </h2>
      
      <div className="relative mx-auto" style={{ width: '600px', height: '400px' }}>
        {/* 배 본체 */}
        <div className="absolute inset-0">
          {/* 선체 메인 */}
          <div 
            className="absolute bg-gradient-to-b from-blue-100 to-blue-200 border-4 border-blue-400 rounded-t-full"
            style={{
              left: '100px',
              top: '50px',
              width: '400px',
              height: '300px',
              borderRadius: '200px 200px 50px 50px'
            }}
          >
            {/* 선교 (브릿지) */}
            <div 
              className="absolute bg-blue-300 border-2 border-blue-500 rounded"
              style={{
                left: '150px',
                top: '100px',
                width: '100px',
                height: '50px'
              }}
            >
              <div className="flex items-center justify-center h-full text-sm font-bold text-blue-800">
                선교
              </div>
            </div>
            
            {/* 선수 표시 */}
            <div 
              className="absolute text-center font-bold text-blue-800"
              style={{ left: '175px', top: '10px' }}
            >
              선수 (BOW)
            </div>
            
            {/* 선미 표시 */}
            <div 
              className="absolute text-center font-bold text-blue-800"
              style={{ left: '175px', bottom: '10px' }}
            >
              선미 (STERN)
            </div>
          </div>
        </div>

        {/* 좌현 (PORT) 계류줄들 */}
        <div className="absolute left-0 top-1/2 transform -translate-y-1/2">
          <div className="text-sm font-bold text-gray-700 mb-2 text-center">
            좌현 (PORT)
          </div>
          <div className="space-y-4">
            {portLines.map((line, index) => (
              <div key={line.id} className="flex items-center">
                <MooringLineButton 
                  line={line} 
                  position="port" 
                  index={index} 
                />
                <div className="ml-2 w-16 h-0.5 bg-gray-400"></div>
              </div>
            ))}
          </div>
        </div>

        {/* 우현 (STARBOARD) 계류줄들 */}
        <div className="absolute right-0 top-1/2 transform -translate-y-1/2">
          <div className="text-sm font-bold text-gray-700 mb-2 text-center">
            우현 (STARBOARD)
          </div>
          <div className="space-y-4">
            {starboardLines.map((line, index) => (
              <div key={line.id} className="flex items-center">
                <div className="mr-2 w-16 h-0.5 bg-gray-400"></div>
                <MooringLineButton 
                  line={line} 
                  position="starboard" 
                  index={index} 
                />
              </div>
            ))}
          </div>
        </div>

        {/* 범례 */}
        <div className="absolute bottom-0 left-0 bg-white/90 backdrop-blur-sm rounded-lg p-3 border">
          <div className="text-sm font-bold mb-2">상태 범례</div>
          <div className="flex flex-wrap gap-2 text-xs">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded mr-1"></div>
              <span>정상</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded mr-1"></div>
              <span>주의</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded mr-1"></div>
              <span>위험</span>
            </div>
          </div>
        </div>

        {/* 나침반 */}
        <div className="absolute top-4 right-4 w-12 h-12 bg-white rounded-full border-2 border-gray-300 flex items-center justify-center">
          <div className="text-xs font-bold text-gray-700">N</div>
          <div className="absolute w-6 h-0.5 bg-red-500 transform rotate-0"></div>
        </div>

        {/* 스케일 */}
        <div className="absolute bottom-4 right-4 text-xs text-gray-600">
          <div>Scale: 1:1000</div>
          <div>선체 길이: ~200m</div>
        </div>
      </div>

      {/* 실시간 정보 패널 */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-sm text-gray-600">총 계류줄</div>
          <div className="text-xl font-bold text-blue-600">
            {portLines.length + starboardLines.length}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-sm text-gray-600">정상 상태</div>
          <div className="text-xl font-bold text-green-600">
            {[...portLines, ...starboardLines].filter(l => l.status === 'NORMAL').length}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-sm text-gray-600">주의 상태</div>
          <div className="text-xl font-bold text-yellow-600">
            {[...portLines, ...starboardLines].filter(l => l.status === 'WARNING').length}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-sm text-gray-600">위험 상태</div>
          <div className="text-xl font-bold text-red-600">
            {[...portLines, ...starboardLines].filter(l => l.status === 'CRITICAL').length}
          </div>
        </div>
      </div>

      <div className="mt-4 text-center text-sm text-gray-600">
        💡 계류줄을 클릭하면 상세 차트를 볼 수 있습니다
      </div>
    </div>
  );
};

export default ShipTopView;