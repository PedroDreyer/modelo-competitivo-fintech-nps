# Presentaciones Anteriores

Carpeta para archivar las presentaciones PDF de NPS Competitivo por site y quarter.
El modelo las parsea automaticamente para enriquecer el reporte con contexto del quarter anterior.

## Como organizar los PDFs

1. Colocar cada PDF en la subcarpeta del site correspondiente:
   - `MLA/` - Argentina
   - `MLB/` - Brasil
   - `MLM/` - Mexico
   - `MLC/` - Chile

2. El nombre del archivo debe contener el quarter y el site. Ejemplo:
   - `25Q4 _ NPS Competitivo MLM [Presented].pdf`
   - `25Q1 _ NPS Competitivo MLA [Presented].pdf`

3. Cada PDF puede contener data de multiples players (el parser extrae todo).

## Como funciona

- Al ejecutar el modelo para un player/quarter, busca automaticamente la presentacion del quarter anterior.
- Ejemplo: si corres `--q2 25Q2`, busca el PDF de `25Q1` del mismo site.
- Los datos extraidos se cachean en `_cache/` como JSON para no re-parsear cada vez.
- Si el PDF cambia (checksum MD5 distinto), se re-parsea automaticamente.

## Carpeta _cache/

Generada automaticamente. Contiene JSONs con los datos extraidos de cada PDF.
No editar manualmente a menos que quieras corregir datos que el parser no capturo bien.
