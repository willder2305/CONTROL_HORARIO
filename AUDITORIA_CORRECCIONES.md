# Auditoría - Correcciones de hallazgos

Fecha de implementación: 2026-10-26

Este documento registra las correcciones realizadas en `uso-local`. No contiene
credenciales, tokens, templates biométricos ni configuración privada.

| Hallazgo | Estado anterior | Corrección | Prueba | Resultado local |
| --- | --- | --- | --- | --- |
| H-01 | Resuelto previamente | No se modificó la identificación ni el algoritmo biométrico. | Suite biométrica y de marcación. | Pasa |
| H-02 | Excepciones del agente podían devolver `AGENT_ERROR` y detalles internos. | El agente traduce errores conocidos; la pantalla pública muestra mensajes operativos. | Pruebas de biometría existentes y compilación del agente. | Pasa |
| H-03 | Se mostraban referencias a desarrollo y el formulario podía mezclar feedback. | Se eliminó el texto visible de desarrollo, se expone estado real del lector y se limpia feedback al iniciar otra acción. | Búsqueda de referencias visibles, TC-12 backend. | Pasa |
| H-04 | La asignación cerraba horarios activos sin considerar la fecha efectiva. | Intervalos inclusivos, reemplazo el mismo día, prevención de rangos negativos y diagnóstico de historial en solo lectura. | `test_schedule_history_closes_intervals_and_replaces_same_day_assignment`. | Pasa; auditoría de datos pendiente de servidor |
| H-05 | Login dependía de colación MySQL, almuerzo incompleto era genérico y el horario se filtraba por ID manual. | Comparación exacta de usuario, mensajes específicos, ortografía visible corregida y selector de asignaciones. | TC-07, TC-16 y filtro inválido. | Pasa |
| H-06 | La sesión no exponía su vencimiento ni avisaba previamente. | Endpoints de estado y renovación con CSRF; aviso basado en segundos reales del backend. | Estado, renovación y CSRF. | Pasa |

## Comandos de validación local

```text
backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests
npm.cmd run build
```

Resultado: 83 pruebas backend aprobadas y build del frontend aprobado.

## Diagnóstico de historial

El comando `flask auditar-historial-horarios` solo lee los datos y reporta:

- fechas de finalización anteriores al inicio;
- grupos de filas idénticas;
- intervalos solapados por trabajador.

No repara ni elimina registros automáticamente. Debe ejecutarse después del
backup de MySQL en el servidor de pruebas antes de cualquier corrección de datos.

## Validación pendiente de servidor

El MySQL local no estaba en ejecución durante esta implementación. La auditoría
de los datos existentes y las pruebas post-deploy quedan pendientes hasta que el
servidor de pruebas esté disponible y se complete el backup requerido.
