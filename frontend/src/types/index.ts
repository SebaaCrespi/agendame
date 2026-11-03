// API Types matching backend schemas

export interface User {
  id: number;
  email: string;
  nombre: string;
  rol: 'CLIENTE' | 'PROVEEDOR' | 'ADMIN';
  activo: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  nombre: string;
  rol: 'CLIENTE' | 'PROVEEDOR';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface UpdateMeRequest {
  nombre?: string;
  password?: string;
}

// Profesional types
export interface Servicio {
  id: number;
  nombre: string;
  descripcion: string | null;
  duracion_min: number;
  precio: number;
  activo: boolean;
  profesional_id: number;
}

export interface Disponibilidad {
  dia_semana: number; // 0-6 (Lunes-Domingo)
  hora_inicio: string; // HH:MM:SS
  hora_fin: string; // HH:MM:SS
}

export interface ExcepcionDisponibilidad {
  id: number;
  fecha: string; // YYYY-MM-DD
  tipo: 'CERRADO' | 'HORARIO_ESPECIAL';
  hora_inicio?: string;
  hora_fin?: string;
  motivo?: string;
}

export interface Profesional {
  id: number;
  user_id: number;
  nombre: string;
  apellido: string;
  bio: string | null;
  foto_url: string | null;
  slot_duracion_min: number;
  activo: boolean;
  servicios: Servicio[];
  disponibilidad: Disponibilidad[];
  excepciones: ExcepcionDisponibilidad[];
}

/** Servicio como lo ve un cliente (solo activos). precio en centavos. */
export interface ServicioPublic {
  id: number;
  nombre: string;
  descripcion: string | null;
  duracion_min: number;
  precio: number;
}

export interface ProfesionalPublic {
  id: number;
  nombre: string;
  apellido: string;
  bio: string | null;
  foto_url: string | null;
  slot_duracion_min: number;
  activo: boolean;
  servicios: ServicioPublic[];
}

export interface ProfesionalPublicListResponse {
  items: ProfesionalPublic[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ProfesionalCreate {
  email: string;
  password: string;
  nombre: string;
  apellido: string;
  bio?: string;
  foto_url?: string;
  slot_duracion_min?: number;
  servicios: { nombre: string; descripcion?: string; duracion_min: number; precio: number }[];
}

export interface ProfesionalUpdate {
  nombre?: string;
  apellido?: string;
  bio?: string;
  foto_url?: string;
  slot_duracion_min?: number;
  activo?: boolean;
}

export interface ServicioCreate {
  nombre: string;
  descripcion?: string;
  duracion_min: number;
  precio: number;
}

export interface ServicioUpdate {
  nombre?: string;
  descripcion?: string;
  duracion_min?: number;
  precio?: number;
  activo?: boolean;
}

export interface DisponibilidadCreate {
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
}

export interface ExcepcionCreate {
  fecha: string;
  tipo: 'CERRADO' | 'HORARIO_ESPECIAL';
  hora_inicio?: string;
  hora_fin?: string;
  motivo?: string;
}

// Turno types
export type TurnoEstado =
  | 'PENDIENTE'
  | 'CONFIRMADO'
  | 'EN_CURSO'
  | 'FINALIZADO'
  | 'CANCELADO_CLIENTE'
  | 'CANCELADO_PROFESIONAL'
  | 'NO_ASISTIO';

export interface Turno {
  id: number;
  cliente_id: number;
  profesional_id: number;
  servicio_id: number;
  fecha_inicio: string; // ISO datetime
  fecha_fin: string; // ISO datetime
  estado: TurnoEstado;
  notas_cliente: string | null;
  notas_profesional: string | null;
  cancelado_por: string | null;
  motivo_cancelacion: string | null;
  cancelado_en: string | null;
  creado_por: string;
  creado_en: string;
  actualizado_en: string;
  confirmado_en: string | null;
  finalizado_en: string | null;
  profesional?: Profesional;
  servicio?: Servicio;
  cliente?: Cliente;
}

export interface Cliente {
  id: number;
  user_id: number;
  telefono: string | null;
  fecha_nacimiento: string | null;
}

export interface TurnoCreate {
  profesional_id: number;
  servicio_id: number;
  fecha: string; // YYYY-MM-DD
  hora_inicio: string; // HH:MM:SS
}

export interface TurnoFiltros {
  estado?: TurnoEstado;
  desde?: string; // YYYY-MM-DD
  hasta?: string; // YYYY-MM-DD
  page: number;
  size: number;
}

export interface TurnoListResponse {
  items: Turno[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface SlotDisponible {
  fecha: string; // YYYY-MM-DD
  hora_inicio: string; // HH:MM:SS
  hora_fin: string; // HH:MM:SS
  disponible: boolean;
}

export interface ProfesionalConSlots {
  profesional_id: number;
  profesional_nombre: string;
  slot_duracion_min: number;
  slots_por_fecha: Record<string, SlotDisponible[]>;
}

export interface DisponibilidadResponse {
  desde: string; // YYYY-MM-DD
  hasta: string; // YYYY-MM-DD
  profesionales: ProfesionalConSlots[];
}

export interface TurnoCancelar {
  motivo: string;
}

export interface TurnoEstadoUpdate {
  nuevo_estado: TurnoEstado;
}

export interface TurnoReasignar {
  nueva_fecha: string; // YYYY-MM-DD
  nueva_hora_inicio: string; // HH:MM:SS
  motivo: string;
}

export interface TurnoNotasUpdate {
  notas_profesional: string;
}

// Chatbot types
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  mensaje: string;
  session_id?: string;
}

export interface ChatResponse {
  respuesta: string;
  session_id: string;
  acciones?: ChatAction[];
}

export interface ChatAction {
  tipo: 'reservar' | 'cancelar' | 'ver_turnos' | 'ver_disponibilidad';
  datos: Record<string, unknown>;
}

// Pagination
export interface PageParams {
  page: number;
  size: number;
}

export interface FilterParams {
  q?: string;
  activo?: boolean;
}