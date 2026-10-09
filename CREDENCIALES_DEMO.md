# Credenciales de demostración

> ⚠️ **Solo para demos y pruebas locales.** Todos los datos son ficticios: personas, RUT, correos y teléfonos. La contraseña es pública. **Nunca** cargues estos datos en un entorno de cliente ni en producción. `seed.py` se niega a ejecutarse si `APP_ENV=production`.

## Cómo cargar la demo

Con la base vacía (borra `hospitalops.db` si ya existe):

```powershell
python seed.py
python -m uvicorn app.main:app --reload --port 8000
```

Abre http://127.0.0.1:8000.

- `python seed.py` carga la **demo completa**: 3 hospitales, 88 usuarios, 26 tickets, inventario con Kardex, bodega de empresa, CRM, etc.
- `python seed.py --minimo` carga solo el set base de las pruebas automáticas.
- El seed **no hace nada** si la base ya tiene usuarios. Para reiniciar la demo, borra `hospitalops.db` y vuelve a ejecutarlo.

## Contraseña

Todas las cuentas usan la misma contraseña: **`DemoSeguro2026!`**

## Empresa de servicio técnico (sin hospital asignado)

| Perfil | Nombre | Correo | Qué mostrar |
|---|---|---|---|
| Superadministrador | Admin Plataforma | `root@hospitalops.example` | Todo: clientes, equipo, bodega, cambio de hospital activo |
| Coordinador empresa | Rodrigo Campos | `coordinador@hospitalops.example` | Centro de operaciones multihospital, bodega y entrega de repuestos |
| Técnico empresa | Felipe Araya | `tecnico1@hospitalops.example` | Tickets en Norte (ventilador e incubadora), repuestos en su poder |
| Técnico empresa | Javiera Rojas | `tecnico2@hospitalops.example` | Tickets en Norte y Costa (ecógrafo, monitor fetal) |
| Técnico empresa | Cristóbal Muñoz | `tecnico3@hospitalops.example` | Tickets en Norte y Sur (rayos X, climatización de pabellón) |

## Hospital Demo Norte (Santiago)

| Perfil | Nombre | Correo | Área / cargo |
|---|---|---|---|
| Administrador hospital | Camila Administradora | `admin@norte.example` | Jefa de operaciones |
| Coordinador | Diego Coordinador | `coordinador@norte.example` | Coordinador técnico |
| Técnico | Sofía Técnica | `tecnico@norte.example` | Técnica electromedicina |
| Técnico | Andrés Pérez | `tecnico2@norte.example` | Técnico de mantenimiento |
| Solicitante | Matías Solicitante | `solicitante@norte.example` | Urgencias · Enfermero |
| Solicitante | Fernanda Lagos | `medico@norte.example` | UCI · Médica intensivista |
| Solicitante | Josefa Herrera | `tens@norte.example` | Pediatría · TENS |
| Solicitante | Pablo Reyes | `imagen@norte.example` | Imagenología · Tecnólogo médico |
| *Pendiente de aprobación* | Antonia Pendiente | `pendiente@norte.example` | No puede entrar hasta que un admin la apruebe |
| *Pendiente de aprobación* | Benjamín Castro | `pendiente2@norte.example` | No puede entrar hasta que un admin lo apruebe |
| *Rechazado* | Lucas Gutiérrez | `rechazado@norte.example` | Cuenta rechazada: no puede entrar |

## Hospital Demo Sur (Temuco)

| Perfil | Nombre | Correo | Área / cargo |
|---|---|---|---|
| Administrador hospital | Valentina Administradora | `admin@sur.example` | Administradora |
| Coordinador | Hernán Vidal | `coordinador@sur.example` | Coordinador de operaciones |
| Técnico | Carolina Núñez | `tecnico@sur.example` | Técnica de mantenimiento |
| Solicitante | Tomás Solicitante | `solicitante@sur.example` | Pabellón |
| Solicitante | Ignacia Molina | `enfermera@sur.example` | Urgencias · Enfermera |
| *Pendiente de aprobación* | Gabriel Sepúlveda | `pendiente@sur.example` | TENS |

## Clínica Demo Costa (Viña del Mar)

| Perfil | Nombre | Correo | Área / cargo |
|---|---|---|---|
| Administrador hospital | Martina Silva | `admin@costa.example` | Gerenta de operaciones |
| Coordinador | Sebastián Torres | `coordinador@costa.example` | Jefe de mantenimiento |
| Técnico | Daniela Fuentes | `tecnico@costa.example` | Técnica electromedicina |
| Solicitante | Catalina Vega | `solicitante@costa.example` | Maternidad · Matrona |
| Solicitante | Joaquín Ortiz | `urgencias@costa.example` | Urgencias · Enfermero |
| *Pendiente de aprobación* | Florencia Pizarro | `pendiente@costa.example` | Tecnóloga médica |

## Personal adicional por hospital

Además de las cuentas anteriores, cada hospital tiene 20 usuarios más. El correo sigue el formato `nombre.apellido@<hospital>.example`, sin tildes ni ñ. La contraseña es la misma: `DemoSeguro2026!`.

### Hospital Demo Norte

| Perfil | Nombre | Correo | Área / cargo |
|---|---|---|---|
| Coordinador | Claudia Morales | `claudia.morales@norte.example` | Coordinadora de turno |
| Técnico | Ricardo Salinas | `ricardo.salinas@norte.example` | Técnico en refrigeración |
| Técnico | Natalia Opazo | `natalia.opazo@norte.example` | Técnica electromedicina |
| Solicitante | Esteban Carrasco | `esteban.carrasco@norte.example` | Urgencias · Médico urgenciólogo |
| Solicitante | Valentina Saavedra | `valentina.saavedra@norte.example` | Urgencias · Enfermera |
| Solicitante | Diego Venegas | `diego.venegas@norte.example` | Urgencias · TENS |
| Solicitante | Macarena Poblete | `macarena.poblete@norte.example` | UCI · Enfermera |
| Solicitante | Francisco Aguilera | `francisco.aguilera@norte.example` | UCI · Kinesiólogo |
| Solicitante | Bárbara Cifuentes | `barbara.cifuentes@norte.example` | UCI · TENS |
| Solicitante | Gonzalo Riquelme | `gonzalo.riquelme@norte.example` | Pabellón · Anestesiólogo |
| Solicitante | Constanza Lillo | `constanza.lillo@norte.example` | Pabellón · Arsenalera |
| Solicitante | Felipe Barrientos | `felipe.barrientos@norte.example` | Pediatría · Pediatra |
| Solicitante | Antonia Zúñiga | `antonia.zuniga@norte.example` | Pediatría · Educadora de párvulos |
| Solicitante | Marcela Tapia | `marcela.tapia@norte.example` | Imagenología · Tecnóloga médica |
| Solicitante | Rodrigo Valdés | `rodrigo.valdes@norte.example` | Laboratorio · Tecnólogo médico |
| Solicitante | Pía Henríquez | `pia.henriquez@norte.example` | Laboratorio · Bioquímica |
| Solicitante | Jorge Sandoval | `jorge.sandoval@norte.example` | Esterilización · Auxiliar de esterilización |
| *Pendiente de aprobación* | Sofía Arancibia | `sofia.arancibia@norte.example` | Pediatría · Enfermera |
| *Pendiente de aprobación* | Matías Leiva | `matias.leiva@norte.example` | Pabellón · TENS |
| *Pendiente de aprobación* | Daniela Yáñez | `daniela.yanez@norte.example` | Imagenología · Tecnóloga médica |

### Hospital Demo Sur

| Perfil | Nombre | Correo | Área / cargo |
|---|---|---|---|
| Coordinador | Patricio Huenchullán | `patricio.huenchullan@sur.example` | Coordinador de mantenimiento |
| Técnico | Alejandra Painemal | `alejandra.painemal@sur.example` | Técnica electromedicina |
| Técnico | Manuel Catrileo | `manuel.catrileo@sur.example` | Técnico eléctrico |
| Solicitante | Verónica Manríquez | `veronica.manriquez@sur.example` | Urgencias · Enfermera |
| Solicitante | Cristián Paredes | `cristian.paredes@sur.example` | Urgencias · Médico urgenciólogo |
| Solicitante | Karina Alarcón | `karina.alarcon@sur.example` | Urgencias · TENS |
| Solicitante | Luis Quilodrán | `luis.quilodran@sur.example` | Pabellón · Cirujano |
| Solicitante | Paulina Ancamil | `paulina.ancamil@sur.example` | Pabellón · Arsenalera |
| Solicitante | Eduardo Bustos | `eduardo.bustos@sur.example` | Pabellón · TENS |
| Solicitante | Francisca Llanquileo | `francisca.llanquileo@sur.example` | Medicina Interna · Enfermera |
| Solicitante | Mauricio Toledo | `mauricio.toledo@sur.example` | Medicina Interna · Médico internista |
| Solicitante | Javiera Neira | `javiera.neira@sur.example` | Medicina Interna · Kinesióloga |
| Solicitante | Héctor Millán | `hector.millan@sur.example` | Esterilización · Auxiliar de esterilización |
| Solicitante | Lorena Cayupán | `lorena.cayupan@sur.example` | Esterilización · Enfermera |
| Solicitante | Ignacio Burgos | `ignacio.burgos@sur.example` | Imagenología · Tecnólogo médico |
| Solicitante | Camila Sáez | `camila.saez@sur.example` | Imagenología · Radióloga |
| Solicitante | Rosa Huaiquil | `rosa.huaiquil@sur.example` | Medicina Interna · TENS |
| *Pendiente de aprobación* | Andrés Figueroa | `andres.figueroa@sur.example` | Urgencias · Enfermero |
| *Pendiente de aprobación* | Tamara Ñancupil | `tamara.nancupil@sur.example` | Pabellón · TENS |
| *Pendiente de aprobación* | Sergio Lagos | `sergio.lagos@sur.example` | Imagenología · Tecnólogo médico |

### Clínica Demo Costa

| Perfil | Nombre | Correo | Área / cargo |
|---|---|---|---|
| Coordinador | Carolina Errázuriz | `carolina.errazuriz@costa.example` | Coordinadora de operaciones |
| Técnico | Álvaro Mella | `alvaro.mella@costa.example` | Técnico electromedicina |
| Técnico | Fernanda Olivares | `fernanda.olivares@costa.example` | Técnica en climatización |
| Solicitante | Nicolás Bravo | `nicolas.bravo@costa.example` | Urgencias · Médico urgenciólogo |
| Solicitante | Romina Castillo | `romina.castillo@costa.example` | Urgencias · Enfermera |
| Solicitante | Vicente Rubio | `vicente.rubio@costa.example` | Urgencias · TENS |
| Solicitante | Gabriela Montt | `gabriela.montt@costa.example` | Pabellón · Cirujana |
| Solicitante | Tomás Echeverría | `tomas.echeverria@costa.example` | Pabellón · Anestesiólogo |
| Solicitante | Josefina Larraín | `josefina.larrain@costa.example` | Pabellón · Arsenalera |
| Solicitante | Amanda Cortés | `amanda.cortes@costa.example` | Maternidad · Matrona |
| Solicitante | Ignacia Valenzuela | `ignacia.valenzuela@costa.example` | Maternidad · Matrona |
| Solicitante | Felipe Cáceres | `felipe.caceres@costa.example` | Maternidad · Ginecólogo |
| Solicitante | Renata Fernández | `renata.fernandez@costa.example` | Imagenología · Tecnóloga médica |
| Solicitante | Agustín Domínguez | `agustin.dominguez@costa.example` | Imagenología · Radiólogo |
| Solicitante | Elena Rivas | `elena.rivas@costa.example` | Laboratorio · Bioquímica |
| Solicitante | Martín Gallardo | `martin.gallardo@costa.example` | Laboratorio · Tecnólogo médico |
| Solicitante | Catalina Peña | `catalina.pena@costa.example` | Maternidad · TENS |
| *Pendiente de aprobación* | Bastián Moya | `bastian.moya@costa.example` | Urgencias · Enfermero |
| *Pendiente de aprobación* | Isabel Soto | `isabel.soto@costa.example` | Pabellón · TENS |
| *Pendiente de aprobación* | Emilia Carvajal | `emilia.carvajal@costa.example` | Laboratorio · Tecnóloga médica |

## Qué datos trae la demo

| Módulo | Contenido |
|---|---|
| Hospitales | 3 clientes con colores y nombre de portal propios |
| Usuarios | 88: 5 de la empresa, 31 en Norte, 26 en Sur y 26 en Costa (13 pendientes de aprobación y 1 rechazado) |
| Áreas | 17 áreas (UCI, Urgencias, Pabellón, Pediatría, Imagenología, Maternidad, etc.) |
| Tickets | 26 tickets en todos los estados y prioridades, repartidos en las últimas semanas, con comentarios y notas internas |
| Equipos | 18 equipos (ventiladores, desfibriladores, ecógrafos, autoclaves, incubadoras…); uno dado de baja |
| Inventario | 34 productos con historial Kardex; varios bajo stock mínimo para mostrar alertas |
| Conteos físicos | En Hospital Norte: uno cerrado con diferencias y otro **abierto**, listo para cerrarlo en vivo |
| Bodega empresa | 18 repuestos con costos en CLP, entregas a técnicos, consumos en tickets y una devolución |
| CRM | 11 contactos y 16 oportunidades en todas las etapas del pipeline (incluye ganadas y perdidas) |
| Auditoría | Bitácora con altas, aprobaciones, confirmaciones, entregas y consumos |

## Flujo sugerido para la demo

1. **Solicitante** (`medico@norte.example`): crea un ticket nuevo. Queda *pendiente*.
2. **Admin hospital** (`admin@norte.example`): en **Aprobaciones** aprueba a `pendiente@norte.example`; luego confirma el ticket nuevo y lo asigna a un **técnico empresa**.
3. **Coordinador empresa** (`coordinador@hospitalops.example`): revisa **Operaciones** con los tickets de los 3 hospitales y entrega repuestos desde **Bodega**.
4. **Técnico empresa** (`tecnico1@hospitalops.example`): en **Mis tickets** avanza el ticket y en **Mis repuestos** registra el consumo.
5. **Solicitante**: acepta la solución y el ticket queda cerrado.
6. Extra: en **Inventario → Conteos** (`coordinador@norte.example`) cierra el conteo abierto, y exporta el inventario a Excel.
