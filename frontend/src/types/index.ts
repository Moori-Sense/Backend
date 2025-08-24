export interface MooringLine {
  id: number;
  name: string;
  position: string | null;
  current_tension: number;
  reference_tension: number;
  tension_percentage: number;
  remaining_lifespan_percentage: number;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL';
}

export interface WeatherData {
  temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
  wind_direction_text: string;
  pressure: number | null;
  wave_height: number | null;
  timestamp: string;
}

export interface Alert {
  id: number;
  mooring_line_id: number;
  alert_type: string;
  message: string;
  severity: string;
  is_resolved: boolean;
  resolved_at: string | null;
  created_at: string;
}

export interface DashboardData {
  mooring_lines: MooringLine[];
  current_weather: WeatherData;
  active_alerts: Alert[];
  system_status: {
    active_lines: number;
    total_lines: number;
    critical_alerts: number;
    warning_alerts: number;
    system_health: string;
  };
}

export interface TensionChartData {
  mooring_line: {
    id: number;
    name: string;
    reference_tension: number;
    max_tension: number;
  };
  data: {
    timestamp: string;
    tension: number;
    status: string;
    temperature: number | null;
    humidity: number | null;
    wind_speed: number | null;
    wind_direction: number | null;
  }[];
}