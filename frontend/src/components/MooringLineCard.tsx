import React from 'react';
import type { MooringLine } from '../types';

interface MooringLineCardProps {
  line: MooringLine;
  onClick: (lineId: number) => void;
}

const MooringLineCard: React.FC<MooringLineCardProps> = ({ line, onClick }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return 'bg-red-500';
      case 'WARNING':
        return 'bg-yellow-500';
      default:
        return 'bg-green-500';
    }
  };

  const getTensionColor = (percentage: number) => {
    if (percentage >= 120) return 'text-red-600';
    if (percentage >= 100) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => onClick(line.id)}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-800">{line.name}</h3>
          <p className="text-sm text-gray-600">
            {line.side} - {line.line_id} 
            {line.position_index !== null ? ` (위치: ${line.position_index})` : ''}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-white text-sm ${getStatusColor(line.status)}`}>
          {line.status}
        </span>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>현재 장력</span>
            <span className={`font-bold ${getTensionColor(line.tension_percentage)}`}>
              {line.current_tension.toFixed(1)} kN
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${
                line.tension_percentage >= 120 ? 'bg-red-500' :
                line.tension_percentage >= 100 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(line.tension_percentage, 150)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>기준: {line.reference_tension.toFixed(1)} kN</span>
            <span>{line.tension_percentage.toFixed(1)}%</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>잔여 수명</span>
            <span className="font-bold">
              {line.remaining_lifespan_percentage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${
                line.remaining_lifespan_percentage < 20 ? 'bg-red-500' :
                line.remaining_lifespan_percentage < 50 ? 'bg-yellow-500' : 'bg-blue-500'
              }`}
              style={{ width: `${line.remaining_lifespan_percentage}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MooringLineCard;