import { useState, useEffect } from 'react';
import { format, parseISO, startOfWeek, endOfWeek, addDays } from 'date-fns';
import { es } from 'date-fns/locale';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { cn } from '@/utils/cn';
import { Calendar, Clock, User, Scissors, CheckCircle, XCircle, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import type { ProfesionalPublic, ServicioPublic, DisponibilidadResponse, SlotDisponible, Turno, TurnoFiltros } from '@/types';

const formatPrecio = (centavos: number) =>
  new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(centavos / 100);

export function ClienteDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'reservar' | 'mis-turnos'>('reservar');

  // Reservar state
  const [profesionales, setProfesionales] = useState<ProfesionalPublic[]>([]);
  const [selectedProfesional, setSelectedProfesional] = useState<ProfesionalPublic | null>(null);
  const [selectedServicio, setSelectedServicio] = useState<ServicioPublic | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [disponibilidad, setDisponibilidad] = useState<DisponibilidadResponse | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<SlotDisponible | null>(null);
  const [loadingDisponibilidad, setLoadingDisponibilidad] = useState(false);
  const [reservaLoading, setReservaLoading] = useState(false);
  const [reservaError, setReservaError] = useState<string | null>(null);
  const [reservaSuccess, setReservaSuccess] = useState<string | null>(null);

  // Mis Turnos state
  const [misTurnos, setMisTurnos] = useState<Turno[]>([]);
  const [loadingTurnos, setLoadingTurnos] = useState(false);
  const [filtros, setFiltros] = useState<TurnoFiltros>({
    page: 1,
    size: 10,
  });
  const [totalPages, setTotalPages] = useState(0);

  // Load profesionales on mount
  useEffect(() => {
    loadProfesionales();
    loadMisTurnos();
  }, []);

  const loadProfesionales = async () => {
    try {
      const data = await api.getProfesionalesPublic();
      setProfesionales(data.filter(p => p.activo));
    } catch (err) {
      console.error('Error loading profesionales:', err);
    }
  };

  const loadMisTurnos = async () => {
    setLoadingTurnos(true);
    try {
      const data = await api.getMisTurnos(filtros);
      setMisTurnos(data.items);
      setTotalPages(data.pages);
    } catch (err) {
      console.error('Error loading turnos:', err);
    } finally {
      setLoadingTurnos(false);
    }
  };

  const handleProfesionalSelect = async (prof: ProfesionalPublic) => {
    setSelectedProfesional(prof);
    setSelectedServicio(null);
    setSelectedSlot(null);
    setDisponibilidad(null);
    setReservaError(null);
    setReservaSuccess(null);
  };

  const handleServicioSelect = async (servicio: ServicioPublic) => {
    if (!selectedProfesional) return;
    setSelectedServicio(servicio);
    setSelectedSlot(null);
    setReservaError(null);
    setReservaSuccess(null);
    // Pasar los valores explícitos: el estado recién seteado no está disponible todavía
    await loadDisponibilidad(selectedProfesional, servicio, selectedDate);
  };

  const loadDisponibilidad = async (
    prof: ProfesionalPublic,
    servicio: ServicioPublic,
    fecha: Date,
  ) => {
    setLoadingDisponibilidad(true);
    try {
      const desde = format(startOfWeek(fecha, { weekStartsOn: 1 }), 'yyyy-MM-dd');
      const hasta = format(endOfWeek(fecha, { weekStartsOn: 1 }), 'yyyy-MM-dd');

      const data = await api.consultarDisponibilidad({
        desde,
        hasta,
        profesional_id: prof.id,
        servicio_id: servicio.id,
      });
      setDisponibilidad(data);
    } catch (err) {
      console.error('Error loading disponibilidad:', err);
      setReservaError('Error al cargar disponibilidad');
    } finally {
      setLoadingDisponibilidad(false);
    }
  };

  const handleDateChange = (newDate: Date) => {
    setSelectedDate(newDate);
    setSelectedSlot(null);
    if (selectedProfesional && selectedServicio) {
      loadDisponibilidad(selectedProfesional, selectedServicio, newDate);
    }
  };

  const handleSlotSelect = (slot: SlotDisponible) => {
    if (!slot.disponible) return;
    setSelectedSlot(slot);
    setReservaError(null);
    setReservaSuccess(null);
  };

  const handleReservar = async () => {
    if (!selectedProfesional || !selectedServicio || !selectedSlot) return;

    setReservaLoading(true);
    setReservaError(null);
    setReservaSuccess(null);

    try {
      await api.crearReserva({
        profesional_id: selectedProfesional.id,
        servicio_id: selectedServicio.id,
        fecha: selectedSlot.fecha,
        hora_inicio: selectedSlot.hora_inicio,
      });
      setReservaSuccess('¡Turno reservado con éxito!');
      setSelectedSlot(null);
      setSelectedServicio(null);
      setSelectedProfesional(null);
      loadMisTurnos();
    } catch (err: unknown) {
      const axiosError = err as { response?: { status?: number; data?: { detail?: string } } };
      setReservaError(axiosError.response?.data?.detail || 'Error al reservar turno');
      // El horario pudo haberse ocupado: refrescar la grilla
      if (axiosError.response?.status === 409) {
        setSelectedSlot(null);
        loadDisponibilidad(selectedProfesional, selectedServicio, selectedDate);
      }
    } finally {
      setReservaLoading(false);
    }
  };

  const handleCancelarTurno = async (turno: Turno) => {
    const motivo = prompt('Motivo de la cancelación:');
    if (!motivo) return;

    try {
      await api.cancelarTurnoCliente(turno.id, motivo);
      loadMisTurnos();
    } catch (err) {
      console.error('Error cancelando turno:', err);
      alert('Error al cancelar turno');
    }
  };

  const canCancel = (turno: Turno): boolean => {
    if (!['PENDIENTE', 'CONFIRMADO'].includes(turno.estado)) return false;
    const ahora = new Date();
    const fechaTurno = new Date(turno.fecha_inicio);
    const diffHours = (fechaTurno.getTime() - ahora.getTime()) / (1000 * 60 * 60);
    return diffHours > 2;
  };

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'CONFIRMADO': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'EN_CURSO': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'FINALIZADO': return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
      case 'CANCELADO_CLIENTE': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'CANCELADO_PROFESIONAL': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
      case 'NO_ASISTIO': return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400';
      default: return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    }
  };

  const semanaActual = format(selectedDate, 'PPPP', { locale: es });
  const inicioSemana = startOfWeek(selectedDate, { weekStartsOn: 1 });
  const diasSemana = Array.from({ length: 7 }, (_, i) => addDays(inicioSemana, i));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Bienvenido, {user?.nombre}</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {[
          { id: 'reservar', label: 'Reservar turno', icon: Calendar },
          { id: 'mis-turnos', label: 'Mis turnos', icon: Clock },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'reservar' | 'mis-turnos')}
            className={cn(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === tab.id
                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            )}
          >
            <tab.icon className="h-5 w-5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Reservar */}
      {activeTab === 'reservar' && reservaError && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/30 rounded-lg text-red-700 dark:text-red-300 text-sm">
          <AlertCircle className="h-4 w-4" />
          {reservaError}
        </div>
      )}
      {activeTab === 'reservar' && reservaSuccess && (
        <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/30 rounded-lg text-green-700 dark:text-green-300 text-sm">
          <CheckCircle className="h-4 w-4" />
          {reservaSuccess}
        </div>
      )}
      {activeTab === 'reservar' && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Paso 1: Profesional */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" /> Profesional
              </CardTitle>
              <CardDescription>Selecciona un profesional</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
              {profesionales.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No hay profesionales disponibles</p>
              ) : (
                profesionales.map((prof) => (
                  <button
                    key={prof.id}
                    onClick={() => handleProfesionalSelect(prof)}
                    className={cn(
                      'w-full text-left p-3 rounded-lg border transition-all',
                      selectedProfesional?.id === prof.id
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
                        <User className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{prof.nombre} {prof.apellido}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{prof.servicios.length} servicios</p>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </CardContent>
          </Card>

          {/* Paso 2: Servicio */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scissors className="h-5 w-5" /> Servicio
              </CardTitle>
              <CardDescription>
                {selectedProfesional
                  ? `Servicios de ${selectedProfesional.nombre}`
                  : 'Primero selecciona un profesional'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
              {!selectedProfesional ? (
                <p className="text-center text-gray-500 py-8">Selecciona un profesional primero</p>
              ) : selectedProfesional.servicios.length === 0 ? (
                <p className="text-center text-gray-500 py-8">Este profesional no tiene servicios activos</p>
              ) : (
                selectedProfesional.servicios.map((servicio) => (
                  <button
                    key={servicio.id}
                    onClick={() => handleServicioSelect(servicio)}
                    className={cn(
                      'w-full text-left p-3 rounded-lg border transition-all',
                      selectedServicio?.id === servicio.id
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    )}
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{servicio.nombre}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {servicio.duracion_min} min • {formatPrecio(servicio.precio)}
                      </p>
                      {servicio.descripcion && (
                        <p className="text-xs text-gray-400 mt-1 line-clamp-2">{servicio.descripcion}</p>
                      )}
                    </div>
                  </button>
                ))
              )}
            </CardContent>
          </Card>

          {/* Paso 3: Disponibilidad y Reserva */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" /> Disponibilidad
              </CardTitle>
              <CardDescription>
                {selectedProfesional && selectedServicio
                  ? `Semana del ${format(inicioSemana, 'd MMM', { locale: es })}`
                  : 'Selecciona profesional y servicio'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Navegación de semana */}
              <div className="flex items-center justify-between">
                <Button variant="outline" size="sm" onClick={() => handleDateChange(addDays(selectedDate, -7))}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="font-medium text-gray-900 dark:text-white capitalize">{semanaActual}</span>
                <Button variant="outline" size="sm" onClick={() => handleDateChange(addDays(selectedDate, 7))}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>

              {loadingDisponibilidad ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent" />
                </div>
              ) : !selectedProfesional || !selectedServicio ? (
                <div className="text-center py-8 text-gray-500">
                  <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Selecciona un profesional y servicio para ver disponibilidad</p>
                </div>
              ) : disponibilidad?.profesionales.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No hay disponibilidad esta semana</p>
                </div>
              ) : (
                <>
                  {/* Grid de días */}
                  <div className="grid grid-cols-7 gap-1 mb-4">
                    {diasSemana.map((dia) => (
                      <div key={dia.toISOString()} className="text-center text-xs font-medium text-gray-500 dark:text-gray-400 py-1">
                        {format(dia, 'EEE', { locale: es }).toUpperCase()}
                      </div>
                    ))}
                  </div>

                  {/* Slots */}
                  <div className="max-h-[400px] overflow-y-auto space-y-3">
                    {diasSemana.map((dia) => {
                      const fechaStr = format(dia, 'yyyy-MM-dd');
                      const profConSlots = disponibilidad?.profesionales[0];
                      const slots = profConSlots?.slots_por_fecha[fechaStr] || [];

                      if (slots.length === 0) return null;

                      return (
                        <div key={fechaStr} className="space-y-2">
                          <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                            {format(dia, 'd MMM', { locale: es })}
                          </div>
                          <div className="grid grid-cols-4 gap-2">
                            {slots.map((slot) => (
                              <button
                                key={`${fechaStr}-${slot.hora_inicio}`}
                                onClick={() => handleSlotSelect(slot)}
                                disabled={!slot.disponible}
                                className={cn(
                                  'py-2 px-2 rounded-lg text-sm font-medium transition-all',
                                  selectedSlot?.fecha === slot.fecha && selectedSlot?.hora_inicio === slot.hora_inicio
                                    ? 'bg-indigo-600 text-white'
                                    : slot.disponible
                                    ? 'bg-gray-100 text-gray-700 hover:bg-indigo-100 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-indigo-900/30'
                                    : 'bg-gray-50 text-gray-300 line-through opacity-50 cursor-not-allowed dark:bg-gray-900 dark:text-gray-600'
                                )}
                              >
                                {format(parseISO(`2000-01-01T${slot.hora_inicio}`), 'HH:mm')}
                              </button>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}

              {/* Resumen y botón reservar */}
              {selectedSlot && (
                <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg border border-indigo-200 dark:border-indigo-800 space-y-3 text-gray-900 dark:text-gray-100">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                    <span className="font-medium">
                      {format(parseISO(selectedSlot.fecha), 'EEEE d MMMM', { locale: es })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                    <span className="font-medium">
                      {format(parseISO(`2000-01-01T${selectedSlot.hora_inicio}`), 'HH:mm')} -{' '}
                      {format(parseISO(`2000-01-01T${selectedSlot.hora_fin}`), 'HH:mm')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Scissors className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                    <span className="font-medium">{selectedServicio?.nombre}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <User className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                    <span className="font-medium">{selectedProfesional?.nombre} {selectedProfesional?.apellido}</span>
                  </div>


                  <Button className="w-full" size="lg" onClick={handleReservar} loading={reservaLoading}>
                    Confirmar reserva
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab: Mis Turnos */}
      {activeTab === 'mis-turnos' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" /> Mis turnos
            </CardTitle>
            <CardDescription>Gestiona tus próximas citas</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingTurnos ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent" />
              </div>
            ) : misTurnos.length === 0 ? (
              <div className="text-center py-12">
                <Calendar className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No tienes turnos</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Cuando reserves, aparecerán aquí</p>
                <Button onClick={() => setActiveTab('reservar')}>
                  Reservar mi primer turno
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {misTurnos.map((turno) => (
                  <div
                    key={turno.id}
                    className={cn(
                      'flex items-center gap-4 p-4 rounded-lg border transition-colors',
                      'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700'
                    )}
                  >
                    <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex flex-col items-center justify-center">
                      <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                        {format(parseISO(turno.fecha_inicio), 'd')}
                      </span>
                      <span className="text-xs text-indigo-600 dark:text-indigo-400">
                        {format(parseISO(turno.fecha_inicio), 'MMM', { locale: es })}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 dark:text-white truncate">
                          {turno.profesional?.nombre} {turno.profesional?.apellido}
                        </h4>
                        <span className={cn('px-2 py-0.5 text-xs font-medium rounded-full', getEstadoColor(turno.estado))}>
                          {turno.estado.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                        {turno.servicio?.nombre}
                      </p>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {format(parseISO(turno.fecha_inicio), 'HH:mm')} -{' '}
                          {format(parseISO(turno.fecha_fin), 'HH:mm')}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {canCancel(turno) && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCancelarTurno(turno)}
                        >
                          <XCircle className="h-4 w-4" />
                          Cancelar
                        </Button>
                      )}
                    </div>
                  </div>
                ))}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-6">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setFiltros((prev) => ({ ...prev, page: prev.page - 1 }));
                        loadMisTurnos();
                      }}
                      disabled={filtros.page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Página {filtros.page} de {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setFiltros((prev) => ({ ...prev, page: prev.page + 1 }));
                        loadMisTurnos();
                      }}
                      disabled={filtros.page === totalPages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}