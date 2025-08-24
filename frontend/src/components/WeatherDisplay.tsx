import React from 'react';
import type { WeatherData } from '../types';
import { format } from 'date-fns';

interface WeatherDisplayProps {
  weather: WeatherData;
}

const WeatherDisplay: React.FC<WeatherDisplayProps> = ({ weather }) => {
  const getWindArrow = (direction: number) => {
    const rotation = direction - 180; // Adjust for arrow pointing from wind direction
    return (
      <svg 
        className="w-6 h-6 inline-block ml-2" 
        style={{ transform: `rotate(${rotation}deg)` }}
        fill="currentColor" 
        viewBox="0 0 20 20"
      >
        <path d="M10 2l-2 7h4l-2-7zm0 0v16m0-16l-8 8m8-8l8 8" />
        <path d="M10 2l-2 5h4l-2-5z" fill="currentColor" />
        <path d="M10 2v16" stroke="currentColor" strokeWidth="2" />
      </svg>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">현재 날씨</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {weather.temperature.toFixed(1)}°C
          </div>
          <div className="text-sm text-gray-600 mt-1">온도</div>
        </div>

        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {weather.humidity.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600 mt-1">습도</div>
        </div>

        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {weather.wind_speed.toFixed(1)} m/s
          </div>
          <div className="text-sm text-gray-600 mt-1">풍속</div>
        </div>

        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-600 flex items-center justify-center">
            {weather.wind_direction_text}
            {getWindArrow(weather.wind_direction)}
          </div>
          <div className="text-sm text-gray-600 mt-1">풍향</div>
        </div>

        {weather.pressure && (
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-600">
              {weather.pressure.toFixed(0)} hPa
            </div>
            <div className="text-sm text-gray-600 mt-1">기압</div>
          </div>
        )}

        {weather.wave_height && (
          <div className="text-center p-3 bg-cyan-50 rounded-lg">
            <div className="text-2xl font-bold text-cyan-600">
              {weather.wave_height.toFixed(1)} m
            </div>
            <div className="text-sm text-gray-600 mt-1">파고</div>
          </div>
        )}
      </div>

      <div className="mt-4 text-xs text-gray-500 text-right">
        업데이트: {format(new Date(weather.timestamp), 'yyyy-MM-dd HH:mm:ss')}
      </div>
    </div>
  );
};

export default WeatherDisplay;