export type DashboardPoint = {
  year: number;
  value: number;
};

export type DashboardSeries = DashboardPoint[];

export type DashboardKpis = {
  empleo_total: number;
  growth_pct: number;
  latest_year: number;
  latest_values: DashboardPoint[];
};

export type ChatResponse = {
  message: string;
  answer: string;
};

export type LoginResponse = {
  name: string;
  username: string;
  role: string;
  token: string;
};

type LegacyDashboardResponse = {
  kpis: {
    total_empleo_miles: number;
    variacion_anual_pct: number;
    ratio_hombres_mujeres: number;
  };
  empleo_trimestral: Array<{
    periodo: string;
    valor: number;
  }>;
};

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;
const normalizedBaseUrl = rawBaseUrl?.replace(/\/+$/, '');

const DEFAULT_API_BASE_URL = '/api';

const baseUrl = normalizedBaseUrl && /^https?:\/\//.test(normalizedBaseUrl)
  ? normalizedBaseUrl
  : DEFAULT_API_BASE_URL;

const ENDPOINTS = {
  login: (import.meta.env.VITE_API_LOGIN_PATH as string | undefined) ?? '/login',
  chat: (import.meta.env.VITE_API_CHAT_PATH as string | undefined) ?? '/getResponseChat',
  dashboard: (import.meta.env.VITE_API_DASHBOARD_PATH as string | undefined) ?? '/getDatosDashboard',
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method?.toUpperCase() ?? 'GET';
  const hasBody = init?.body !== undefined;

  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      ...(hasBody || method !== 'GET' ? { 'Content-Type': 'application/json' } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

let dashboardCache: Promise<LegacyDashboardResponse> | null = null;

function getLegacyDashboard(): Promise<LegacyDashboardResponse> {
  if (!dashboardCache) {
    dashboardCache = requestJson<LegacyDashboardResponse>(ENDPOINTS.dashboard);
  }
  return dashboardCache;
}

function mapLegacySeries(response: LegacyDashboardResponse): DashboardSeries {
  return response.empleo_trimestral.map((item) => ({
    year: Number(item.periodo.toString().slice(0, 4)) || 0,
    value: Number(item.valor),
  }));
}

function mapLegacyKpis(response: LegacyDashboardResponse): DashboardKpis {
  const latestValues = mapLegacySeries(response).slice(-5);
  const latestYear = latestValues[latestValues.length - 1]?.year ?? new Date().getFullYear();

  return {
    empleo_total: Number(response.kpis.total_empleo_miles),
    growth_pct: Number(response.kpis.variacion_anual_pct),
    latest_year: latestYear,
    latest_values: latestValues,
  };
}

export const dashboardApi = {
  getKpis: async () => mapLegacyKpis(await getLegacyDashboard()),
  getSeries: async () => mapLegacySeries(await getLegacyDashboard()),
};

export const chatApi = {
  sendMessage: (message: string) =>
    requestJson<{ question: string; answer: string }>(ENDPOINTS.chat, {
      method: 'POST',
      body: JSON.stringify({ question: message }),
    }).then((response) => ({ message: response.question, answer: response.answer })),
};

export const authApi = {
  login: (username: string, password: string) =>
    requestJson<LoginResponse>(ENDPOINTS.login, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
};
