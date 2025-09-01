import axios from 'axios';
import type { DashboardData, TensionChartData } from '../types';

// Use relative URL for API calls when served from the same backend
const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApi = {
  getDashboard: async (): Promise<DashboardData> => {
    // Get mooring lines separately and combine with dashboard data
    const [dashboardResponse, mooringLinesResponse] = await Promise.all([
      api.get('/dashboard'),
      api.get('/mooring-lines')
    ]);
    
    return {
      ...dashboardResponse.data,
      mooring_lines: mooringLinesResponse.data
    };
  },
};

export const mooringLineApi = {
  getTensionHistory: async (lineId: number, hours: number = 24): Promise<TensionChartData> => {
    const response = await api.get(`/tension/${lineId}/chart-data?hours=${hours}`);
    return response.data;
  },
};

export const alertApi = {
  resolveAlert: async (alertId: number): Promise<void> => {
    await api.put(`/alerts/${alertId}/resolve`);
  },
};

export const simulationApi = {
  generateSampleData: async (): Promise<void> => {
    await api.post('/simulation/generate-data');
  },
  
  startSimulation: async (): Promise<void> => {
    await api.post('/simulation/start');
  },
  
  stopSimulation: async (): Promise<void> => {
    await api.post('/simulation/stop');
  },
  
  getSimulationStatus: async (): Promise<any> => {
    const response = await api.get('/simulation/status');
    return response.data;
  },
};