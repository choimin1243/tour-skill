# 🌍 탐방수업 스킬

통합 수업 스킬 — 역사탐방, 우리동네, 지형등고선, 기후지대 탐방을 하나의 스킬로 제공합니다.

## 기능 목록

### ① 역사탐방
역사 사건명을 입력하면 관련 장소를 자동 수집하여 순차 탐방합니다.
- WebSearch + Wikipedia로 장소 5~8개 자동 생성
- 정류장별 역사적 의의, 관찰 포인트, 탐구 질문/정답
- 퀴즈, 활동지, 보고서 출력

### ② 우리동네 알아봐요
학교명 입력 → 2km 반경 공공시설 자동 탐색
- Overpass API로 주민센터·경찰서·소방서·도서관·우체국 검색
- Wikimedia 실제 사진 자동 삽입
- 거리순 정렬, 시설 안내·탐구 질문 제공

### ③ 지형 등고선 탐색기
산·해저 지형의 등고선 및 3D 시각화
- **2D 등고선**: 마칭스퀘어 알고리즘, 12레벨 색상 등고선
- **3D 지형**: Three.js 인터랙티브 3D 모델 (드래그 회전, 줌)
- **단면도**: 동서 고도/수심 프로파일
- 육상(SRTM90m) / 해저(ETOPO1) 자동 선택
- Google Earth 연동 버튼

### ④ 건조지대 탐방
세계 주요 사막 6곳 순차 탐방
- 사하라 → 아라비아 → 고비 → 아타카마 → 오스트레일리아 내륙 → 타클라마칸
- 기온 바 시각화 (겨울/연평균/여름)
- 강수량 바 + 건조도 등급
- 스트리트뷰 / 구글지도 연동

### ⑤ 한랭지대 탐방
세계 주요 한랭지대 6곳 순차 탐방
- 오이먀콘 → 알래스카 → 캐나다 북부 → 스칸디나비아 → 그린란드 → 남극
- ④와 동일한 UI 구성

### ⑥ 기후지대 비교 지도
건조지대 + 한랭지대 전 세계 분포 비교
- 주요 위도선 굵게 표시 (적도·회귀선·극권)
- 🟧 건조지대 (주황) / 🟦 한랭지대 (하늘색) 영역 색상 구분
- 마우스 오버 지역명 툴팁

---

## 설치 방법

### 1. 의존성
- Python 3.8+
- 외부 라이브러리 없음 (표준 라이브러리만 사용)
- CDN 자동 로드: Leaflet 1.9.4, Three.js r128

### 2. 경로 설정
`scripts/tour_skill.py` 상단의 경로를 환경에 맞게 수정:
```python
STATE_FILE        = Path("경로/tour_state.json")
TERRAIN_FILE      = Path("경로/terrain_state.json")
CLIMATE_STATE_FILE= Path("경로/climate_state.json")
OUTPUT_DIR        = Path("경로/GoogleEarth")
```

### 3. 스킬 파일 배치
```
./tour-skill/skills/탐방수업.md        ← skills/탐방수업.md 복사
./tour-skill/commands/탐방수업.md      ← skills/탐방수업_command.md 복사
./tour-skill/scripts/tour_skill.py     ← scripts/tour_skill.py 복사
```

### 4. 서버 실행
```powershell
python tour_skill.py serve
```
브라우저에서 `http://localhost:8765` 접속

---

## 사용 방법

로컬 환경에서 `/탐방수업` 스킬 실행:

```
/탐방수업 3.1운동              → 역사탐방 모드
/탐방수업 송명초등학교 우리동네  → 우리동네 모드
/탐방수업 한라산 등고선         → 지형등고선 모드
/탐방수업 마리아나해구          → 해저 지형 모드 (ETOPO1)
/탐방수업 건조지대             → 건조지대 탐방
/탐방수업 한랭지대             → 한랭지대 탐방
/탐방수업 기후지대 비교        → 비교 지도
```

---

## 서버 엔드포인트

| URL | 기능 |
|-----|------|
| `localhost:8765/` | 역사·우리동네 탐방 네비게이터 |
| `localhost:8765/terrain` | 지형 등고선 탐색기 |
| `localhost:8765/climate` | 기후지대 탐방 |
| `localhost:8765/climate-map` | 기후지대 비교 지도 |
| `localhost:8765/state` | 현재 탐방 상태 JSON |
| `localhost:8765/elevation-grid` | 고도 격자 데이터 (SRTM/ETOPO1) |

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| 서버 | Python `http.server` + `ThreadingTCPServer` |
| 지도 | Leaflet 1.9.4 (Esri World Imagery) |
| 3D | Three.js r128 |
| 등고선 | Marching Squares (JavaScript 구현) |
| 고도 API | OpenTopoData (SRTM 90m / ETOPO1) |
| 지오코딩 | Nominatim (OpenStreetMap) |
| 시설 검색 | Overpass API |
| 사진 | Wikimedia Commons API |

---

## 라이선스

MIT License
