---
name: tour-skill
description: Korean elementary social-studies tour lesson helper for building and running interactive local-neighborhood, history, terrain-contour, desert/cold-climate, and climate-zone comparison map lessons with the bundled Python server. Use when the user asks Codex to run or prepare a 탐방수업, 역사탐방, 우리동네 탐방, 지형 등고선 탐색, 건조지대/한랭지대 탐방, or climate-zone comparison activity.
---

# 탐방수업

Use this skill to prepare and run Korean classroom exploration lessons with
`scripts/tour_skill.py`. The script uses only Python 3.8+ standard libraries and
serves interactive Leaflet/Three.js pages at `http://localhost:8765`.

## First Steps

1. Resolve the skill directory and run all commands from there, or use the
   absolute path to `scripts/tour_skill.py`.
2. Set UTF-8 mode before running Python on Windows:

```powershell
$env:PYTHONUTF8 = "1"
```

3. Start the local server if port 8765 is not already listening:

```powershell
$listening = netstat -an 2>$null | Select-String "127\.0\.0\.1:8765.*LISTEN"
if (-not $listening) {
    Start-Process python -ArgumentList "`"scripts\tour_skill.py`" serve" -WindowStyle Hidden
    Start-Sleep -Milliseconds 900
}
```

4. Open the relevant URL for the selected activity.

## Activity Modes

Choose the mode from the user's request.

- 역사탐방: Create a route of historical stops, then open
  `http://localhost:8765/`.
- 우리동네 탐방: Build nearby public-facility stops around a school or
  neighborhood, then open `http://localhost:8765/`.
- 지형/등고선 탐색: Generate terrain state for a mountain, plateau, trench, ridge,
  or other landform, then open `http://localhost:8765/terrain`.
- 건조지대 탐방: Run the desert climate route, then open
  `http://localhost:8765/climate`.
- 한랭지대 탐방: Run the cold climate route, then open
  `http://localhost:8765/climate`.
- 기후지대 비교 지도: Open `http://localhost:8765/climate-map`.

## History Tour

For a historical event or topic:

1. Gather 5-8 relevant places with coordinates. Prefer reliable web sources,
   Korean Wikipedia summaries, official tourism/heritage pages, and map search.
2. For each stop, prepare:
   - `name`
   - `lat`
   - `lon`
   - `historical_significance`
   - `observation_points`
   - `student_questions`
   - `student_answers`
   - `street_view_url`
3. Save the stops JSON to a UTF-8 temp file.
4. Run:

```powershell
python "scripts\tour_skill.py" tour --event "{event_name}" --locations-file "{json_file}"
python "scripts\tour_skill.py" tour-nav --action start
Start-Process "http://localhost:8765/"
```

Use `tour-nav --action next` and `tour-nav --action prev` for navigation. Use
`worksheet` or `report` to print classroom handouts.

## Neighborhood Tour

For a school or neighborhood:

1. Geocode the school/neighborhood center with Nominatim or another reliable map
   source.
2. Find nearby public facilities within about 2 km. Useful categories are:
   `community`, `government`, `police`, `fire`, `library`, `post_office`, and
   `residential`.
3. Prepare JSON in this shape:

```json
{
  "locations": {
    "community": [{ "name": "행정복지센터", "lat": 37.0, "lon": 127.0 }],
    "government": [],
    "police": [],
    "fire": [],
    "library": [],
    "post_office": [],
    "residential": []
  }
}
```

4. Run:

```powershell
python "scripts\tour_skill.py" neighborhood --region "{region_name}" --center-lat {lat} --center-lon {lon} --radius 2.0 --data-file "{json_file}"
python "scripts\tour_skill.py" tour-nav --action start
Start-Process "http://localhost:8765/"
```

## Terrain And Contour Tour

Use this mode for mountains, plateaus, valleys, trenches, ridges, seamounts, and
ocean-floor features.

1. Geocode the place or use known coordinates for ocean features.
2. Pick a radius:
   - Mountains and local landforms: 15-25 km
   - Large plateaus or basins: 50-150 km
   - Ocean trenches or ridges: 150-500 km
3. Run land terrain:

```powershell
python "scripts\tour_skill.py" terrain --name "{place_name}" --lat {lat} --lon {lon} --radius {radius_km}
Start-Process "http://localhost:8765/terrain"
```

4. Run ocean terrain with `--ocean`:

```powershell
python "scripts\tour_skill.py" terrain --name "{place_name}" --lat {lat} --lon {lon} --radius {radius_km} --ocean
Start-Process "http://localhost:8765/terrain"
```

## Climate Tours

Run one of the built-in climate datasets:

```powershell
python "scripts\tour_skill.py" climate --zone desert
Start-Process "http://localhost:8765/climate"
```

```powershell
python "scripts\tour_skill.py" climate --zone cold
Start-Process "http://localhost:8765/climate"
```

For the comparison map:

```powershell
python "scripts\tour_skill.py" climate-map
Start-Process "http://localhost:8765/climate-map"
```

## Output Files

The script writes state and generated lesson files under:

```text
C:\Users\choi2\Documents\GoogleEarth
```

If the user needs a different location, update the path constants at the top of
`scripts/tour_skill.py` before running the activity.
