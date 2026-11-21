# FORGED IN THE DARK FANTASY — juego de rol de ordenador

Un juego de rol en Python (pygame) al estilo de los *dungeon crawlers* en primera
persona de finales de los 80 y principios de los 90 (The Bard's Tale, Might and Magic,
Eye of the Beholder): el grupo ve el mundo con sus propios ojos, avanza room a room y
los aventureros aparecen como retratos en la parte inferior con su salud, estrés y
corrupción. Usa el reglamento **FORGED IN THE DARK FANTASY** (basado en Blades in the
Dark, de John Harper / One Seven Design).

## Ejecutar

    pip install pygame-ce      (o pygame 2)
    python main.py

## Qué hace

- **Personajes**: crear (asistente paso a paso con razas, clases, extraños, edad,
  trasfondo, límites de creación, motivación, vicio, apariencia, personalidad,
  recuerdos, amigos y enemigos, talentos), ver la ficha y eliminar.
- **Aventuras**: nueva (elige dungeon y forma un grupo de 1 a 6 personajes), cargar,
  guardar y eliminar. Los personajes se copian a la partida; al salir puedes
  actualizar también sus fichas.
- **Juego**: vista en primera persona (imagen de la room o pasillo dibujado si no
  tiene imagen), orientación y giros, mapa automático de lo explorado, salidas de
  sentido único, sonido ambiente en bucle, y todas las tiradas del reglamento:
  habilidad (esfuerzo, ayuda, heridas, crítico), resistencia, resistencia a la
  muerte, tirada en equipo, fortuna, curación, corrupción, experiencia, fase de
  descanso, traumas, ruinas y talentos.

## Controles en el juego

| Tecla | Acción |
|---|---|
| ↑ / W | avanzar |
| ↓ / S | retroceder |
| ← / A, → / D | girar |
| Q / E | paso lateral |
| RePág / AvPág | subir / bajar |
| X | salida especial |
| 1-6 | elegir personaje (clic en el retrato: idem; segundo clic: ficha) |
| T | tirada de habilidad |
| R | tirada de resistencia |
| F | ficha |
| G | guardar |
| ESC | salir |

## Archivos

- `reglas.py` — todo el reglamento mecanizado (si el DJ cambia una regla, se cambia aquí).
- `models.py` — Personaje, Partida y las clases del dungeon (formato del Editor de Dungeons).
- `formularios.py` — formularios y diálogos reutilizables.
- `screens/` — pantallas (menú, personajes, creador, ficha, aventuras, juego).
- `data/personajes`, `data/saves`, `data/dungeons` — datos guardados.
- `assets/images` (imágenes de rooms), `assets/images/retratos` (retratos opcionales
  de personajes), `assets/audio` (sonidos).

Los personajes creados con la versión anterior se convierten automáticamente al
cargarlos (Alto Elfo/Elfo de los bosques → Elfo, Mago/Clérigo → Extraño, heridas →
puntos de golpe).
