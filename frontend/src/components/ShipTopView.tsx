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

      
      <div className="relative mx-auto" style={{ width: '500px', height: '600px' }}>
        {/* 배 본체 */}
        <div className="absolute inset-0">
          {/* 선체 메인 */}
          <div 
            className="absolute bg-gradient-to-b from-blue-100 to-blue-200 border-4 border-blue-400"
            style={{
              left: '75px',
              top: '50px',
              width: '350px',
              height: '500px',
              borderRadius: '175px 175px 30px 30px'
            }}
          >
            {/* 선교 (브릿지) */}
            <div 
              className="absolute bg-blue-300 border-2 border-blue-500 rounded"
              style={{
                left: '125px',
                top: '200px',
                width: '100px',
                height: '60px'
              }}
            >
            </div>
            

          </div>
        </div>

        {/* 좌현 (PORT) 계류줄들 */}
        <div className="absolute left-0 top-1/2 transform -translate-y-1/2">
          <div className="space-y-8">
            {portLines.map((line, index) => (
              <div key={line.id} className="flex items-center">
                <MooringLineButton 
                  line={line} 
                  position="port" 
                  index={index} 
                />
                <div className="ml-2 w-20 h-0.5 bg-gray-600"></div>
              </div>
            ))}
          </div>
        </div>

        {/* 우현 (STARBOARD) 계류줄들 */}
        <div className="absolute right-0 top-1/2 transform -translate-y-1/2">
          <div className="space-y-8">
            {starboardLines.map((line, index) => (
              <div key={line.id} className="flex items-center">
                <div className="mr-2 w-20 h-0.5 bg-gray-600"></div>
                <MooringLineButton 
                  line={line} 
                  position="starboard" 
                  index={index} 
                />
              </div>
            ))}
          </div>
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