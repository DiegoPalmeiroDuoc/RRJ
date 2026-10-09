# Manual de operación HospitalOps 1.1 — Empresa de soporte técnico

## Ingreso y primera configuración

1. Iniciar sesión en el dominio autorizado.
2. Entrar como `superadmin` y abrir **Clientes / hospitales**; registrar institución, código y contacto.
3. Seleccionar hospital en la barra superior; crear sus usuarios desde **Usuarios**, áreas/cargos en **Departamentos** y personalización en **Configuración**.
4. Entrar a **Equipo de técnicos** para registrar integrantes de la empresa. El técnico empresa no pertenece a ningún hospital único.
5. Cambiar contraseña desde **Mi cuenta**. Al hacerlo, se revocan otras sesiones de la misma cuenta.

## Tickets: recepción y cierre

Un solicitante aprobado crea la incidencia en **Tickets → Nuevo** indicando asunto, descripción, ubicación, categoría, prioridad y equipo. El ticket nace *pendiente*. El **administrador del hospital** confirma o rechaza. El **coordinador de empresa** ve los tickets en **Todos los hospitales**, los abre y asigna a un técnico local o global. El técnico global consulta **Mis tickets multihospital**, añade comentarios, notas internas, cambia a *en proceso* y marca *resuelto*. El solicitante acepta la solución y queda *cerrado*.

> No incluir nombres de pacientes, RUT, diagnósticos, historia clínica ni otros datos sensibles en descripciones y comentarios. HospitalOps está pensado para soporte técnico e inventario, no para atención clínica.

## Repuestos e inventario

- **Bodega central**: stock propio de la empresa prestadora. Se registran SKU, categoría, ubicación, precio bruto, precio de venta, existencias y mínimo.
- **Entrada / salida / ajuste**: movimientos trazables en Kardex empresa con motivo obligatorio.
- **Entregar a técnico**: las unidades salen de bodega y aumentan el stock individual del profesional; la suma total solo cambia con consumo o movimientos explícitos.
- **Mis repuestos**: el técnico registra consumo solamente sobre tickets propios que estén abiertos o en proceso; el Kardex vincula repuesto, técnico, hospital y ticket.
- **Devolución**: el coordinador retorna al stock central unidades que el técnico aún conserva.
- **Inventario (hospital)**: inventario por institución, separado de la bodega central. Permite conteo físico y exportación.

## CRM y otras funciones

La sección CRM muestra contactos y oportunidades por hospital, con etapas de negocio. La sección **Equipos** registra activos y números de serie hospitalarios. **Auditoría** permite a administradores revisar actividades registradas dentro del hospital.

## Permisos

- Superadmin: controla todos los hospitales y personal de empresa.
- Coordinador empresa: todas las operaciones multihospital sin administración de identidades globales.
- Técnico empresa: tickets propios y repuestos en custodia.
- Administrador hospital: gestiona su hospital y confirma tickets.
- Coordinador/técnico hospital: gestión local según sus permisos.
- Solicitante: crea y visualiza solo sus tickets.

## Soporte de incidencias

Si no puedes entrar, solicita al administrador restablecer o habilitar la cuenta. Si el sistema responde 403, verifica tu rol y hospital activo. Si hay error de inventario, revisa cantidades, existencia y asignación. Si falla el servidor, verificar primero `/ready`, logs, PostgreSQL y estado de almacenamiento; contactar al operador de infraestructura.
