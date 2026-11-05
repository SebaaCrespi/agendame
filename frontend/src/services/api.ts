// API Client with axios interceptors for auth

import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type { TokenResponse } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
      // Arrays como parámetro repetido (estado=A&estado=B), el formato de FastAPI
      paramsSerializer: { indexes: null },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newToken = await this.refreshAccessToken();
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return this.client(originalRequest);
          } catch {
            // Refresh failed - redirect to login
            this.clearAuth();
            window.location.href = '/login';
            return Promise.reject(error);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token');
      }

      const response = await axios.post<TokenResponse>(`${API_URL}/api/v1/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      return access_token;
    })();

    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  // Auth endpoints
  async register(data: { email: string; password: string; nombre: string; rol: 'CLIENTE' | 'PROVEEDOR' }) {
    const response = await this.client.post<TokenResponse>('/auth/register', data);
    this.setAuth(response.data);
    return response.data;
  }

  async login(email: string, password: string) {
    const response = await this.client.post<TokenResponse>('/auth/login', { email, password });
    this.setAuth(response.data);
    return response.data;
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token');
    const response = await this.client.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken });
    this.setAuth(response.data);
    return response.data;
  }

  async getMe() {
    const response = await this.client.get<TokenResponse['user']>('/auth/me');
    return response.data;
  }

  async updateMe(data: { nombre?: string; password?: string }) {
    const response = await this.client.put<TokenResponse['user']>('/auth/me', data);
    const user = response.data;
    localStorage.setItem('user', JSON.stringify(user));
    return user;
  }

  logout() {
    this.clearAuth();
  }

  private setAuth(data: TokenResponse) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }

  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getUser(): TokenResponse['user'] | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  // Profesionales endpoints
  async getProfesionalesPublic(params?: { q?: string; page?: number; size?: number }) {
    const response = await this.client.get<import('../types').ProfesionalPublicListResponse>('/profesionales', {
      params: { size: 50, ...params },
    });
    return response.data.items;
  }

  async getProfesionalPublic(id: number) {
    const response = await this.client.get<import('../types').ProfesionalPublic>(`/profesionales/${id}`);
    return response.data;
  }

  async getProfesionalSlots(id: number, desde: string, hasta: string, servicio_id?: number) {
    const response = await this.client.get<import('../types').DisponibilidadResponse>(`/profesionales/${id}/slots`, {
      params: { desde, hasta, servicio_id },
    });
    return response.data;
  }

  // Profesional - Mi Perfil
  async getMiPerfil() {
    const response = await this.client.get<import('../types').MiPerfil>('/profesionales/me');
    return response.data;
  }

  async updateMiPerfil(data: import('../types').ProfesionalUpdate) {
    const response = await this.client.put<import('../types').Profesional>('/profesionales/me', data);
    return response.data;
  }

  async getMisServicios() {
    const response = await this.client.get<import('../types').Servicio[]>('/profesionales/me/servicios');
    return response.data;
  }

  async crearServicio(data: import('../types').ServicioCreate) {
    const response = await this.client.post<import('../types').Servicio>('/profesionales/me/servicios', data);
    return response.data;
  }

  async actualizarServicio(id: number, data: import('../types').ServicioUpdate) {
    const response = await this.client.put<import('../types').Servicio>(`/profesionales/me/servicios/${id}`, data);
    return response.data;
  }

  async desactivarServicio(id: number) {
    await this.client.delete(`/profesionales/me/servicios/${id}`);
  }

  async getMiGrilla() {
    const response = await this.client.get<import('../types').GrillaProfesional>('/profesionales/me/disponibilidad');
    return response.data;
  }

  async actualizarGrillaCompleta(grilla: import('../types').DisponibilidadCreate[]) {
    const response = await this.client.put<import('../types').GrillaProfesional>('/profesionales/me/disponibilidad', grilla);
    return response.data;
  }

  async getMisExcepciones(desde?: string, hasta?: string) {
    const response = await this.client.get<import('../types').ExcepcionDisponibilidad[]>('/profesionales/me/excepciones', {
      params: { desde, hasta },
    });
    return response.data;
  }

  async agregarExcepcion(data: import('../types').ExcepcionCreate) {
    const response = await this.client.post<import('../types').ExcepcionDisponibilidad>('/profesionales/me/excepciones', data);
    return response.data;
  }

  async eliminarExcepcion(id: number) {
    await this.client.delete(`/profesionales/me/excepciones/${id}`);
  }

  async getMisSlots(params: { desde: string; hasta: string; servicio_id?: number; excluir_turno_id?: number }) {
    const response = await this.client.get<import('../types').SlotsListResponse>('/profesionales/me/slots', { params });
    return response.data;
  }

  // Profesional - Turnos
  async getMisTurnosProfesional(filtros: import('../types').TurnoFiltrosProfesional) {
    const response = await this.client.get<import('../types').TurnoListResponse>('/profesionales/me/turnos', { params: filtros });
    return response.data;
  }

  async getTurnoProfesional(id: number) {
    const response = await this.client.get<import('../types').Turno>(`/profesionales/me/turnos/${id}`);
    return response.data;
  }

  async cambiarEstadoTurno(id: number, nuevo_estado: import('../types').TurnoEstado) {
    const response = await this.client.put<import('../types').Turno>(`/profesionales/me/turnos/${id}/estado`, { nuevo_estado });
    return response.data;
  }

  async reasignarTurno(id: number, data: import('../types').TurnoReasignar) {
    const response = await this.client.put<import('../types').Turno>(`/profesionales/me/turnos/${id}/reasignar`, data);
    return response.data;
  }

  async cancelarTurnoProfesional(id: number, motivo: string) {
    const response = await this.client.put<import('../types').Turno>(`/profesionales/me/turnos/${id}/cancelar`, { motivo });
    return response.data;
  }

  async agregarNotasTurno(id: number, notas_profesional: string) {
    const response = await this.client.put<import('../types').Turno>(`/profesionales/me/turnos/${id}/notas`, { notas_profesional });
    return response.data;
  }

  // Cliente - Turnos
  async consultarDisponibilidad(params: { desde: string; hasta: string; profesional_id?: number; servicio_id?: number }) {
    const response = await this.client.get<import('../types').DisponibilidadResponse>('/turnos/disponibilidad', { params });
    return response.data;
  }

  async crearReserva(data: import('../types').TurnoCreate) {
    const response = await this.client.post<import('../types').Turno>('/turnos', data);
    return response.data;
  }

  async getMisTurnos(filtros: import('../types').TurnoFiltros) {
    const response = await this.client.get<import('../types').TurnoListResponse>('/turnos/mis-turnos', { params: filtros });
    return response.data;
  }

  async getTurno(id: number) {
    const response = await this.client.get<import('../types').Turno>(`/turnos/${id}`);
    return response.data;
  }

  async cancelarTurnoCliente(id: number, motivo: string) {
    const response = await this.client.put<import('../types').Turno>(`/turnos/${id}/cancelar`, { motivo });
    return response.data;
  }

  // Chatbot (CU-05/06)
  async enviarMensajeChat(mensaje: string, session_id: string | null) {
    const response = await this.client.post<import('../types').ChatMessageResponse>('/chat/message', { mensaje, session_id });
    return response.data;
  }

  // Admin - Turnos
  async getAllTurnosAdmin(params: {
    page?: number;
    size?: number;
    estado?: import('../types').TurnoEstado;
    desde?: string;
    hasta?: string;
    profesional_id?: number;
    cliente_id?: number;
  }) {
    const response = await this.client.get<import('../types').TurnoListResponse>('/admin/turnos', { params });
    return response.data;
  }

  async getTurnoAdmin(id: number) {
    const response = await this.client.get<import('../types').Turno>(`/admin/turnos/${id}`);
    return response.data;
  }

  // Admin - Profesionales
  async getProfesionalesAdmin(params: { page?: number; size?: number; q?: string; activo?: boolean }) {
    const response = await this.client.get<{ items: import('../types').Profesional[]; total: number; page: number; size: number; pages: number }>('/admin/profesionales', { params });
    return response.data;
  }

  async getProfesionalAdmin(id: number) {
    const response = await this.client.get<import('../types').Profesional>(`/admin/profesionales/${id}`);
    return response.data;
  }

  async crearProfesionalAdmin(data: import('../types').ProfesionalCreate) {
    const response = await this.client.post<import('../types').Profesional>('/admin/profesionales', data);
    return response.data;
  }

  async actualizarProfesionalAdmin(id: number, data: import('../types').ProfesionalUpdate) {
    const response = await this.client.put<import('../types').Profesional>(`/admin/profesionales/${id}`, data);
    return response.data;
  }

  async desactivarProfesionalAdmin(id: number) {
    await this.client.delete(`/admin/profesionales/${id}`);
  }
}

export const api = new ApiClient();
export default api;