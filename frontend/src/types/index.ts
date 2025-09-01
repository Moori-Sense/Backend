export interface MooringLine {
  id: number;
  line_id: string;  // L0, L1, L2, L3, L4, L5, L6, L7
  name: string;
  side: 'PORT' | 'STARBOARD';
  position_index: number;  // 0-3
  line_type?: 'BREAST' | 'SPRING';
  current_tension: number;
  reference_tension: number;
  max_tension?: number;  // 최대 허용 장력
  tension_percentage: number;
  remaining_lifespan_percentage: number;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL';
}

export interface MooringLineSummary extends MooringLine {
  // All fields from MooringLine
}

export interface ShipLayoutData {
  port_lines: MooringLineSummary[];
  starboard_lines: MooringLineSummary[];
  total_lines: number;
  ship_dimensions: {
    length: number;
    width: number;
    scale: string;
  };
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
  location?: string;
  description?: string;
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
  mooring_lines: MooringLineSummary[];
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

// Sensor Data Types
export interface SensorDataPoint {
  timestamp: string;
  raw_timestamp: string;
  distance_to_port: number;
  lines: {
    [key: string]: {
      tension: number;
      length: number;
    };
  };
}

export interface ProcessedSensorData {
  message: string;
  lines_updated: number;
  timestamp: string;
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
    // Real sensor data fields
    distance_to_port?: number;
    line_length?: number;
    raw_timestamp?: string;
  }[];
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'dashboard_update' | 'sensor_data_update' | 'tension_update' | 'weather_update';
  data?: any;
  timestamp: string;
  mooring_line_id?: number;
  tension_value?: number;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface TensionHistoryPoint {
  id: number;
  mooring_line_id: number;
  tension_value: number;
  distance_to_port?: number;
  line_length?: number;
  raw_timestamp?: string;
  timestamp: string;
  status?: string;
}