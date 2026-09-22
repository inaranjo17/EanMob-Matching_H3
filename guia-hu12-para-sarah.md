# Guía para Sarah — HU-12: Scoring de relevancia (issue #183)

Esta guía asume que ya hiciste el reclone limpio del repo (la guía anterior de "borrar y reclonar"). Aquí vamos a: (1) configurar tu firma de commits, que hoy no tienes, (2) explicarte qué son los checks automáticos que vas a ver en tu Pull Request, y (3) implementar HU-12 completo con tests.

---

## FASE 1 — Configura tu firma de commits (Verified)

Ahora mismo, cuando haces un commit, GitHub lo muestra sin ninguna etiqueta especial. Isabella sí tiene los suyos marcados como **"Verified"** (un candado verde junto al hash del commit) porque configuró esto en su máquina. Es configuración local tuya, no algo que venga con el repo — vamos a hacerlo ahora.

### 1.1 Revisa si ya tienes una llave SSH

```bash
ls -al ~/.ssh
```

Busca `id_ed25519.pub` o `id_rsa.pub`. Si existe alguno, salta a 1.3.

### 1.2 Genera una llave nueva (si no tenías ninguna)

```bash
ssh-keygen -t ed25519 -C "tu-correo-de-github@ejemplo.com"
```

Presiona Enter para aceptar la ubicación por defecto. Te pedirá una contraseña (passphrase) — puedes dejarla vacía presionando Enter dos veces para no tener que escribirla cada vez.

### 1.3 Copia tu llave pública

```bash
cat ~/.ssh/id_ed25519.pub
```

Copia toda la línea que empieza con `ssh-ed25519 AAAA...`.

### 1.4 Agrégala en GitHub como Signing Key

1. GitHub.com → tu foto de perfil → **Settings**.
2. Menú izquierdo → **SSH and GPG keys**.
3. **New SSH key**.
4. **Title**: `Laptop Sarah - signing`.
5. **Key type**: selecciona **"Signing Key"** (no "Authentication Key").
6. **Key**: pega la línea copiada.
7. **Add SSH key**.

### 1.5 Configura git en tu máquina

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

### 1.6 Confirma que tu email de git esté verificado en GitHub

```bash
git config --global user.email
```

Ese correo debe estar en GitHub → Settings → Emails, marcado como verificado. Si no coincide con ninguno de los tuyos:

```bash
git config --global user.email "tu-correo-verificado@ejemplo.com"
```

De aquí en adelante, todos tus commits van a salir con el candado **"Verified"** automáticamente, sin que tengas que hacer nada más cada vez.

---

## FASE 2 — Qué son los "checks" que vas a ver en tu PR (y cómo evitar sorpresas)

Cuando abras tu Pull Request en GitHub, vas a ver una sección que dice algo como **"2/2 checks passed"** (o 3/3, revisa la Fase 3). Esto corre automáticamente en los servidores de GitHub cada vez que subes código — **no necesitas instalar ni configurar nada en tu máquina para que esto funcione**, ya está armado en el repo desde antes.

Lo que sí revisan:
- **lint**: que tu código siga un estilo consistente (imports ordenados, sin variables sin usar, etc.), usando una herramienta llamada `ruff`.
- **smoke-test**: que la app arranque sin errores de importación.
- **test** (si ya existe, revisa la Fase 3): que las pruebas unitarias pasen.

**Para no descubrir errores recién en GitHub**, corre lo mismo localmente antes de hacer push:

```bash
pip install ruff
ruff check .
```

Si marca errores, muchos se arreglan solos con:

```bash
ruff check . --fix
```

---

## FASE 3 — Verifica si ya existe el job de pytest

Antes de empezar, revisa el archivo `.github/workflows/ci.yml` en el repo (ábrelo en VS Code después de tu `git pull`).

- **Si ves un job llamado `test` que corre `pytest`**: perfecto, ya está listo, tu PR va a mostrar 3/3 checks.
- **Si solo ves `lint` y `smoke-test`, sin `test`**: avísale a Isabella — ella tenía pendiente agregar ese job en un PR aparte (`chore/pytest-ci`) antes de que empezaras. Mientras tanto, puedes seguir con HU-12 normalmente; los tests que escribas en la Fase 5 simplemente no correrán automáticamente hasta que ese job exista, pero sí puedes correrlos tú localmente con `pytest -v`.

---

## FASE 4 — Diseño de HU-12 (contexto antes de programar)

- `/match/find` recibe `origin_address` (texto, ej. "Chapinero") y geocodifica internamente — no recibe coordenadas ni H3 ya calculados.
- Fórmula de relevancia, ya documentada por Miguel:
  ```
  relevance_score = 0.6 × score_distancia + 0.4 × score_horario
  ```
- Constantes que ya se usaron en HU-11 y se reutilizan aquí: `TIME_TOLERANCE_MINUTES = 30`, y nueva: `MAX_DISTANCE_KM = 0.5` (radio aproximado de `grid_disk(k=1)` en resolución 9).

---

## FASE 5 — Código

### 5.1 Rama, desde main actualizado

```bash
git checkout main
git pull origin main
git checkout -b feat/183-relevance-scoring
```

### 5.2 Reemplaza `app/services/h3_matching.py`

```python
from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt

import h3
from sqlalchemy.orm import Session

from app.models.trayecto import Trayecto, TripStatus
from app.services.geocoding import geocode_address

TIME_TOLERANCE_MINUTES = 30
MAX_DISTANCE_KM = 0.5  # ~ radio de grid_disk(k=1) en resolución 9


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia en línea recta entre dos coordenadas, en kilómetros."""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def score_distance(distance_km: float) -> float:
    """1.0 = misma ubicación, 0.0 = en el borde de MAX_DISTANCE_KM o más lejos."""
    return max(0.0, 1 - (distance_km / MAX_DISTANCE_KM))


def score_time(diff_minutes: float) -> float:
    """1.0 = mismo horario exacto, 0.0 = en el borde de TIME_TOLERANCE_MINUTES o más."""
    return max(0.0, 1 - (diff_minutes / TIME_TOLERANCE_MINUTES))


async def find_candidates(db: Session, origin_address: str, target_time: datetime):
    geo = await geocode_address(origin_address)
    passenger_lat, passenger_lng = geo["lat"], geo["lng"]
    passenger_h3 = geo["h3_index"]

    candidate_cells = h3.grid_disk(passenger_h3, 1)
    time_min = target_time - timedelta(minutes=TIME_TOLERANCE_MINUTES)
    time_max = target_time + timedelta(minutes=TIME_TOLERANCE_MINUTES)

    trips = (
        db.query(Trayecto)
        .filter(Trayecto.status == TripStatus.open)
        .filter(Trayecto.origin_h3.in_(candidate_cells))
        .filter(Trayecto.hora_inicio.between(time_min, time_max))
        .filter(Trayecto.available_seats > 0)
        .all()
    )

    scored = []
    for trip in trips:
        distance_km = haversine_km(
            passenger_lat, passenger_lng, float(trip.origin_lat), float(trip.origin_lng)
        )
        diff_minutes = abs((trip.hora_inicio - target_time).total_seconds()) / 60

        s_dist = score_distance(distance_km)
        s_time = score_time(diff_minutes)
        relevance_score = round(0.6 * s_dist + 0.4 * s_time, 4)

        scored.append((trip, relevance_score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored
```

### 5.3 Actualiza `app/schemas/match_schema.py`

```python
class MatchFindRequest(BaseModel):
    origin_address: str
    target_time: datetime


class MatchCandidate(BaseModel):
    id: int
    origen: str
    destino: str
    hora_inicio: datetime
    hora_fin: datetime | None
    nombre_prestador: str
    score: float
```

### 5.4 Actualiza `app/routers/match.py`

```python
@router.post("/match/find", response_model=MatchFindResponse)
async def match_find(payload: MatchFindRequest, db: Session = Depends(get_db)):
    scored_trips = await find_candidates(db, payload.origin_address, payload.target_time)
    candidates = [
        MatchCandidate(
            id=trip.id,
            origen=trip.origen,
            destino=trip.destino,
            hora_inicio=trip.hora_inicio,
            hora_fin=trip.hora_fin,
            nombre_prestador=trip.nombre_prestador,
            score=score,
        )
        for trip, score in scored_trips
    ]
    return {"candidates": candidates}
```

### 5.5 Tests unitarios

```bash
mkdir -p tests
touch tests/__init__.py tests/test_h3_matching.py
```

```python
# tests/test_h3_matching.py
import pytest

from app.services.h3_matching import (
    MAX_DISTANCE_KM,
    TIME_TOLERANCE_MINUTES,
    haversine_km,
    score_distance,
    score_time,
)


def test_score_distance_at_zero():
    assert score_distance(0.0) == 1.0


def test_score_distance_at_max_range():
    assert score_distance(MAX_DISTANCE_KM) == 0.0


def test_score_distance_beyond_max_range_clips_to_zero():
    assert score_distance(MAX_DISTANCE_KM * 3) == 0.0


def test_score_distance_halfway():
    assert score_distance(MAX_DISTANCE_KM / 2) == pytest.approx(0.5)


def test_score_time_at_zero():
    assert score_time(0.0) == 1.0


def test_score_time_at_tolerance_limit():
    assert score_time(TIME_TOLERANCE_MINUTES) == 0.0


def test_score_time_beyond_limit_clips_to_zero():
    assert score_time(TIME_TOLERANCE_MINUTES * 2) == 0.0


def test_haversine_same_point_is_zero():
    assert haversine_km(4.6486, -74.0628, 4.6486, -74.0628) == pytest.approx(0.0)


def test_haversine_known_distance_bogota():
    # Chapinero (aprox) -> Usaquén (aprox), distancia real ~6-7 km
    distance = haversine_km(4.6486, -74.0628, 4.7110, -74.0387)
    assert 5 < distance < 8
```

Corre localmente:

```bash
pytest -v
```

Deberían pasar todos en verde antes de seguir.

### 5.6 Prueba manual en `/docs`

Con tu contenedor MySQL local corriendo y 2-3 trayectos de prueba con distintos horarios/distancias (recuerda: genera el `origin_h3` real llamando a tu propio `/maps/geocode`, no lo escribas a mano — es justo el error que le costó tiempo a Isabella):

```json
{ "origin_address": "Chapinero, Bogotá", "target_time": "2026-08-25T07:20:00" }
```

Verifica que los resultados vengan ordenados de mayor a menor `score`.

---

## FASE 6 — Commit, push, PR

### 6.1 Commit

```bash
git add app/services/h3_matching.py app/schemas/match_schema.py app/routers/match.py \
        tests/test_h3_matching.py
```

```bash
git commit -m "feat(matching): add relevance scoring, result ordering, and unit tests" -m "- Add haversine_km() for real distance calculation between passenger
  and candidate trip origins
- Add score_distance() and score_time(), each normalized 0-1 and
  clipped at their respective range limits
- Compute relevance_score = 0.6*distance_score + 0.4*time_score per
  Miguel's documented formula (docs/matching/h3-matching-engine.md)
- Sort candidates by relevance_score descending before returning
- Change MatchFindRequest from origin_h3 to origin_address: the
  endpoint now geocodes internally via geocode_address(), so Node
  only needs to forward the raw search text
- Add score field to MatchCandidate response
- Add unit tests for haversine_km, score_distance, and score_time
  covering zero, midpoint, boundary, and beyond-boundary cases
- Manually verified via /docs with seeded local trips: ordering correct

Part of HU-12 (issue #183). Builds on HU-11 core matching (#179)."
```

Este commit debería salir con **Verified** ya, gracias a la Fase 1.

### 6.2 Push

```bash
git push -u origin feat/183-relevance-scoring
```

### 6.3 Abre el Pull Request

1. En GitHub, click **Compare & pull request**.
2. Título: el mismo del commit.
3. Descripción: pega las mismas viñetas.
4. Agrega `Related to #183, builds on #179`.
5. Click **Create pull request**.
6. Espera a que corran los checks (2/2 o 3/3 según lo que confirmaste en la Fase 3).
7. **Como `main` tiene branch protection activo**, el botón de merge no se va a habilitar hasta que Isabella (o quien tenga permiso) apruebe tu PR — avísale para que lo revise.

### 6.4 Merge

Una vez aprobado: **Squash and merge** → **Confirm** → **Delete branch**.

---

## Checklist

- [ ] Llave SSH generada/confirmada y agregada en GitHub como Signing Key
- [ ] `git config` de firma configurado (gpg.format, signingkey, gpgsign)
- [ ] Email de git coincide con uno verificado en GitHub
- [ ] Confirmaste si el job `test` ya existe en `ci.yml` (o avisaste a Isabella)
- [ ] Rama `feat/183-relevance-scoring` creada desde main actualizado
- [ ] Código de scoring implementado y corriendo local (`ruff check .` limpio)
- [ ] Tests escritos y pasando (`pytest -v`)
- [ ] Probado manualmente en `/docs` con datos variados
- [ ] Commit hecho (Verified ✔️), pusheado, PR abierto
- [ ] Aprobado por Isabella y mergeado con Squash and merge
