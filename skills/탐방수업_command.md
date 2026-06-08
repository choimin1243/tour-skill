# /탐방수업 — 역사탐방 + 우리동네 통합 수업 스킬

역사 탐방 또는 우리 동네 알아봐요 수업을 하나의 스킬에서 시작합니다.  
이 파일 하나로 두 수업 모두 완전히 동작합니다 (외부 스킬 파일 불필요).

---

## 라우팅 규칙

스킬 호출 시 args(입력값)를 분석하여 수업 모드를 결정합니다.

### 역사탐방 모드 트리거 키워드
"역사", "탐방", "사건", "운동", "독립", "전쟁", "항쟁", "3.1", "임진", "동학", 역사 사건명

### 우리동네 모드 트리거 키워드
"우리 동네", "우리동네", "학교", "초등학교", "중학교", "주변", "관공서", "공공시설", "시설"

### 모드 불명확 시 → 아래 메뉴 출력 후 대기

```
어떤 수업을 시작할까요?

1️⃣  역사탐방 — 역사 사건·장소를 따라가는 탐방 수업
2️⃣  우리동네 — 학교 주변 공공시설을 알아보는 수업

수업 이름 또는 번호를 입력해 주세요.
```

사용자가 번호 또는 이름을 입력하면 해당 모드를 즉시 실행합니다.

---

## ① 역사탐방 모드

사용 스크립트: `scripts\tour_skill.py`

### 수업 시작 흐름

#### 단계 1: 역사 정보 수집 (WebSearch + WebFetch)

- WebSearch: `"{사건명} 관련 역사적 장소 위치"`
- WebFetch: `https://ko.wikipedia.org/api/rest_v1/page/summary/{사건명}`
- 관련 장소 5~8개 목록 작성

#### 단계 2: 장소별 지오코딩 (WebFetch Nominatim)

각 장소:
```
GET https://nominatim.openstreetmap.org/search?q={장소명}&format=json&limit=1&accept-language=ko
```
lat, lon 추출. 실패 시 WebSearch로 좌표 검색.

#### 단계 3: 정류장 내용 작성 (수업 준비 단계)

각 장소마다:
- `historical_significance`: 역사적 의의 1~2문장
- `observation_points`: 관찰 포인트 2~3개
- `student_questions`: 탐구 질문 2~3개
- `student_answers`: 각 질문의 모범 답안
- `street_view_url`: `https://www.google.com/maps/@{lat},{lon},3a,75y,0h,90t/data=!3m1!1e1`

#### 단계 4: tour 실행 (PowerShell)

```powershell
$env:PYTHONUTF8 = "1"
$qFile = "C:\Users\choi2\Documents\GoogleEarth\temp_stops.json"
[System.IO.File]::WriteAllText($qFile, '{stops_JSON}', [System.Text.Encoding]::UTF8)
$pyArgs = @("tour", "--event", "{사건명}", "--locations-file", $qFile)
& python "scripts\tour_skill.py" @pyArgs
```

#### 단계 5: 서버 시작 + 탐방 시작

```powershell
$env:PYTHONUTF8 = "1"
$listening = netstat -an 2>$null | Select-String "127\.0\.0\.1:8765.*LISTEN"
if (-not $listening) {
    Start-Process python -ArgumentList "`"scripts\tour_skill.py`" serve" -WindowStyle Hidden
    Start-Sleep -Milliseconds 900
}
& python "scripts\tour_skill.py" tour-nav --action start
Start-Process "http://localhost:8765"
```

#### 단계 6: 결과 출력

```
🗺️ {사건명} 역사 탐방 코스
① {장소1}  ② {장소2}  ③ ...
정류장 수: N개
"탐방 시작"을 입력하면 첫 번째 정류장으로 이동합니다.
```

### 역사탐방 수업 중 명령어

#### "다음" / "이전"

```powershell
$env:PYTHONUTF8 = "1"
& python "scripts\tour_skill.py" tour-nav --action next   # 또는 prev
```

`warning` 있으면 "마지막/첫 번째 정류장입니다" 안내.

#### 정류장 출력 형식

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{circle_num} 정류장 {current+1}/{total}: {name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 위치: {lat}°N, {lon}°E
📜 역사적 의의: {historical_significance}
👁️ 관찰 포인트: ...
❓ 더보기 → 탐구 질문 + 💡 답
{'다음' 또는 '🏁 탐방 완료!'}
```

#### "퀴즈"

현재 정류장 `student_questions[0]`을 4지선다로 출력. 정답 번호 내부 기억.

#### "정답"

정답 + 해설 출력 → `tour-nav --action next` 자동 실행.

#### "활동지" / "보고서"

```powershell
$env:PYTHONUTF8 = "1"
& python "scripts\tour_skill.py" worksheet   # 또는 report
```

### 역사탐방 오류 처리

| 상황 | 대응 |
|------|------|
| Nominatim 결과 없음 | WebSearch로 좌표 재검색 |
| 역사 자료 없음 | 없다고 안내, 국가기록원 등 대체 자료 제안 |
| tour_state.json 없음 | "탐방 코스를 먼저 만들어 주세요." |
| 정류장 10개 초과 | 앞 10개만 자동 사용 |

---

## ② 우리동네 모드

사용 스크립트: `scripts\tour_skill.py`

### 수업 시작 흐름

#### 단계 1: Nominatim 지오코딩 (WebFetch)

```
GET https://nominatim.openstreetmap.org/search?q={학교명}&format=json&limit=1&accept-language=ko
```
추출: `lat`, `lon`

#### 단계 2: Overpass 시설 검색 (Python)

반경 2km bounding box: `south=lat-0.018, west=lon-0.024, north=lat+0.018, east=lon+0.024`

```powershell
$env:PYTHONUTF8 = "1"
python "C:\Users\choi2\Documents\GoogleEarth\overpass_query.py" {south} {west} {north} {east}
```

유형 분류:
| Overpass 태그 | 내부 키 | 뱃지 |
|---|---|---|
| `amenity=community_centre` | `community` | 🏘️ |
| `office=government`, `amenity=townhall` | `government` | 🏛️ |
| `amenity=police` | `police` | 👮 |
| `amenity=fire_station` | `fire` | 🚒 |
| `amenity=library` | `library` | 📚 |
| `amenity=post_office` | `post_office` | 📮 |

유형별 최대 3개, 전체 최대 10개. 결과 3개 미만이면 반경 3km로 재시도.

#### 단계 3: Wikimedia 사진 검색 (WebFetch × 시설 수, 선택)

"사진 없이 시작" 입력 시 건너뜀.

```
GET https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={시설명}&srnamespace=6&format=json&srlimit=1
```
파일명 획득 후 썸네일:
```
GET https://commons.wikimedia.org/w/api.php?action=query&titles={파일명}&prop=imageinfo&iiprop=url&iiurlwidth=400&format=json
```
실패 시 `photo_url: ""` (스크립트 내 기본 사진 자동 사용).

#### 단계 4: neighborhood 실행 (PowerShell)

```powershell
$env:PYTHONUTF8 = "1"
$dataFile = "C:\Users\choi2\Documents\GoogleEarth\temp_neighborhood.json"
[System.IO.File]::WriteAllText($dataFile, '{locations_JSON}', [System.Text.Encoding]::UTF8)
$pyArgs = @("neighborhood", "--region", "{학교명}", "--center-lat", "{lat}", "--center-lon", "{lon}", "--radius", "2.0", "--data-file", $dataFile)
& python "scripts\tour_skill.py" @pyArgs
```

#### 단계 5: 서버 시작 + 탐방 시작

```powershell
$env:PYTHONUTF8 = "1"
$listening = netstat -an 2>$null | Select-String "127\.0\.0\.1:8765.*LISTEN"
if (-not $listening) {
    Start-Process python -ArgumentList "`"scripts\tour_skill.py`" serve" -WindowStyle Hidden
    Start-Sleep -Milliseconds 900
}
& python "scripts\tour_skill.py" tour-nav --action start
Start-Process "http://localhost:8765"
```

### 우리동네 수업 중 명령어

#### "다음" / "이전"

```powershell
$env:PYTHONUTF8 = "1"
& python "scripts\tour_skill.py" tour-nav --action next   # 또는 prev
```

#### 시설 출력 형식

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{뱃지} {index}/{total}: {name}  ({distance_km}km)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 위치: {lat}°N, {lon}°E
🏙️ 시설 안내: {historical_significance}
👁️ 관찰 포인트: ...
❓ 더보기 → 탐구 질문 + 💡 답
{'다음' 또는 '🏁 탐방 완료!'}
```

#### "퀴즈"

현재 시설 `student_questions[0]`을 4지선다로 출력. 정답 번호 내부 기억.

#### "정답"

정답 + 해설 출력 → `tour-nav --action next` 자동 실행.

#### "활동지" / "보고서"

```powershell
$env:PYTHONUTF8 = "1"
& python "scripts\tour_skill.py" worksheet   # 또는 report
```

### 우리동네 오류 처리

| 상황 | 대응 |
|------|------|
| Nominatim 결과 없음 | 더 구체적인 주소 요청 |
| Overpass 결과 0개 | 반경 3km로 재시도 |
| tour_state.json 없음 | "먼저 학교명을 입력해 탐방을 시작해 주세요." |
| 시설 10개 초과 | 거리 순 10개 자동 선택 |
