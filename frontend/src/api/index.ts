import axios from 'axios';
import { DashboardData, TensionChartData } from '../types';

const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000/api'
  : 'https://8000-ir0ri94bpy59cyqsm8eok-6532622b.e2b.dev/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApi = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await api.get('/dashboard');
    return response.data;
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
};