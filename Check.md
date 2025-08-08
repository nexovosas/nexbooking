
✅.env
✅renombrar rutas
alembic





✅ MÓDULOS Y FUNCIONALIDADES PARA UN SISTEMA DE RESERVAS (BOOKING SYSTEM)
🏨 1. GESTIÓN DE HOTELES

✅Crear, editar, eliminar hoteles

✅Activar/desactivar hotel 


✅Galería de imágenes por hotel

✅Servicios del hotel (wifi, parqueadero, desayuno, etc.)

🚪 2. HABITACIONES

✅CRUD de habitaciones

✅Relación con hotel

✅Capacidad, precio por noche, descripción

✅Tipos de cama (doble, sencilla, etc.)

✅Fotos de cada habitación

✅Amenidades por habitación (aire, TV, baño privado, etc.)

    Tarifas variables por temporada o día (precio dinámico)

📅 3. DISPONIBILIDAD Y CALENDARIO

✅Calendario visual con ocupación por habitación

✅Ver disponibilidad por fecha

✅Bloquear habitaciones (ej: mantenimiento)

    ✅Configurar estadía mínima/máxima

📦 4. RESERVAS

✅Crear reserva (check-in, check-out, user_id)

✅Relación con habitación y usuario

✅Prevenir superposición de reservas

✅Estado de reserva (pendiente, confirmada, cancelada, completada)

✅Confirmación por correo o notificación S,PT

✅Código de reserva único


🧑‍💼 6. ADMINISTRADOR DEL HOTEL

✅Panel para propietarios de hoteles

✅Gestionar solo sus hoteles y habitaciones

✅Ver calendario de reservas de su hotel

    ✅Reporte de ingresos por fechas

🔍 7. BUSCADOR Y FILTROS

✅Buscar hoteles por nombre

    ✅Filtros por:

      ✅  Capacidad

       ✅ Precio

       ✅ Servicios



📊 8. REPORTES

✅Reservas por día, semana, mes

✅Ingresos por hotel





🔐 9. SEGURIDAD Y ESCALABILIDAD

✅Conexión directa a la base de datos PostgreSQL compartida

✅Separación por microservicio FastAPI

✅Autenticación JWT en endpoints privados

✅Middleware para autorización

✅Validaciones por Pydantic en todos los esquemas


