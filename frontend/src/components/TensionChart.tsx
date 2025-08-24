import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { format } from 'date-fns';
import type { TensionChartData } from '../types';
import { mooringLineApi } from '../api';

interface TensionChartProps {
  lineId: number;
  onClose: () => void;
}

const TensionChart: React.FC<TensionChartProps> = ({ lineId, onClose }) => {
  const [chartData, setChartData] = useState<TensionChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(24); // hours

  useEffect(() => {
    loadChartData();
  }, [lineId, timeRange]);

  const loadChartData = async () => {
    try {
      setLoading(true);
      const data = await mooringLineApi.getTensionHistory(lineId, timeRange);
      setChartData(data);
    } catch (error) {
      console.error('Failed to load chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">Loading...</div>
        </div>
      </div>
    );
  }

  if (!chartData) return null;

  const processedData = chartData.data.map(item => ({
    ...item,
    time: format(new Date(item.timestamp), 'HH:mm'),
    fullTime: format(new Date(item.timestamp), 'yyyy-MM-dd HH:mm:ss'),
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border">
          <p className="font-bold text-sm mb-2">{data.fullTime}</p>
          <div className="space-y-1 text-sm">
            <p>
              <span className="font-semibold">장력:</span>{' '}
              <span className={`font-bold ${
                data.status === 'CRITICAL' ? 'text-red-600' :
                data.status === 'WARNING' ? 'text-yellow-600' : 'text-green-600'
              }`}>
                {data.tension.toFixed(1)} kN
              </span>
            </p>
            {data.temperature !== null && (
              <p><span className="font-semibold">온도:</span> {data.temperature.toFixed(1)}°C</p>
            )}
            {data.humidity !== null && (
              <p><span className="font-semibold">습도:</span> {data.humidity.toFixed(1)}%</p>
            )}
            {data.wind_speed !== null && (
              <p><span className="font-semibold">풍속:</span> {data.wind_speed.toFixed(1)} m/s</p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-auto">
        <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              {chartData.mooring_line.name} - 장력 변화 그래프
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              기준 장력: {chartData.mooring_line.reference_tension} kN | 
              최대 장력: {chartData.mooring_line.max_tension} kN
            </p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="px-3 py-1 border rounded-lg text-sm"
            >
              <option value={6}>6시간</option>
              <option value={12}>12시간</option>
              <option value={24}>24시간</option>
              <option value={48}>48시간</option>
            </select>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Main Tension Chart */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">장력 추이</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={processedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="time" 
                  interval="preserveStartEnd"
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  label={{ value: '장력 (kN)', angle: -90, position: 'insideLeft' }}
                  domain={[0, chartData.mooring_line.max_tension * 1.1]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {/* Reference lines */}
                <ReferenceLine 
                  y={chartData.mooring_line.reference_tension} 
                  stroke="blue" 
                  strokeDasharray="5 5"
                  label={{ value: "기준 장력", position: "right" }}
                />
                <ReferenceLine 
                  y={chartData.mooring_line.reference_tension * 1.2} 
                  stroke="orange" 
                  strokeDasharray="5 5"
                  label={{ value: "경고 임계값", position: "right" }}
                />
                <ReferenceLine 
                  y={chartData.mooring_line.max_tension * 0.9} 
                  stroke="red" 
                  strokeDasharray="5 5"
                  label={{ value: "위험 임계값", position: "right" }}
                />
                
                <Line 
                  type="monotone" 
                  dataKey="tension" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={false}
                  name="장력"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Weather Correlation Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Temperature & Humidity */}
            <div>
              <h3 className="text-lg font-semibold mb-4">온도 & 습도</h3>
              <ResponsiveContainer width="100%" height={200}>
                <ComposedChart data={processedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" interval="preserveStartEnd" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="temp" orientation="left" label={{ value: '온도 (°C)', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="humidity" orientation="right" label={{ value: '습도 (%)', angle: 90, position: 'insideRight' }} />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="temp" type="monotone" dataKey="temperature" stroke="#ff7300" dot={false} name="온도" />
                  <Line yAxisId="humidity" type="monotone" dataKey="humidity" stroke="#82ca9d" dot={false} name="습도" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Wind Speed */}
            <div>
              <h3 className="text-lg font-semibold mb-4">풍속</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={processedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" interval="preserveStartEnd" tick={{ fontSize: 12 }} />
                  <YAxis label={{ value: '풍속 (m/s)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="wind_speed" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                  <Line type="monotone" dataKey="wind_speed" stroke="#8884d8" dot={false} name="풍속" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Statistics */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold mb-3">통계</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">최대 장력</p>
                <p className="font-bold text-lg">
                  {Math.max(...processedData.map(d => d.tension)).toFixed(1)} kN
                </p>
              </div>
              <div>
                <p className="text-gray-600">최소 장력</p>
                <p className="font-bold text-lg">
                  {Math.min(...processedData.map(d => d.tension)).toFixed(1)} kN
                </p>
              </div>
              <div>
                <p className="text-gray-600">평균 장력</p>
                <p className="font-bold text-lg">
                  {(processedData.reduce((sum, d) => sum + d.tension, 0) / processedData.length).toFixed(1)} kN
                </p>
              </div>
              <div>
                <p className="text-gray-600">경고 발생</p>
                <p className="font-bold text-lg">
                  {processedData.filter(d => d.status !== 'NORMAL').length} 회
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TensionChart;