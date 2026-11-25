# Contribuir al proyecto

Gracias por tu interés en contribuir. Este proyecto es un prototipo académico orientado a convertirse en un sistema productivo para la UPLA.

## Flujo de trabajo

1. **Fork + branch**: crea una rama desde `main` con el prefijo que corresponda:
   - `feat/<descripción>` — nueva funcionalidad
   - `fix/<descripción>` — corrección de bug
   - `docs/<descripción>` — cambios solo en documentación
   - `refactor/<descripción>` — reestructuración sin cambio de comportamiento
   - `chore/<descripción>` — mantenimiento (dependencias, CI, etc.)

2. **Commits convencionales**: un commit por cambio lógico, en español, siguiendo el formato:
   ```
   feat(agents): agregar agente de pagos
   fix(rag): corregir filtro por sensitivity
   docs(readme): actualizar diagrama de arquitectura
   ```

3. **Tests**: todo cambio en `apps/api/app/agents/` o `apps/api/app/rag/` debe acompañarse de tests. Corre `make test` antes de hacer push.

4. **Pull Request**: apunta a `main`. Describe qué cambia y por qué, siguiendo la plantilla.

5. **Revisión**: al menos un reviewer antes del merge.

## Estándares de código

- **Python**: formateo con `black` + `ruff`. Type hints en toda función pública.
- **TypeScript**: `strict: true` en tsconfig; `next lint` debe pasar sin warnings.
- **Commits**: en español, imperativo ("agrega", no "agregado").

## Áreas donde se necesita ayuda

- Pulir la UI del panel admin (filtros, exportación CSV).
- Streaming de respuestas con SSE.
- Agregar las 14 fichas SGC al RAG.
- Integración WhatsApp Business Platform real.
- Pipeline de evaluación continua en CI.

## Preguntas

Abre un issue con la etiqueta `question` o escribe a jaimehuaytalla@gmail.com.
