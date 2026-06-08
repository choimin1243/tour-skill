# -*- coding: utf-8 -*-
"""
tour_skill.py — 우리동네 탐방 + 역사 탐방 독립 스크립트
외부 라이브러리 없음. 표준 Python 3.8+ 만 사용.
"""
import argparse, http.server, json, math, os, re, socketserver, sys, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

STATE_FILE        = Path("C:/Users/choi2/Documents/GoogleEarth/tour_state.json")
TERRAIN_FILE      = Path("C:/Users/choi2/Documents/GoogleEarth/terrain_state.json")
CLIMATE_STATE_FILE= Path("C:/Users/choi2/Documents/GoogleEarth/climate_state.json")
OUTPUT_DIR   = Path("C:/Users/choi2/Documents/GoogleEarth")
CIRCLE_NUMBERS = "①②③④⑤⑥⑦⑧⑨⑩"

def circle_num(i): return CIRCLE_NUMBERS[i] if i < len(CIRCLE_NUMBERS) else str(i+1)
def safe_filename(n): return re.sub(r'[\\/:*?"<>|]', '', n).strip().replace(' ', '_')[:60]
def out(d): print(json.dumps(d, ensure_ascii=False, indent=2))
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

# ── 우리 동네 교육 데이터 ──────────────────────────────────────────────────────
_W = "https://upload.wikimedia.org/wikipedia/commons/thumb/"
NEIGHBORHOOD_EDUCATION = {
    "community": {
        "photo_url": _W+"9/90/Seoul_City_Hall_20190608_001.jpg/330px-Seoul_City_Hall_20190608_001.jpg",
        "significance": "주민센터(동사무소)는 우리 동네에서 가장 가까운 관공서예요. 주민등록증 발급, 전입신고, 복지 서비스 신청 등 생활에 꼭 필요한 일들을 처리해 줍니다.",
        "observation_points": ["건물 입구에 동(洞) 이름이 적힌 간판을 찾아보세요", "태극기와 자치단체 깃발이 게양되어 있는지 확인해 보세요"],
        "student_questions": ["주민센터에서 어떤 서비스를 받을 수 있을까요?", "우리 동네 주민센터의 이름은 무엇인가요?"],
        "student_answers":   ["주민등록증 발급, 전입신고, 복지 급여 신청 등을 받을 수 있어요.", "동 이름 + 행정복지센터예요. 예: 아라1동 행정복지센터."],
    },
    "government": {
        "photo_url": _W+"9/90/Seoul_City_Hall_20190608_001.jpg/330px-Seoul_City_Hall_20190608_001.jpg",
        "significance": "구청·시청·군청은 그 지역 전체를 관리하는 기관이에요. 도로 정비, 환경 관리, 복지 정책 시행 등 우리 생활 곳곳에 영향을 미치는 큰 결정들을 이곳에서 내립니다.",
        "observation_points": ["건물 규모가 주민센터보다 얼마나 큰지 비교해 보세요", "주변에 다른 공공기관이 모여 있는지 살펴보세요"],
        "student_questions": ["구청과 주민센터는 하는 일이 어떻게 다를까요?", "우리 지역의 구청장(시장) 이름을 알고 있나요?"],
        "student_answers":   ["구청은 구 전체(예: 서구)를 관리하고, 주민센터는 작은 동(洞)을 담당해요.", "인터넷이나 시청 홈페이지에서 찾을 수 있어요."],
    },
    "police": {
        "photo_url": _W+"d/d2/Seoul_Mapo_Police_Station.JPG/330px-Seoul_Mapo_Police_Station.JPG",
        "significance": "경찰서와 파출소는 동네의 안전을 지켜주는 곳이에요. 범죄 예방, 교통 단속, 긴급 신고 출동 등을 담당해요.",
        "observation_points": ["경찰차(순찰차)가 주차된 공간을 찾아보세요", "경찰 마크(무궁화 문장)가 있는 간판을 확인해 보세요"],
        "student_questions": ["경찰이 하는 일에는 어떤 것들이 있을까요?", "위험한 상황이 생기면 몇 번에 신고해야 할까요?"],
        "student_answers":   ["범죄 예방, 교통 단속, 사고 수습, 실종자 수색 등 다양한 일을 해요.", "112예요. 위험한 일이 생기면 즉시 112에 신고해요."],
    },
    "fire": {
        "photo_url": _W+"b/b6/Fire_station_upernavik_2007-06-01.jpg/330px-Fire_station_upernavik_2007-06-01.jpg",
        "significance": "소방서와 119안전센터는 화재·사고·응급환자를 구조하는 곳이에요. 소방차와 구급차가 항상 대기하고 있어서 긴급 상황에 빠르게 출동할 수 있어요.",
        "observation_points": ["붉은색 소방차가 대기하는 차고를 찾아보세요", "소방서 건물이 넓은 도로 옆에 있는 이유를 생각해 보세요"],
        "student_questions": ["소방서는 왜 넓은 도로 근처에 있을까요?", "불이 나면 몇 번에 신고해야 할까요?"],
        "student_answers":   ["소방차가 빠르게 이동하려면 넓은 도로가 필요하기 때문이에요.", "119예요. 화재나 응급환자가 발생하면 바로 119에 신고해요."],
    },
    "library": {
        "photo_url": _W+"a/a3/SanDiegoCityCollegeLearningResource_-_bookshelf.jpg/330px-SanDiegoCityCollegeLearningResource_-_bookshelf.jpg",
        "significance": "도서관은 책·신문·DVD 등 다양한 자료를 누구나 무료로 이용할 수 있는 공공시설이에요. 공부방·독서실·전시 공간 등도 갖추고 있어요.",
        "observation_points": ["도서관 건물의 크기와 층수를 살펴보세요", "어린이 열람실이 따로 있는지 입구 안내판을 확인해 보세요"],
        "student_questions": ["도서관에서 책 말고 어떤 서비스를 이용할 수 있을까요?", "도서관이 무료로 운영되는 이유는 무엇일까요?"],
        "student_answers":   ["컴퓨터 사용, 전시 관람, 강의 참여, DVD 대여 등을 무료로 할 수 있어요.", "세금으로 운영되어 모든 시민이 공평하게 문화 서비스를 누릴 수 있도록 하기 위해서예요."],
    },
    "post_office": {
        "photo_url": _W+"b/bf/%EC%9D%B8%EC%B2%9C%EC%98%A5%EB%A0%A8%EB%8F%99%EC%9A%B0%EC%B2%B4%EA%B5%AD_2024.jpg/330px-%EC%9D%B8%EC%B2%9C%EC%98%A5%EB%A0%A8%EB%8F%99%EC%9A%B0%EC%B2%B4%EA%B5%AD_2024.jpg",
        "significance": "우체국은 편지·소포 배달과 함께 저금, 보험, 전자금융 서비스도 제공해요. 빨간 우체통이 상징이에요.",
        "observation_points": ["빨간 우체통이 건물 앞이나 근처에 있는지 찾아보세요", "우체국 로고(빨간 제비 또는 우정 마크)를 확인해 보세요"],
        "student_questions": ["우체국에서 편지 외에 어떤 서비스를 받을 수 있을까요?", "빨간 우체통의 역할은 무엇일까요?"],
        "student_answers":   ["저금·적금 관리, 보험 가입, 공과금 납부, 여권 접수 등 다양한 서비스를 받을 수 있어요.", "편지나 엽서를 넣으면 우체부 아저씨가 수거해 목적지로 배달해 주는 역할을 해요."],
    },
    "residential": {
        "photo_url": _W+"1/1a/23rd_St_6th_Av_19_-_Chelsea_Stratus.jpg/330px-23rd_St_6th_Av_19_-_Chelsea_Stratus.jpg",
        "significance": "주거지(아파트·주택단지)는 동네 사람들이 생활하는 곳이에요. 아파트·빌라·단독주택 등 다양한 형태가 있어요.",
        "observation_points": ["아파트 동수와 동 배치를 위성사진으로 확인해 보세요", "주차장·놀이터·쉼터 같은 단지 내 시설을 찾아보세요"],
        "student_questions": ["우리 동네에는 어떤 형태의 집들이 있나요?", "주거지 근처에 공공시설이 있으면 어떤 점이 편리할까요?"],
        "student_answers":   ["아파트, 빌라, 단독주택, 연립주택 등 다양한 형태가 있어요.", "병원, 학교, 도서관 등을 걸어서 이용할 수 있어 생활이 더 편리해져요."],
    },
}

NEIGHBORHOOD_TYPES = {
    "community": "🏘️ 주민센터", "government": "🏛️ 관공서",
    "police": "👮 경찰서", "fire": "🚒 소방서",
    "library": "📚 도서관", "post_office": "📮 우체국",
    "residential": "🏠 주거지",
}

# ── 네비게이터 HTML ───────────────────────────────────────────────────────────
NAVIGATOR_HTML = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>수업 탐방 네비게이터</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;font-family:'Segoe UI',sans-serif;background:#0d0d1a;color:#e0e0ff}
#hdr{height:52px;background:#111128;border-bottom:1px solid #4ecca3;
  display:flex;align-items:center;padding:0 18px;gap:16px;flex-shrink:0}
#hdr h1{font-size:1.1em;color:#4ecca3;white-space:nowrap}
#prog{color:#888;font-size:.82em;white-space:nowrap}
#sname{font-size:1.25em;font-weight:bold;color:#e94560;flex:1;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#coords{color:#4ecca3;font-family:monospace;font-size:.78em;white-space:nowrap}
#dist-badge{display:none;padding:2px 9px;border-radius:10px;font-size:.76em;
  background:#1a2e20;color:#4ecca3;border:1px solid #4ecca3;margin-left:6px;flex-shrink:0}
#dist-badge.vis{display:inline-block}
#body{display:flex;height:calc(100% - 52px)}
#panel{width:320px;flex-shrink:0;background:#13132a;border-right:1px solid #2a2a50;
  display:flex;flex-direction:column;overflow-y:auto}
.photo-wrap{width:100%;background:#0a0a18;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;min-height:180px}
#photo{width:100%;max-height:220px;object-fit:cover;transition:opacity .35s;display:none}
#photo.vis{display:block}
#photo.fade{opacity:0}
#info{padding:14px;display:flex;flex-direction:column;gap:10px;flex:1}
.label{font-size:.7em;color:#4ecca3;text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px}
.sig{font-size:.82em;color:#ccd;line-height:1.55}
.obs,.qs{font-size:.8em;color:#aab;line-height:1.6;padding-left:0;list-style:none}
.obs li{display:flex;align-items:flex-start;gap:6px;margin-bottom:5px}
.qs li{margin-bottom:8px;list-style:none;padding-left:0}
.obs-text{flex:1;line-height:1.5}
.obs-btn{flex-shrink:0;background:none;border:1px solid #4ecca3;color:#4ecca3;
  border-radius:4px;padding:1px 6px;cursor:pointer;font-size:.75em;margin-top:1px}
.obs-btn:hover{background:#4ecca322}
#sv-btns{display:none;flex-direction:row;gap:6px;margin-top:4px}
.sv-btn{background:none;border:1px solid #4ecca3;color:#4ecca3;font-size:.75em;
  padding:3px 8px;border-radius:4px;cursor:pointer}
.sv-btn:hover{background:#4ecca322}
#sv-btn-map{border-color:#888;color:#888}
#st{font-size:.78em;color:#666;padding:6px 14px 4px;border-top:1px solid #2a2a50;flex-shrink:0}
#nav-btns{display:flex;gap:8px;padding:8px 14px 12px;flex-shrink:0}
.nav-btn{flex:1;padding:8px 0;border:none;border-radius:6px;font-size:.95em;
  font-weight:bold;cursor:pointer;transition:opacity .15s}
.nav-btn:hover{opacity:.82}
.nav-btn:active{opacity:.6}
#btn-prev{background:#252540;color:#4ecca3;border:1px solid #4ecca3}
#btn-next{background:#4ecca3;color:#0d0d1a}
#btn-prev:disabled,#btn-next:disabled{opacity:.3;cursor:default}
#mapwrap{flex:1;position:relative}
#mapframe{width:100%;height:100%}
#map-overlay{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;background:#0d0d1a;pointer-events:none;transition:opacity .5s}
#map-overlay.gone{opacity:0}
#map-overlay p{color:#4ecca3;font-size:1em}
#facility-badge{display:none;padding:2px 10px;border-radius:12px;font-size:.78em;
  font-weight:bold;border:1px solid currentColor;margin-left:6px;flex-shrink:0}
#facility-badge.vis{display:inline-block}
.qs-label{font-size:.75em;letter-spacing:.08em;text-transform:uppercase;
  color:#888;margin-bottom:5px;margin-top:2px}
.qa-q{display:block;color:#ccd;margin-bottom:4px;font-size:.93em}
.ans-btn{background:none;border:1px solid #4ecca366;color:#4ecca3;
  border-radius:4px;padding:2px 8px;cursor:pointer;font-size:.78em;
  margin-bottom:2px;transition:background .15s}
.ans-btn:hover{background:#4ecca322}
.qa-a{display:none;color:#4ecca3;font-size:.9em;
  border-left:2px solid #4ecca344;padding-left:7px;margin-top:3px;margin-bottom:6px}
</style>
</head>
<body>
<div id="hdr">
  <h1>&#127758; <span id="tour-name">탐방</span></h1>
  <span id="prog"></span>
  <span id="sname">&#8212;</span>
  <span id="facility-badge"></span>
  <span id="dist-badge"></span>
  <span id="coords"></span>
</div>
<div id="body">
  <div id="panel">
    <div class="photo-wrap"><img id="photo" src="" alt="장소 사진"></div>
    <div id="info">
      <div>
        <div class="label" id="sig-label">역사적 의의</div>
        <div class="sig" id="sig">탐방을 시작하세요.</div>
      </div>
      <div id="obs-wrap" style="display:none">
        <div class="label">관찰 포인트</div>
        <ul class="obs" id="obs"></ul>
      </div>
      <div id="qs-wrap" style="display:none">
        <div class="qs-label">❓ 탐구 질문</div>
        <ul class="qs" id="qs" style="margin-top:4px"></ul>
      </div>
      <div id="sv-btns">
        <button class="sv-btn" onclick="showSV()">🔍 스트리트뷰 (새 탭)</button>
        <button class="sv-btn" id="sv-btn-map" onclick="showMap()">🛰 위성지도로 돌아가기</button>
      </div>
    </div>
    <div id="st">대기 중...</div>
    <div id="nav-btns">
      <button class="nav-btn" id="btn-prev" onclick="navClick('prev')">◀ 이전</button>
      <button class="nav-btn" id="btn-next" onclick="navClick('next')">다음 ▶</button>
    </div>
  </div>
  <div id="mapwrap">
    <div id="mapframe"></div>
    <div id="map-overlay"><p>탐방 시작을 기다리는 중...</p></div>
  </div>
</div>
<script>
var map=L.map('mapframe',{zoomControl:true,attributionControl:false}).setView([37.5,127.0],14);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  {maxZoom:20}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
  {maxZoom:20,opacity:.7}).addTo(map);

function makeIcon(emoji,flip){
  return L.divIcon({className:'',
    html:'<div style="font-size:28px;line-height:1;'+(flip?'transform:scaleX(-1);':'')
        +'filter:drop-shadow(0 2px 4px #000b)">'+emoji+'</div>',
    iconSize:[32,32],iconAnchor:[16,28],popupAnchor:[0,-28]});
}

var schoolMarker=null,facilityMarker=null,routeLine=null,distLabel=null;
var centerLat=null,centerLon=null,lastLat=null,lastLon=null,lastPhoto='';
var curLat=null,curLon=null,curSvUrl=null;
var curStopIdx=null;

var badgeMap={community:'🏘️ 주민센터',government:'🏛️ 관공서',police:'👮 경찰서',
  fire:'🚒 소방서',library:'📚 도서관',post_office:'📮 우체국',residential:'🏠 주거지',
  school:'🏫 학교',park:'🌳 공원',hospital:'🏥 병원'};
var colorMap={community:'#4ecca3',government:'#4ecca3',police:'#4f9cff',
  fire:'#e94560',library:'#dddddd',post_office:'#4f9cff',residential:'#f0a040',
  school:'#e94560',park:'#f0c040',hospital:'#dddddd'};
var emojiMap={community:'🏘️',government:'🏛️',police:'👮',fire:'🚒',
  library:'📚',post_office:'📮',residential:'🏠',school:'🏫',park:'🌳',hospital:'🏥'};

function haversinM(a,b,c,d){
  var R=6371000,p=a*Math.PI/180,q=c*Math.PI/180,
      dp=(c-a)*Math.PI/180,dl=(d-b)*Math.PI/180,
      x=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p)*Math.cos(q)*Math.sin(dl/2)*Math.sin(dl/2);
  return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));
}

function showSV(){if(curSvUrl)window.open(curSvUrl,'_blank');}
function showMap(){if(curLat!=null)moveMap(curLat,curLon);}
function moveMap(lat,lon){
  if(centerLat&&centerLon) map.fitBounds([[centerLat,centerLon],[lat,lon]],{padding:[40,40]});
  else map.setView([lat,lon],16);
  document.getElementById('map-overlay').classList.add('gone');
}

function setFacilityMarker(lat,lon,name,emoji,ft){
  if(facilityMarker)map.removeLayer(facilityMarker);
  if(routeLine)map.removeLayer(routeLine);
  if(distLabel)map.removeLayer(distLabel);
  facilityMarker=L.marker([lat,lon],{icon:makeIcon(emoji||'📍',ft==='residential')})
    .addTo(map).bindPopup('<b>'+name+'</b>');
  if(centerLat&&centerLon){
    routeLine=L.polyline([[centerLat,centerLon],[lat,lon]],
      {color:'#4ecca3',weight:2,dashArray:'6 4',opacity:.8}).addTo(map);
    var dk=haversinM(centerLat,centerLon,lat,lon);
    distLabel=L.marker([(centerLat+lat)/2,(centerLon+lon)/2],{
      icon:L.divIcon({className:'',
        html:'<div style="background:#111128cc;color:#4ecca3;font-size:11px;padding:2px 6px;border-radius:8px;border:1px solid #4ecca3;white-space:nowrap">📏 '+dk.toFixed(0)+'m</div>',
        iconSize:[80,20],iconAnchor:[40,10]}),interactive:false}).addTo(map);
  }
}
function setSchoolMarker(lat,lon,name){
  if(!schoolMarker)
    schoolMarker=L.marker([lat,lon],{icon:makeIcon('🏫')}).addTo(map).bindPopup('<b>📍 '+name+'</b>');
}

function setObsList(items,lat,lon,name){
  var ul=document.getElementById('obs'),wr=document.getElementById('obs-wrap');
  if(!items||!items.length){wr.style.display='none';return;}
  ul.innerHTML='';
  items.forEach(function(t){
    var li=document.createElement('li');
    var span=document.createElement('span');span.className='obs-text';span.textContent=t;
    var btn=document.createElement('button');btn.className='obs-btn';btn.textContent='📍';
    btn.onclick=(function(la,lo,n){return function(){
      map.setView([la,lo],19);
      if(facilityMarker)facilityMarker.openPopup();
      document.getElementById('st').textContent='🔍 현장 확대: '+n;
    };})(lat,lon,name);
    li.appendChild(btn);li.appendChild(span);ul.appendChild(li);
  });
  wr.style.display='';
}

function showAns(btn){
  var li=btn.parentElement;
  btn.style.display='none';
  var a=li.querySelector('.qa-a');
  if(a)a.style.display='block';
}

var curSvLat=0,curSvLon=0;
function openSV(){if(curSvLat)window.open('https://www.google.com/maps/@'+curSvLat+','+curSvLon+',3a,75y,0h,90t/data=!3m1!1e1','_blank')}
function openMap(){if(curSvLat)window.open('https://www.google.com/maps/search/?api=1&query='+curSvLat+','+curSvLon,'_blank')}
function navClick(action){
  var btn=document.getElementById(action==='next'?'btn-next':'btn-prev');
  btn.disabled=true;
  fetch('/nav/'+action,{method:'POST'}).then(function(r){return r.json();})
    .then(applyState).catch(function(){}).finally(function(){btn.disabled=false;});
}

function applyState(d){
  if(!d||d.error)return;
  if(d.center_lat&&d.center_lon&&centerLat==null){
    centerLat=d.center_lat;centerLon=d.center_lon;
    setSchoolMarker(centerLat,centerLon,d.tour_name||'학교');
  }
  document.getElementById('tour-name').textContent=d.tour_name||'탐방';
  document.getElementById('prog').textContent=(d.current_index+1)+' / '+d.total_stops;
  document.getElementById('btn-prev').disabled=d.current_index===0;
  document.getElementById('btn-next').disabled=d.current_index===d.total_stops-1;
  var s=d.stop;if(!s)return;
  document.getElementById('sname').textContent=s.name||'';
  var ft=s.facility_type,badge=document.getElementById('facility-badge');
  if(ft&&badgeMap[ft]){
    badge.textContent=badgeMap[ft];badge.style.color=colorMap[ft]||'#aaa';
    badge.classList.add('vis');
    document.getElementById('sname').style.color=colorMap[ft]||'#e94560';
    document.getElementById('sig-label').textContent='시설 안내';
  }else{
    badge.classList.remove('vis');badge.textContent='';
    document.getElementById('sname').style.color='#e94560';
    document.getElementById('sig-label').textContent='역사적 의의';
  }
  var db=document.getElementById('dist-badge'),dk=s.distance_km;
  if(dk!=null){db.textContent='📏 '+dk.toFixed(2)+'km';db.classList.add('vis');}
  else db.classList.remove('vis');
  document.getElementById('coords').textContent=
    'N '+(s.lat||0).toFixed(4)+'° E '+(s.lon||0).toFixed(4)+'°';
  document.getElementById('sig').textContent=s.historical_significance||'';
  setObsList(s.observation_points,s.lat,s.lon,s.name||'');
  var qs=s.student_questions||[],qa=s.student_answers||[];
  var qsWr=document.getElementById('qs-wrap'),qsUl=document.getElementById('qs');
  if(d.current_index!==curStopIdx){
    curStopIdx=d.current_index;
    if(!qs.length){qsWr.style.display='none';}else{
      qsUl.innerHTML='';
      qs.forEach(function(q,i){
        var li=document.createElement('li');
        var html='<span class="qa-q">'+(i+1)+'. '+q+'</span>';
        if(qa[i]){
          html+='<button class="ans-btn" onclick="showAns(this)">💡 정답 보기</button>'
               +'<span class="qa-a">💡 '+qa[i]+'</span>';
        }
        li.innerHTML=html;
        qsUl.appendChild(li);
      });
      qsWr.style.display='';
    }
  }
  curLat=s.lat;curLon=s.lon;curSvUrl=s.street_view_url||null;
  document.getElementById('sv-btns').style.display=s.lat?'flex':'none';
  var purl=s.photo_url||'';
  if(purl&&purl!==lastPhoto){
    lastPhoto=purl;var img=document.getElementById('photo');
    img.classList.add('fade');
    setTimeout(function(){img.src=purl;img.classList.add('vis');
      img.onload=function(){img.classList.remove('fade');};},200);
  }
  if(s.lat!==lastLat||s.lon!==lastLon){
    lastLat=s.lat;lastLon=s.lon;
    setFacilityMarker(s.lat,s.lon,s.name||'',emojiMap[ft]||'📍',ft);
    moveMap(s.lat,s.lon);
    document.getElementById('st').textContent='🗺 '+s.name+' — 다음/이전 버튼으로 이동';
  }
}

function update(){fetch('/state').then(function(r){return r.json();}).then(applyState).catch(function(){});}
update();setInterval(update,600);
</script>
</body>
</html>"""


# ── 지형 등고선 HTML ──────────────────────────────────────────────────────────
TERRAIN_HTML = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>지형 등고선 탐색기</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d1a;color:#ccd;font-family:'Segoe UI',sans-serif;
  display:flex;flex-direction:column;height:100vh;overflow:hidden}
#hdr{background:#12122a;padding:7px 14px;display:flex;align-items:center;
  gap:10px;border-bottom:1px solid #2a2a50;flex-shrink:0;flex-wrap:wrap}
#hdr h1{font-size:1em;color:#4ecca3;white-space:nowrap}
.hinfo{font-size:.78em;color:#888}
.hbtn{background:none;border:1px solid #4ecca3;color:#4ecca3;border-radius:4px;
  padding:3px 9px;cursor:pointer;font-size:.77em;transition:background .15s}
.hbtn:hover{background:#4ecca322}
#body{display:flex;flex:1;overflow:hidden}
#panel{width:44%;display:flex;flex-direction:column;border-right:1px solid #2a2a50;min-width:280px}
#tabs{display:flex;gap:5px;padding:6px 10px;background:#12122a;
  border-bottom:1px solid #2a2a50;flex-shrink:0}
.tab-btn{background:none;border:1px solid #4ecca3;color:#4ecca3;border-radius:4px;
  padding:3px 9px;cursor:pointer;font-size:.77em;transition:background .15s}
.tab-btn:hover,.tab-btn.active{background:#4ecca3;color:#0d0d1a}
#views{flex:1;position:relative;overflow:hidden}
#cv-contour,#cv-3d{position:absolute;inset:0;width:100%;height:100%}
#cv-3d{display:none}
#profile-wrap{height:120px;border-top:1px solid #2a2a50;position:relative;flex-shrink:0}
#cv-profile{width:100%;height:100%}
#plabel{position:absolute;top:3px;left:8px;font-size:.68em;color:#555}
#legend{position:absolute;bottom:8px;left:8px;background:#12122acc;
  border:1px solid #2a2a50;border-radius:5px;padding:5px 8px;font-size:.68em;
  backdrop-filter:blur(4px);pointer-events:none;z-index:5}
.lrow{display:flex;align-items:center;gap:5px;margin-bottom:2px}
.lsw{width:14px;height:8px;border-radius:2px;flex-shrink:0}
#compass{position:absolute;top:6px;right:8px;font-size:.68em;color:#4ecca366;
  pointer-events:none;z-index:5;line-height:1.2;text-align:center}
#loading{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;background:#0d0d1acc;z-index:20;flex-direction:column;gap:8px}
#loading p{color:#4ecca3;font-size:.88em}
#load-sub{font-size:.75em;color:#888!important}
#mapwrap{flex:1;position:relative}
#mapframe{width:100%;height:100%}
#ge-btn{position:absolute;top:8px;right:8px;z-index:500;background:#12122acc;
  border:1px solid #4ecca3;color:#4ecca3;border-radius:4px;padding:4px 10px;
  cursor:pointer;font-size:.77em;backdrop-filter:blur(4px)}
#ge-btn:hover{background:#4ecca322}
#tip3d{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
  font-size:.7em;color:#666;pointer-events:none}
</style>
</head>
<body>
<div id="hdr">
  <h1>⛰️ <span id="tname">지형 탐색기</span></h1>
  <span class="hinfo" id="hcoord"></span>
  <span class="hinfo" id="helev"></span>
  <button class="hbtn" id="gebtn">🌏 Google Earth</button>
</div>
<div id="body">
  <div id="panel">
    <div id="tabs">
      <button class="tab-btn active" id="tab-c" onclick="switchTab('c')">🗺️ 등고선 (위에서)</button>
      <button class="tab-btn" id="tab-3" onclick="switchTab('3')">⛰️ 3D 지형</button>
    </div>
    <div id="views">
      <canvas id="cv-contour"></canvas>
      <canvas id="cv-3d"></canvas>
      <div id="loading">
        <p>⏳ 고도 데이터 로딩 중...</p>
        <p id="load-sub"></p>
      </div>
      <div id="legend">
        <div class="lrow"><div class="lsw" style="background:#143c78"></div><span id="leg0"></span></div>
        <div class="lrow"><div class="lsw" style="background:#1e7a1e"></div><span>저지대</span></div>
        <div class="lrow"><div class="lsw" style="background:#a8c840"></div><span>중간</span></div>
        <div class="lrow"><div class="lsw" style="background:#c87830"></div><span>고지대</span></div>
        <div class="lrow"><div class="lsw" style="background:#f0f0ee"></div><span id="leg1"></span></div>
      </div>
      <div id="compass">N<br>W·+·E<br>S</div>
      <div id="tip3d" style="display:none;position:absolute;bottom:8px;left:50%;transform:translateX(-50%);font-size:.7em;color:#666;pointer-events:none;white-space:nowrap">마우스 드래그: 회전 &nbsp;|&nbsp; 스크롤: 줌</div>
    </div>
    <div id="profile-wrap">
      <div id="plabel">📊 동서 단면도</div>
      <canvas id="cv-profile"></canvas>
    </div>
  </div>
  <div id="mapwrap">
    <div id="mapframe"></div>
    <button id="ge-btn" id="ge-btn">🌏 Google Earth로 열기</button>
  </div>
</div>
<script>
var tLat=0,tLon=0,tName='',tRadius=15,tOcean=false;
var grid=null,minE=0,maxE=1000,activeTab='c';
var rdr3=null,scene3=null,cam3=null,animId=null;

// Satellite map
var map=L.map('mapframe',{zoomControl:true,attributionControl:false}).setView([37,127],9);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:20}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:20,opacity:.7}).addTo(map);
var mainMarker=null;

function geUrl(){return 'https://earth.google.com/web/@'+tLat+','+tLon+',0a,'+Math.round(tRadius*3000)+'d,35y,0h,45t,0r';}
document.getElementById('gebtn').onclick=function(){window.open(geUrl(),'_blank');};
document.getElementById('ge-btn').onclick=function(){window.open(geUrl(),'_blank');};

// ─── Elevation colour stops ────────────────────────────────────────
// Colour stops cover full range: ocean depth (negative) → land peaks
// t=0 → minE (may be very negative), t=1 → maxE
// We embed a SEABED flag: if minE < -50, ocean mode
var OCEAN_MODE=false;
var CSTOPS_LAND=[
  [0.00,[20,50,130]],
  [0.10,[20,100,50]],
  [0.28,[50,140,40]],
  [0.48,[168,160,55]],
  [0.65,[170,95,35]],
  [0.82,[125,65,45]],
  [1.00,[240,238,235]]
];
var CSTOPS_OCEAN=[
  [0.00,[5,5,30]],
  [0.12,[10,20,80]],
  [0.28,[15,55,140]],
  [0.45,[20,100,175]],
  [0.58,[30,150,200]],
  [0.70,[60,190,210]],
  [0.80,[120,210,180]],
  [0.88,[170,210,120]],
  [0.93,[100,160,70]],
  [0.97,[170,130,60]],
  [1.00,[240,238,235]]
];
var CSTOPS=CSTOPS_LAND;
function elevRGB(t){
  t=Math.max(0,Math.min(1,t));
  for(var i=1;i<CSTOPS.length;i++){
    var a=CSTOPS[i-1],b=CSTOPS[i];
    if(t<=b[0]){
      var f=(t-a[0])/(b[0]-a[0]);
      return [a[1][0]+(b[1][0]-a[1][0])*f,
              a[1][1]+(b[1][1]-a[1][1])*f,
              a[1][2]+(b[1][2]-a[1][2])*f];
    }
  }
  return [240,238,235];
}
function rgba(t,a){var c=elevRGB(t);return 'rgba('+Math.round(c[0])+','+Math.round(c[1])+','+Math.round(c[2])+','+(a||1)+')';}

// ─── Bilinear interpolation ────────────────────────────────────────
function bilerp(g,r,c){
  var R=g.length,C=g[0].length;
  var r0=Math.floor(r),r1=Math.min(r0+1,R-1),c0=Math.floor(c),c1=Math.min(c0+1,C-1);
  var fr=r-r0,fc=c-c0;
  return g[r0][c0]*(1-fr)*(1-fc)+g[r0][c1]*(1-fr)*fc+g[r1][c0]*fr*(1-fc)+g[r1][c1]*fr*fc;
}

// ─── Marching squares ──────────────────────────────────────────────
// edges: 0=top 1=right 2=bottom 3=left
var MST={1:[[2,3]],2:[[1,2]],3:[[1,3]],4:[[0,1]],5:[[0,3],[1,2]],
         6:[[0,2]],7:[[0,3]],8:[[3,0]],9:[[2,0]],10:[[3,1],[2,0]],
         11:[[1,0]],12:[[3,1]],13:[[2,1]],14:[[3,2]]};
function lerp01(a,b,v){return Math.abs(b-a)<0.001?0.5:Math.max(0,Math.min(1,(v-a)/(b-a)));}
function ept(e,r,c,cw,ch,tl,tr,bl,br,lv){
  var t=lerp01(tl,tr,lv),ri=lerp01(tr,br,lv),bt=lerp01(bl,br,lv),l=lerp01(tl,bl,lv);
  if(e===0)return[c*cw+t*cw,r*ch];
  if(e===1)return[(c+1)*cw,r*ch+ri*ch];
  if(e===2)return[c*cw+bt*cw,(r+1)*ch];
  if(e===3)return[c*cw,r*ch+l*ch];
}

// ─── 2D Contour render ─────────────────────────────────────────────
function renderContour(){
  var cv=document.getElementById('cv-contour');
  var vw=document.getElementById('views');
  cv.width=vw.clientWidth; cv.height=vw.clientHeight;
  var ctx=cv.getContext('2d'),W=cv.width,H=cv.height;
  var R=grid.length,C=grid[0].length;
  var cw=W/(C-1),ch=H/(R-1);
  // Filled elevation image
  var img=ctx.createImageData(W,H);
  for(var py=0;py<H;py++){
    for(var px=0;px<W;px++){
      var e=bilerp(grid,py/(H-1)*(R-1),px/(W-1)*(C-1));
      var t=(e-minE)/(maxE-minE||1);
      var col=elevRGB(t), i=(py*W+px)*4;
      img.data[i]=col[0];img.data[i+1]=col[1];img.data[i+2]=col[2];img.data[i+3]=255;
    }
  }
  ctx.putImageData(img,0,0);
  // Contour lines (12 levels)
  var nL=12;
  for(var li=1;li<nL;li++){
    var lv=minE+(maxE-minE)*li/nL;
    var t=(lv-minE)/(maxE-minE||1);
    var col=elevRGB(t);
    var isMaj=(li%3===0);
    ctx.strokeStyle='rgba('+(col[0]-50|0)+','+(col[1]-50|0)+','+(col[2]-50|0)+','+(isMaj?.85:.45)+')';
    ctx.lineWidth=isMaj?1.8:0.7;
    ctx.beginPath();
    for(var r=0;r<R-1;r++){
      for(var c=0;c<C-1;c++){
        var tl=grid[r][c],tr=grid[r][c+1],bl=grid[r+1][c],br=grid[r+1][c+1];
        var cn=(tl>=lv?8:0)|(tr>=lv?4:0)|(br>=lv?2:0)|(bl>=lv?1:0);
        var segs=MST[cn]; if(!segs)continue;
        for(var s=0;s<segs.length;s++){
          var p1=ept(segs[s][0],r,c,cw,ch,tl,tr,bl,br,lv);
          var p2=ept(segs[s][1],r,c,cw,ch,tl,tr,bl,br,lv);
          if(p1&&p2){ctx.moveTo(p1[0],p1[1]);ctx.lineTo(p2[0],p2[1]);}
        }
      }
    }
    ctx.stroke();
    // Altitude label on major contours
    if(isMaj){
      ctx.fillStyle='rgba(220,220,220,.7)';ctx.font='8px sans-serif';ctx.textAlign='left';
      ctx.fillText(Math.round(lv)+'m',4,H*(1-t)+10);
    }
  }
  // Peak marker
  var pr=0,pc=0,pe=grid[0][0];
  for(var r=0;r<R;r++)for(var c=0;c<C;c++)if(grid[r][c]>pe){pe=grid[r][c];pr=r;pc=c;}
  var px=pc/(C-1)*W,py=pr/(R-1)*H;
  ctx.fillStyle='#fff';ctx.font='bold 13px sans-serif';ctx.textAlign='center';
  ctx.fillText('△',px,py);
  ctx.font='9px sans-serif';ctx.fillStyle='#ccd';
  ctx.fillText(Math.round(pe)+'m',px,py+12);
  // Center cross
  ctx.strokeStyle='#ffffff44';ctx.lineWidth=1;ctx.setLineDash([4,4]);
  ctx.beginPath();ctx.moveTo(W/2,0);ctx.lineTo(W/2,H);
  ctx.moveTo(0,H/2);ctx.lineTo(W,H/2);ctx.stroke();
  ctx.setLineDash([]);
}

// ─── Elevation profile ─────────────────────────────────────────────
function renderProfile(){
  var cv=document.getElementById('cv-profile');
  var wr=document.getElementById('profile-wrap');
  cv.width=wr.clientWidth; cv.height=wr.clientHeight;
  var ctx=cv.getContext('2d'),W=cv.width,H=cv.height;
  var R=grid.length,C=grid[0].length;
  var midR=Math.floor(R/2);
  var pad={t:8,b:20,l:34,r:6};
  var iW=W-pad.l-pad.r,iH=H-pad.t-pad.b;
  ctx.fillStyle='#0d0d1a';ctx.fillRect(0,0,W,H);
  ctx.strokeStyle='#1e1e3a';ctx.lineWidth=1;
  for(var i=0;i<=4;i++){
    var y=pad.t+iH*(1-i/4);
    ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(pad.l+iW,y);ctx.stroke();
    ctx.fillStyle='#555';ctx.font='8px sans-serif';ctx.textAlign='right';
    ctx.fillText(Math.round(minE+(maxE-minE)*i/4)+'m',pad.l-2,y+3);
  }
  // Filled area
  ctx.beginPath();ctx.moveTo(pad.l,pad.t+iH);
  for(var c=0;c<C;c++){
    var x=pad.l+c/(C-1)*iW;
    var t=(grid[midR][c]-minE)/(maxE-minE||1);
    ctx.lineTo(x,pad.t+iH*(1-t));
  }
  ctx.lineTo(pad.l+iW,pad.t+iH);ctx.closePath();
  var gr=ctx.createLinearGradient(0,pad.t,0,pad.t+iH);
  gr.addColorStop(0,'rgba(78,204,163,.55)');gr.addColorStop(1,'rgba(78,204,163,.05)');
  ctx.fillStyle=gr;ctx.fill();
  // Line
  ctx.beginPath();
  for(var c=0;c<C;c++){
    var x=pad.l+c/(C-1)*iW;
    var t=(grid[midR][c]-minE)/(maxE-minE||1);
    var y=pad.t+iH*(1-t);
    c===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  }
  ctx.strokeStyle='#4ecca3';ctx.lineWidth=2;ctx.stroke();
  // Peak dot
  var mc=0,me=grid[midR][0];
  for(var c=1;c<C;c++)if(grid[midR][c]>me){me=grid[midR][c];mc=c;}
  var mpx=pad.l+mc/(C-1)*iW,mpy=pad.t+iH*(1-(me-minE)/(maxE-minE||1));
  ctx.fillStyle='#e94560';ctx.beginPath();ctx.arc(mpx,mpy,3,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#ccd';ctx.font='8px sans-serif';ctx.textAlign='center';
  ctx.fillText(Math.round(me)+'m',mpx,mpy-5);
  ctx.fillStyle='#555';ctx.textAlign='left';ctx.fillText('← 서(W)',pad.l,H-4);
  ctx.textAlign='right';ctx.fillText('동(E) →',pad.l+iW,H-4);
}

// ─── Three.js 3D terrain ──────────────────────────────────────────
function init3D(){
  var cv=document.getElementById('cv-3d');
  var vw=document.getElementById('views');
  cv.width=vw.clientWidth;cv.height=vw.clientHeight;
  if(rdr3){rdr3.dispose();cancelAnimationFrame(animId);rdr3=null;}
  rdr3=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:false});
  rdr3.setSize(cv.width,cv.height);
  rdr3.setClearColor(0x0d0d1a,1);
  scene3=new THREE.Scene();
  cam3=new THREE.PerspectiveCamera(50,cv.width/cv.height,0.1,500);
  var R=grid.length,C=grid[0].length;
  var geo=new THREE.PlaneGeometry(10,10,C-1,R-1);
  geo.rotateX(-Math.PI/2);
  var pos=geo.attributes.position,cols=[];
  for(var r=0;r<R;r++){
    for(var c=0;c<C;c++){
      var idx=r*C+c;
      var t=(grid[r][c]-minE)/(maxE-minE||1);
      pos.setY(idx,t*5);
      var col=elevRGB(t);
      cols.push(col[0]/255,col[1]/255,col[2]/255);
    }
  }
  geo.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));
  geo.computeVertexNormals();
  scene3.add(new THREE.Mesh(geo,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide})));
  var wmat=new THREE.LineBasicMaterial({color:0x4ecca3,opacity:.18,transparent:true});
  scene3.add(new THREE.LineSegments(new THREE.WireframeGeometry(geo),wmat));
  scene3.add(new THREE.AmbientLight(0xffffff,.55));
  var dl=new THREE.DirectionalLight(0xffffff,.9);dl.position.set(5,12,8);scene3.add(dl);
  var theta=0.5,phi=1.0,rr=22;
  function setcam(){cam3.position.set(rr*Math.sin(phi)*Math.sin(theta),rr*Math.cos(phi),rr*Math.sin(phi)*Math.cos(theta));cam3.lookAt(0,2,0);}
  setcam();
  var drag=false,lx=0,ly=0;
  cv.addEventListener('mousedown',function(e){drag=true;lx=e.clientX;ly=e.clientY;});
  window.addEventListener('mouseup',function(){drag=false;});
  window.addEventListener('mousemove',function(e){
    if(!drag)return;
    theta+=(e.clientX-lx)*.012;phi=Math.max(.1,Math.min(1.5,phi-(e.clientY-ly)*.012));
    lx=e.clientX;ly=e.clientY;setcam();
  });
  cv.addEventListener('wheel',function(e){rr=Math.max(8,Math.min(45,rr+e.deltaY*.04));setcam();e.preventDefault();},{passive:false});
  document.getElementById('tip3d').style.display='block';
  function animate(){animId=requestAnimationFrame(animate);rdr3.render(scene3,cam3);}
  animate();
}

// ─── Tab switch ────────────────────────────────────────────────────
function switchTab(t){
  activeTab=t;
  document.getElementById('cv-contour').style.display=t==='c'?'block':'none';
  document.getElementById('cv-3d').style.display=t==='3'?'block':'none';
  document.getElementById('tip3d').style.display=t==='3'?'block':'none';
  document.getElementById('tab-c').classList.toggle('active',t==='c');
  document.getElementById('tab-3').classList.toggle('active',t==='3');
  if(t==='3'&&grid)init3D();
}
document.getElementById('tip3d') && (document.getElementById('tip3d').style.display='none');

// ─── Bootstrap ────────────────────────────────────────────────────
fetch('/terrain-state').then(function(r){return r.json();}).then(function(d){
  if(!d||d.error)return;
  tLat=d.lat;tLon=d.lon;tName=d.name||'지형';tRadius=d.radius_km||15;tOcean=!!d.ocean;
  document.getElementById('tname').textContent=tName;
  document.getElementById('hcoord').textContent=tLat.toFixed(4)+'°N, '+tLon.toFixed(4)+'°E';
  map.setView([tLat,tLon],Math.round(13-Math.log2(tRadius/5)));
  if(mainMarker)map.removeLayer(mainMarker);
  mainMarker=L.marker([tLat,tLon]).addTo(map).bindPopup('<b>⛰️ '+tName+'</b>').openPopup();
  document.getElementById('load-sub').textContent='격자 20×20 = 400점 고도 조회 중...';
  return fetch('/elevation-grid?lat='+tLat+'&lon='+tLon+'&radius='+tRadius+'&steps=20&ocean='+(tOcean?'1':'0'));
}).then(function(r){return r&&r.json();}).then(function(g){
  if(!g||g.error){
    document.getElementById('loading').innerHTML='<p style="color:#e94560">⚠️ 고도 데이터 실패: '+(g&&g.error||'unknown')+'</p>';return;
  }
  grid=g.grid;minE=g.min_elev;maxE=g.max_elev;
  OCEAN_MODE=(minE<-50);
  CSTOPS=OCEAN_MODE?CSTOPS_OCEAN:CSTOPS_LAND;
  var elevLabel=OCEAN_MODE?'수심/고도 '+Math.round(minE)+'m ~ '+Math.round(maxE)+'m'
                           :'고도 '+Math.round(minE)+'m ~ '+Math.round(maxE)+'m';
  document.getElementById('helev').textContent=elevLabel;
  document.getElementById('leg0').textContent=Math.round(minE)+(minE<0?'m (심해)':'m');
  document.getElementById('leg1').textContent=Math.round(maxE)+(maxE>0?'m (육지/봉우리)':'m');
  document.getElementById('plabel').textContent=OCEAN_MODE?'📊 동서 단면도 (수심 프로파일)':'📊 동서 단면도 (고도 프로파일)';
  document.getElementById('loading').style.display='none';
  renderContour();
  renderProfile();
}).catch(function(e){
  document.getElementById('loading').innerHTML='<p style="color:#e94560">⚠️ '+e.message+'</p>';
});

window.addEventListener('resize',function(){
  if(!grid)return;
  if(activeTab==='c')renderContour();
  else if(activeTab==='3')init3D();
  renderProfile();
});
</script>
</body>
</html>"""


# ── 서버 ────────────────────────────────────────────────────────────────────
def fetch_elevation_grid(lat, lon, radius_km=15, steps=20, ocean=False):
    """Fetch steps×steps elevation grid.
    Uses ETOPO1 (covers land+ocean) when ocean=True, SRTM90m otherwise.
    """
    dataset = "etopo1" if ocean else "srtm90m"
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * math.cos(math.radians(lat)))
    pts = []
    for i in range(steps):
        for j in range(steps):
            pts.append((lat - dlat + 2*dlat*i/(steps-1),
                        lon - dlon + 2*dlon*j/(steps-1)))
    elevs = []
    for start in range(0, len(pts), 100):
        batch = pts[start:start+100]
        locs  = "|".join(f"{p[0]:.5f},{p[1]:.5f}" for p in batch)
        url   = f"https://api.opentopodata.org/v1/{dataset}?locations=" + locs
        req   = urllib.request.Request(url, headers={"User-Agent": "tour_skill/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
            for res in data.get("results", []):
                e = res.get("elevation")
                elevs.append(float(e) if e is not None else 0.0)
        except Exception:
            elevs.extend([0.0] * len(batch))
    grid = [[elevs[i*steps + j] for j in range(steps)] for i in range(steps)]
    return {
        "grid": grid, "lat": lat, "lon": lon,
        "radius_km": radius_km, "steps": steps,
        "min_elev": min(elevs),
        "max_elev": max(elevs),
        "ocean": ocean,
    }

def get_state():
    if not STATE_FILE.exists():
        return {"error": "탐방이 시작되지 않았습니다."}
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    idx = state.get("current_index", 0)
    stops = state.get("stops", [])
    if not stops or idx >= len(stops):
        return {"error": "정류장 정보 없음"}
    return {
        "current_index": idx,
        "total_stops":   state["total_stops"],
        "tour_name":     state["tour_name"],
        "tour_mode":     state.get("tour_mode", "tour"),
        "center_lat":    state.get("center_lat"),
        "center_lon":    state.get("center_lon"),
        "stop":          stops[idx],
    }

def cmd_serve(_args):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def send_json(self, data, status=200):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        def send_html(self, html):
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path   = parsed.path
            params = urllib.parse.parse_qs(parsed.query)
            def p(k, default, typ=str):
                return typ(params[k][0]) if k in params else default
            if path == "/state":
                self.send_json(get_state())
            elif path == "/terrain":
                self.send_html(TERRAIN_HTML)
            elif path == "/climate":
                self.send_html(CLIMATE_HTML)
            elif path == "/climate-map":
                self.send_html(CLIMATE_MAP_HTML)
            elif path == "/climate-state":
                self.send_json(get_climate_state())
            elif path == "/terrain-state":
                if TERRAIN_FILE.exists():
                    with open(TERRAIN_FILE, encoding="utf-8") as f:
                        self.send_json(json.load(f))
                else:
                    self.send_json({"error": "no terrain state"})
            elif path == "/elevation-grid":
                lat    = p("lat", 37.0, float)
                lon    = p("lon", 127.0, float)
                radius = p("radius", 15.0, float)
                steps  = p("steps", 20, int)
                ocean  = p("ocean", "0") in ("1","true","yes")
                try:
                    self.send_json(fetch_elevation_grid(lat, lon, radius, steps, ocean))
                except Exception as e:
                    self.send_json({"error": str(e)}, 500)
            else:
                self.send_html(NAVIGATOR_HTML)
        def do_POST(self):
            parsed2 = urllib.parse.urlparse(self.path)
            parts   = [p for p in parsed2.path.split("/") if p]
            # climate navigation
            if len(parts) == 2 and parts[0] == "climate-nav":
                action = parts[1]
                if not CLIMATE_STATE_FILE.exists():
                    self.send_response(404); self.end_headers(); return
                with open(CLIMATE_STATE_FILE, encoding="utf-8") as f:
                    cs = json.load(f)
                idx   = cs["current_index"]
                total = cs["total_stops"]
                if action == "next" and idx < total - 1: idx += 1
                elif action == "prev" and idx > 0:       idx -= 1
                cs["current_index"] = idx
                with open(CLIMATE_STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cs, f, ensure_ascii=False)
                self.send_json(get_climate_state())
                return
            # regular tour navigation
            action = parts[-1] if parts else ""
            if not STATE_FILE.exists():
                self.send_response(404); self.end_headers(); return
            with open(STATE_FILE, encoding="utf-8") as f:
                state = json.load(f)
            idx   = state["current_index"]
            total = state["total_stops"]
            if action == "next" and idx < total - 1: idx += 1
            elif action == "prev" and idx > 0:       idx -= 1
            state["current_index"] = idx
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
            self.send_json(get_state())
    socketserver.TCPServer.allow_reuse_address = True
    class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer): pass
    with ThreadedServer(("127.0.0.1", 8765), H) as srv:
        srv.serve_forever()


# ── 우리 동네 탐방 ────────────────────────────────────────────────────────────
def cmd_neighborhood(args):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    region = args.region
    if getattr(args, "data_file", None) and os.path.exists(args.data_file):
        with open(args.data_file, encoding="utf-8-sig") as f:
            data = json.load(f)
    else:
        data = json.loads(args.data)

    locations = data.get("locations", {})
    clat = args.center_lat
    clon = args.center_lon

    stops_raw = []
    for ftype, label in NEIGHBORHOOD_TYPES.items():
        for type_idx, loc in enumerate(locations.get(ftype, [])):
            lat_v = loc.get("lat", 0)
            lon_v = loc.get("lon", 0)
            name  = loc.get("name") or label
            dist  = haversine(clat, clon, lat_v, lon_v) if (clat and clon) else 0
            stops_raw.append((dist, ftype, label, name, lat_v, lon_v, loc, type_idx))

    stops_raw.sort(key=lambda x: x[0])
    if len(stops_raw) > 10:
        stops_raw = stops_raw[:10]

    stops = []
    for idx, (dist, ftype, label, name, lat_v, lon_v, loc, _) in enumerate(stops_raw, 1):
        edu = NEIGHBORHOOD_EDUCATION.get(ftype, {})
        stops.append({
            "index": idx, "name": name, "lat": lat_v, "lon": lon_v, "alt": 0,
            "facility_type":        ftype,
            "distance_km":          round(dist, 2),
            "historical_significance": edu.get("significance", ""),
            "observation_points":   list(edu.get("observation_points", [])),
            "student_questions":    list(edu.get("student_questions", [])),
            "student_answers":      list(edu.get("student_answers", [])),
            "photo_url":            loc.get("photo_url") or edu.get("photo_url", ""),
            "street_view_url":      f"https://www.google.com/maps/@{lat_v},{lon_v},3a,75y,0h,90t/data=!3m1!1e1",
        })

    state = {
        "tour_name":     f"{region} 우리 동네 탐방",
        "tour_mode":     "neighborhood",
        "center_lat":    clat, "center_lon": clon,
        "current_index": 0, "total_stops": len(stops),
        "created_at":    datetime.now().isoformat(),
        "stops":         stops,
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    out({"state_path": str(STATE_FILE), "stop_count": len(stops),
         "stops_summary": [{"index": s["index"], "name": s["name"],
                             "type": s["facility_type"], "distance_km": s["distance_km"]}
                            for s in stops]})


# ── 역사 탐방 ────────────────────────────────────────────────────────────────
def cmd_tour(args):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    event = args.event
    if getattr(args, "locations_file", None) and os.path.exists(args.locations_file):
        with open(args.locations_file, encoding="utf-8-sig") as f:
            stops = json.load(f)
    else:
        stops = json.loads(args.locations)

    if len(stops) > 10:
        stops = stops[:10]

    for i, s in enumerate(stops, 1):
        s.setdefault("index", i)
        s.setdefault("student_answers", [])

    state = {
        "tour_name":     f"{event} 역사 탐방",
        "tour_mode":     "tour",
        "current_index": 0, "total_stops": len(stops),
        "created_at":    datetime.now().isoformat(),
        "stops":         stops,
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    out({"state_path": str(STATE_FILE), "stop_count": len(stops),
         "stops_summary": [{"index": i+1, "name": s["name"]} for i, s in enumerate(stops)]})


# ── 탐방 네비게이션 ────────────────────────────────────────────────────────────
def cmd_tour_nav(args):
    if not STATE_FILE.exists():
        out({"error": "탐방이 시작되지 않았습니다. 먼저 탐방을 만들어 주세요."}); return
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    idx   = state["current_index"]
    total = state["total_stops"]

    def emit(warning=None):
        payload = {"current_index": idx, "stop": state["stops"][idx],
                   "is_first": idx == 0, "is_last": idx == total-1,
                   "total_stops": total, "tour_name": state["tour_name"]}
        if state.get("center_lat"): payload["center_lat"] = state["center_lat"]
        if state.get("center_lon"): payload["center_lon"] = state["center_lon"]
        if warning: payload["warning"] = warning
        out(payload)

    action = args.action
    if action == "start":
        idx = 0
    elif action == "next":
        if idx < total - 1: idx += 1
        else:
            state["current_index"] = idx
            with open(STATE_FILE, "w", encoding="utf-8") as f: json.dump(state, f, ensure_ascii=False)
            emit(f"마지막 정류장({total}번)입니다."); return
    elif action == "prev":
        if idx > 0: idx -= 1
        else:
            state["current_index"] = idx
            with open(STATE_FILE, "w", encoding="utf-8") as f: json.dump(state, f, ensure_ascii=False)
            emit("첫 번째 정류장입니다."); return

    state["current_index"] = idx
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    emit()


# ── 활동지 / 보고서 ───────────────────────────────────────────────────────────
# ── 기후지대 데이터 ────────────────────────────────────────────────────────────
CLIMATE_STOPS = {
  "desert": [
    {"name":"사하라 사막","country":"북아프리카 (알제리·리비아·차드)","lat":23.5,"lon":12.0,
     "climate_type":"desert","rainfall_mm":25,"temp_summer":50,"temp_winter":10,"temp_avg":30,
     "historical_significance":"세계 최대 열대 사막. 면적 920만 km²로 미국 본토와 맞먹는 크기입니다. 대부분이 암석 사막(하마다)이며 모래 사막(에르그)은 전체의 25%에 불과합니다.",
     "features":["극심한 일교차 — 낮 50°C, 밤 10°C","연 강수량 25mm 미만","모래폭풍(하르마탄)이 자주 발생","오아시스 주변에만 취락 형성"],
     "observation_points":["위성사진에서 모래 사막(노란색)과 암석 사막(갈색)의 차이를 찾아보세요","나일강 주변만 녹색인 이유를 생각해 보세요"],
     "student_questions":["사하라에 사는 사람들은 어떻게 물을 구할까요?","낮과 밤의 기온 차이가 큰 이유는 무엇일까요?"],
     "student_answers":["오아시스, 지하수, 나일강 등 수자원 근처에 거주하거나 유목 생활을 합니다.","모래는 열을 빠르게 흡수·방출하고 수분이 없어 기온 완충 작용이 없기 때문입니다."]},
    {"name":"아라비아 사막","country":"사우디아라비아·아랍에미리트","lat":23.6,"lon":46.7,
     "climate_type":"desert","rainfall_mm":80,"temp_summer":48,"temp_winter":15,"temp_avg":32,
     "historical_significance":"루브알할리(Rub' al Khali) — 세계 최대 연속 모래 사막을 포함합니다. 석유 자원이 풍부하여 두바이·리야드 같은 현대 도시가 발전했습니다.",
     "features":["루브알할리: 세계 최대 연속 모래 사막","석유·천연가스 매장량 세계 1위","연 강수량 80mm 미만","봄·가을 모래폭풍 발생"],
     "observation_points":["두바이·리야드 도시가 사막 속에 위치한 것을 확인해 보세요","관개 농업으로 녹화된 원형 경작지를 찾아보세요"],
     "student_questions":["사막 국가인데 두바이 같은 대도시가 발전할 수 있었던 이유는?","사막의 물 부족 문제는 어떻게 해결할 수 있을까요?"],
     "student_answers":["석유 수출로 얻은 부를 바탕으로 해수담수화 시설과 현대 인프라를 건설했습니다.","해수담수화, 태양에너지, 빗물 수집, 지하수 개발 등의 방법이 연구되고 있습니다."]},
    {"name":"고비 사막","country":"몽골·중국 북부","lat":42.0,"lon":103.0,
     "climate_type":"desert","rainfall_mm":190,"temp_summer":40,"temp_winter":-40,"temp_avg":5,
     "historical_significance":"아시아 최대 온대 사막. 여름 40°C, 겨울 -40°C의 극심한 기온 변화가 특징입니다. 공룡 화석 발굴지로도 유명합니다.",
     "features":["온대 사막 — 여름 40°C, 겨울 -40°C","연 강수량 190mm","공룡 화석 대량 출토","사막화 진행으로 한국 황사 발원지"],
     "observation_points":["몽골 초원과 고비 사막의 경계선을 위성사진에서 찾아보세요","황사의 발원지임을 고려해 한국과의 거리를 확인해 보세요"],
     "student_questions":["고비 사막은 왜 여름과 겨울의 기온 차이가 그렇게 클까요?","고비 사막이 한국의 황사와 어떤 관련이 있을까요?"],
     "student_answers":["바다에서 멀리 떨어진 대륙 내부에 위치해 해양의 기온 완충 효과를 받지 못하기 때문입니다.","고비의 모래와 먼지가 편서풍을 타고 한반도까지 날아와 황사를 일으킵니다."]},
    {"name":"아타카마 사막","country":"칠레·페루","lat":-24.0,"lon":-69.0,
     "climate_type":"desert","rainfall_mm":1,"temp_summer":25,"temp_winter":0,"temp_avg":15,
     "historical_significance":"세계에서 가장 건조한 사막. 일부 지역은 400년 이상 비가 내리지 않았습니다. 해발 4,000m 이상 고지 사막이며 세계 최대 천문대들이 위치합니다.",
     "features":["세계 최건조 (연 강수량 1mm 미만)","400년 이상 무강수 기록 존재","해발 4,000m 이상 고지 사막","세계 최대 구리 광산·천문대 집중"],
     "observation_points":["안데스 산맥과 사막의 경계를 확인해 보세요","위성사진에서 원형 구리 광산 채굴 구덩이를 찾아보세요"],
     "student_questions":["아타카마가 세계에서 가장 건조한 이유는 무엇일까요?","아타카마에 왜 세계 최대 천문대들이 모여 있을까요?"],
     "student_answers":["태평양 한류(훔볼트 해류)로 증발이 적고, 안데스 산맥이 습기를 차단하며, 고기압 지배로 강수가 매우 적습니다.","구름이 없어 1년 300일 이상 맑은 하늘이 유지되어 천체 관측 조건이 세계 최고입니다."]},
    {"name":"오스트레일리아 내륙 (아웃백)","country":"오스트레일리아","lat":-25.0,"lon":134.0,
     "climate_type":"desert","rainfall_mm":250,"temp_summer":50,"temp_winter":5,"temp_avg":25,
     "historical_significance":"오스트레일리아 대륙의 약 70%가 건조·반건조 기후입니다. 울루루(에어즈 록)와 독특한 생태계, 원주민 아보리진의 삶의 터전입니다.",
     "features":["연 강수량 250mm 미만","울루루 (세계 최대 단일 암석) 위치","원주민 아보리진 전통 문화 지역","캥거루·코알라 등 독특한 생태계"],
     "observation_points":["울루루(에어즈 록)를 위성사진에서 찾아보세요 (붉은 거대 암석)","강수량이 적은데도 간헐하천 흔적이 보이는 이유를 생각해 보세요"],
     "student_questions":["아웃백의 원주민 아보리진은 어떻게 극한 환경에서 살아왔을까요?","오스트레일리아 동물들이 다른 대륙과 다른 이유는?"],
     "student_answers":["오랫동안 전해 내려온 지식으로 땅속 수분, 식물 뿌리, 동물의 이동 경로를 파악해 생존했습니다.","수천만 년 전 다른 대륙과 분리되어 독자적으로 진화했기 때문입니다."]},
    {"name":"타클라마칸 사막","country":"중국 신장 위구르","lat":38.5,"lon":82.0,
     "climate_type":"desert","rainfall_mm":10,"temp_summer":38,"temp_winter":-20,"temp_avg":12,
     "historical_significance":"'한번 들어가면 나올 수 없는 곳'이라는 뜻의 위구르어 지명. 사방이 산으로 둘러싸인 분지 사막으로 실크로드의 주요 통로였습니다.",
     "features":["연 강수량 10mm 미만","사방이 산으로 둘러싸인 분지","실크로드 오아시스 도시들","모래 폭풍으로 시야 수시로 차단"],
     "observation_points":["카슈가르·호탄 오아시스 도시를 위성사진에서 찾아보세요","텐산·쿤룬 산맥에 둘러싸인 지형을 확인해 보세요"],
     "student_questions":["실크로드가 타클라마칸 주변부를 통과한 이유는 무엇일까요?","오아시스 도시가 발달한 이유는 무엇인가요?"],
     "student_answers":["사막 한가운데는 너무 위험해 상인들이 오아시스를 따라 사막 가장자리로 돌아다녔습니다.","산에서 내려오는 물이 모이는 곳에 농업이 가능해 자연스럽게 도시가 형성되었습니다."]},
  ],
  "cold": [
    {"name":"오이먀콘 (시베리아)","country":"러시아 사하공화국","lat":63.46,"lon":142.77,
     "climate_type":"cold","rainfall_mm":210,"temp_summer":30,"temp_winter":-68,"temp_avg":-15,
     "historical_significance":"사람이 사는 곳 중 지구에서 가장 추운 마을. 1924년 -71.2°C를 기록한 '북반구의 추위 극점'입니다. 약 500명의 주민이 실제로 생활합니다.",
     "features":["최저 기온 -71.2°C 기록 (1924)","연평균 기온 -15°C","영구동토층(퍼마프로스트) 지역","사람이 거주하는 세계 최한지"],
     "observation_points":["오이먀콘 마을 주변 침엽수림(타이가)을 위성사진에서 확인해 보세요","강이 완전히 얼어 하얗게 보이는 모습을 찾아보세요"],
     "student_questions":["오이먀콘 사람들은 -68°C의 혹한에서 어떻게 생활할까요?","영구동토층이란 무엇이며, 기후변화와 어떤 관련이 있을까요?"],
     "student_answers":["순록 유목, 낚시, 사냥으로 생활하며 집을 두껍게 짓고 자동차도 24시간 시동을 켜둔 채 생활합니다.","1년 내내 얼어있는 땅으로, 기후변화로 녹으면 지반 침하와 온실가스 방출이 심각해집니다."]},
    {"name":"알래스카","country":"미국 알래스카 주","lat":64.2,"lon":-153.0,
     "climate_type":"cold","rainfall_mm":350,"temp_summer":20,"temp_winter":-35,"temp_avg":-5,
     "historical_significance":"북극에 인접한 미국 최대의 주. 툰드라, 빙하, 오로라로 유명합니다. 덴날리(맥킨리, 6,190m)는 북미 최고봉입니다.",
     "features":["여름 22시간 백야, 겨울 극야","오로라(북극광) 관측 최적지","빙하·툰드라·타이가 다양한 생태계","북극곰·순록·연어 등 풍부한 야생동물"],
     "observation_points":["덴날리(맥킨리) 봉우리를 위성사진에서 찾아보세요","알래스카를 가로지르는 파이프라인 경로를 확인해 보세요"],
     "student_questions":["알래스카에서 여름에 밤이 없는 백야가 생기는 이유는?","원주민 이누이트는 어떻게 극한 추위에 적응했을까요?"],
     "student_answers":["지구 자전축이 기울어진 채 공전하므로 고위도에서는 여름에 태양이 지지 않는 백야가 나타납니다.","이글루(눈집), 카약, 두꺼운 동물 가죽 옷, 지방 위주의 식단으로 극한 환경에 적응했습니다."]},
    {"name":"캐나다 북부 (누나부트)","country":"캐나다","lat":63.0,"lon":-96.0,
     "climate_type":"cold","rainfall_mm":200,"temp_summer":12,"temp_winter":-40,"temp_avg":-10,
     "historical_significance":"캐나다 국토의 약 50%가 북방 한랭 지대입니다. 누나부트 준주는 이누이트가 자치를 이루는 지역으로 면적이 한국의 20배에 달합니다.",
     "features":["이누이트 자치 지역 (누나부트)","툰드라 + 영구동토층","허드슨 만 연간 결빙","북극곰 집단 서식지 처칠 위치"],
     "observation_points":["허드슨 만이 겨울에 결빙되는 모습을 계절 위성사진으로 비교해 보세요","도로가 거의 없는 이유를 지형과 기후로 설명해 보세요"],
     "student_questions":["누나부트처럼 넓은 땅인데 인구가 매우 적은 이유는 무엇일까요?","기후변화로 북극 얼음이 녹으면 어떤 변화가 생길까요?"],
     "student_answers":["혹독한 추위, 짧은 여름, 빈약한 농업 환경으로 인해 인간이 살기 매우 어렵기 때문입니다.","북극항로가 열려 물류 혁명이 일어나고, 자원 개발이 쉬워지지만 생태계 파괴도 심각해집니다."]},
    {"name":"스칸디나비아 북부 (라플란드)","country":"노르웨이·스웨덴·핀란드","lat":69.0,"lon":20.0,
     "climate_type":"cold","rainfall_mm":450,"temp_summer":18,"temp_winter":-25,"temp_avg":0,
     "historical_significance":"유럽의 극지 지역. 순록 유목 민족 사미인의 고향이며 오로라 관측의 성지입니다. 여름 백야, 겨울 극야가 나타납니다.",
     "features":["사미족 순록 유목 문화","여름 백야 · 겨울 극야","오로라 관측의 성지","피오르 지형 발달 (노르웨이)"],
     "observation_points":["피오르 해안선의 복잡한 모양을 위성사진에서 찾아보세요","침엽수림(타이가)이 끝나고 툰드라가 시작되는 경계를 확인해 보세요"],
     "student_questions":["사미족은 왜 한곳에 정착하지 않고 순록을 따라 이동 생활을 할까요?","피오르는 어떻게 만들어졌을까요?"],
     "student_answers":["순록은 계절마다 다른 목초지를 찾아 이동하므로 사미족도 순록을 따라 계절 이동 생활을 합니다.","빙하기에 빙하가 골짜기를 깎아내고, 빙하가 녹은 후 바닷물이 들어와 형성된 좁고 깊은 만입니다."]},
    {"name":"그린란드","country":"덴마크 자치령","lat":72.0,"lon":-40.0,
     "climate_type":"cold","rainfall_mm":300,"temp_summer":8,"temp_winter":-50,"temp_avg":-20,
     "historical_significance":"세계 최대의 섬. 면적의 80% 이상이 두께 최대 3km의 빙상으로 덮여 있습니다. 빙상이 모두 녹으면 해수면이 7m 상승합니다.",
     "features":["세계 최대 섬 (면적 216만 km²)","빙상 두께 최대 3,000m","인구 약 56,000명 (연안 소수 거주)","기후변화로 빙상 급격히 감소 중"],
     "observation_points":["빙상(흰색)과 노출된 암석(갈색)의 경계를 위성사진에서 찾아보세요","연안부에만 취락이 형성된 이유를 생각해 보세요"],
     "student_questions":["그린란드 이름이 '초록의 땅'인데 왜 대부분이 얼음으로 덮여 있을까요?","그린란드 빙상이 녹으면 우리나라에 어떤 영향을 미칠까요?"],
     "student_answers":["10세기 바이킹 탐험가 에릭이 이민을 유도하기 위해 '초록의 땅'이라 이름 붙였다는 설이 있습니다.","해수면이 최대 7m 상승해 우리나라 서해안·남해안 저지대와 제주도 일부가 침수될 수 있습니다."]},
    {"name":"남극 대륙","country":"국제 조약 지역 (남극조약)","lat":-80.0,"lon":0.0,
     "climate_type":"cold","rainfall_mm":50,"temp_summer":-25,"temp_winter":-89,"temp_avg":-49,
     "historical_significance":"지구 최남단 대륙. 최저 기온 -89.2°C(세계 기록). 연평균 -49°C로 지구에서 가장 추운 곳입니다. 지구 담수의 70%가 이곳 빙상에 저장되어 있습니다.",
     "features":["최저 기온 -89.2°C 기록","담수의 70%가 남극 빙상에 보존","1년 중 6개월 극야·6개월 백야","연구 목적 외 거주 금지 (남극조약)"],
     "observation_points":["남극 대륙의 실제 모양을 위성사진으로 확인하고 지도의 왜곡과 비교해 보세요","여름(12~2월)과 겨울 해빙 범위를 비교해 보세요"],
     "student_questions":["남극이 북극보다 더 추운 이유는 무엇일까요?","남극조약은 왜 만들어졌고 어떤 내용을 담고 있을까요?"],
     "student_answers":["남극은 두꺼운 빙상 위의 고원(해발 2,300m)으로, 고도가 높고 바다와 격리되어 있어 북극보다 훨씬 춥습니다.","1961년 체결. 군사 활동 금지, 과학 연구 보장, 영토 주장 동결을 담고 있습니다."]},
  ]
}


# ── 기후 탐방 HTML ─────────────────────────────────────────────────────────────
CLIMATE_HTML = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>기후지대 탐방</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d1a;color:#ccd;font-family:'Segoe UI',sans-serif;display:flex;flex-direction:column;height:100vh;overflow:hidden}
#hdr{background:#12122a;padding:6px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid #2a2a50;flex-shrink:0;flex-wrap:wrap}
#hdr h1{font-size:.93em}
.badge{padding:2px 10px;border-radius:12px;font-size:.76em;font-weight:bold;border:1px solid currentColor}
.bd{color:#ff8c00;border-color:#ff8c00}.bc{color:#4fc3f7;border-color:#4fc3f7}
#prog{font-size:.76em;color:#888;margin-left:auto}
#body{display:flex;flex:1;overflow:hidden}
#panel{width:45%;display:flex;flex-direction:column;border-right:1px solid #2a2a50;min-width:260px}
#scroll{flex:1;overflow-y:auto;padding:10px 14px}
#sname{font-size:1.1em;font-weight:bold;margin-bottom:1px}
#country-lbl{font-size:.76em;color:#888;margin-bottom:8px}
#stats{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:10px}
.sbox{background:#12122a;border:1px solid #2a2a50;border-radius:5px;padding:7px 9px}
.slbl{font-size:.65em;letter-spacing:.07em;text-transform:uppercase;color:#666;margin-bottom:5px}
#temp-track{position:relative;height:11px;border-radius:4px;margin-bottom:12px;
  background:linear-gradient(to right,#0d47a1,#1565c0,#0288d1,#00acc1,#43a047,#c0ca33,#f57c00,#d32f2f)}
.tm{position:absolute;top:-15px;font-size:.6em;transform:translateX(-50%);white-space:nowrap}
.td{position:absolute;width:10px;height:10px;border-radius:50%;top:1px;transform:translateX(-50%);border:2px solid #0d0d1a}
#tvals{font-size:.68em;color:#aaa;margin-top:2px;line-height:1.5}
#rain-row{display:flex;align-items:center;gap:6px;margin-bottom:3px}
#rain-bg{flex:1;height:10px;background:#1a1a2e;border-radius:4px;overflow:hidden}
#rain-fill{height:100%;border-radius:4px;background:linear-gradient(to right,#64b5f6,#1565c0)}
#rain-n{font-size:.82em;font-weight:bold;color:#64b5f6}
#rain-tag{font-size:.65em;color:#888}
#sv-row{display:flex;gap:6px;margin-top:8px;flex-shrink:0}
.sv-lnk{flex:1;background:none;border:1px solid #4ecca3;color:#4ecca3;border-radius:4px;padding:4px 0;cursor:pointer;font-size:.78em;text-align:center}
.sv-lnk:hover{background:#4ecca322}
.sv-lnk.map-btn{border-color:#888;color:#888}
.sec-lbl{font-size:.65em;letter-spacing:.07em;text-transform:uppercase;color:#666;margin:8px 0 4px}
.sig-txt{font-size:.8em;color:#aab;line-height:1.55;margin-bottom:4px}
.feat-ul{list-style:none;padding:0;margin-bottom:4px}
.feat-ul li{font-size:.78em;color:#ccd;padding:1px 0 1px 11px;position:relative}
.feat-ul li::before{content:'·';position:absolute;left:2px;color:#4ecca3}
.obs-ul{list-style:none;padding:0;margin-bottom:4px}
.obs-ul li{font-size:.78em;color:#bbc;padding:2px 0}
.qs-ul{list-style:none;padding:0}
.qs-ul li{margin-bottom:7px}
.qa-q{display:block;font-size:.8em;color:#ccd}
.ans-btn{background:none;border:1px solid #4ecca366;color:#4ecca3;border-radius:4px;
  padding:2px 7px;cursor:pointer;font-size:.72em;margin-top:3px}
.ans-btn:hover{background:#4ecca322}
.qa-a{display:none;font-size:.78em;color:#4ecca3;border-left:2px solid #4ecca344;padding-left:7px;margin-top:4px}
#nav-btns{display:flex;gap:7px;padding:7px 12px 9px;flex-shrink:0;border-top:1px solid #2a2a50}
.nb{flex:1;padding:7px 0;border:none;border-radius:5px;font-size:.9em;font-weight:bold;cursor:pointer}
#btn-prev{background:#252540;color:#4ecca3;border:1px solid #4ecca3}
#btn-next{background:#4ecca3;color:#0d0d1a}
#btn-prev:disabled,#btn-next:disabled{opacity:.3;cursor:default}
#mapwrap{flex:1;position:relative}
#mapframe{width:100%;height:100%}
</style>
</head>
<body>
<div id="hdr">
  <h1>🌍 기후지대 탐방</h1>
  <span id="zone-badge" class="badge"></span>
  <span id="prog"></span>
</div>
<div id="body">
  <div id="panel">
    <div id="scroll">
      <div id="sname"></div>
      <div id="country-lbl"></div>
      <div id="stats">
        <div class="sbox">
          <div class="slbl">🌡️ 기온</div>
          <div id="temp-track"></div>
          <div id="tvals"></div>
        </div>
        <div class="sbox">
          <div class="slbl">🌧️ 연 강수량</div>
          <div id="rain-row"><div id="rain-bg"><div id="rain-fill"></div></div><span id="rain-n"></span></div>
          <div id="rain-tag"></div>
        </div>
      </div>
      <div class="sec-lbl">📋 지역 소개</div>
      <div class="sig-txt" id="sig"></div>
      <div class="sec-lbl">✅ 주요 특징</div>
      <ul class="feat-ul" id="feat-ul"></ul>
      <div class="sec-lbl">👁️ 관찰 포인트</div>
      <ul class="obs-ul" id="obs-ul"></ul>
      <div id="sv-row">
        <button class="sv-lnk" id="sv-btn" onclick="openSV()">🔍 스트리트뷰</button>
        <button class="sv-lnk map-btn" id="map-btn" onclick="openMap()">🛰️ 구글지도 보기</button>
      </div>
      <div class="sec-lbl">❓ 탐구 질문</div>
      <ul class="qs-ul" id="qs-ul"></ul>
    </div>
    <div id="nav-btns">
      <button class="nb" id="btn-prev" onclick="navClick('prev')">◀ 이전</button>
      <button class="nb" id="btn-next" onclick="navClick('next')">다음 ▶</button>
    </div>
  </div>
  <div id="mapwrap"><div id="mapframe"></div></div>
</div>
<script>
var map=L.map('mapframe',{
  zoomControl:true,
  attributionControl:false,
  scrollWheelZoom:'center',
  bounceAtZoomLimits:false
}).setView([30,30],3);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:20}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:20,opacity:.7}).addTo(map);
var mk=null,curIdx=null;

function showAns(btn){btn.style.display='none';var a=btn.parentElement.querySelector('.qa-a');if(a)a.style.display='block';}

function drawTemp(tw,ta,ts){
  var el=document.getElementById('temp-track');el.innerHTML='';
  var lo=-70,hi=50,rng=hi-lo;
  function pct(t){return Math.max(0,Math.min(100,(t-lo)/rng*100))+'%';}
  [[tw,'#64b5f6'],[ta,'#ffffff'],[ts,'#ef5350']].forEach(function(p){
    var dot=document.createElement('div');dot.className='td';dot.style.left=pct(p[0]);dot.style.background=p[1];
    var lbl=document.createElement('div');lbl.className='tm';lbl.style.left=pct(p[0]);lbl.style.color=p[1];lbl.textContent=p[0]+'°';
    el.appendChild(lbl);el.appendChild(dot);
  });
  document.getElementById('tvals').innerHTML='겨울 <b style="color:#64b5f6">'+tw+'°C</b> &nbsp;/&nbsp; 연평균 <b>'+ta+'°C</b> &nbsp;/&nbsp; 여름 <b style="color:#ef5350">'+ts+'°C</b>';
}

function drawRain(mm){
  document.getElementById('rain-fill').style.width=Math.min(100,mm/2000*100)+'%';
  document.getElementById('rain-n').textContent=mm+'mm';
  var tag=mm<50?'극건조':mm<250?'건조':mm<500?'반건조':mm<1000?'보통':'습윤';
  document.getElementById('rain-tag').textContent=tag+' (세계평균 990mm)';
}

function applyState(d){
  if(!d||d.error)return;
  var s=d.stop;if(!s)return;
  var stopChanged=(d.current_index!==curIdx);
  var isD=(s.climate_type==='desert');
  var badge=document.getElementById('zone-badge');
  badge.textContent=isD?'🏜️ 건조지대':'🏔️ 한랭지대';
  badge.className='badge '+(isD?'bd':'bc');
  document.getElementById('prog').textContent=(d.current_index+1)+' / '+d.total_stops;
  document.getElementById('sname').textContent=s.name||'';
  document.getElementById('sname').style.color=isD?'#ff8c00':'#4fc3f7';
  document.getElementById('country-lbl').textContent=s.country||'';
  drawTemp(s.temp_winter,s.temp_avg,s.temp_summer);
  drawRain(s.rainfall_mm);
  document.getElementById('sig').textContent=s.historical_significance||'';
  var fu=document.getElementById('feat-ul');fu.innerHTML='';
  (s.features||[]).forEach(function(f){var li=document.createElement('li');li.textContent=f;fu.appendChild(li);});
  var ou=document.getElementById('obs-ul');ou.innerHTML='';
  (s.observation_points||[]).forEach(function(o){var li=document.createElement('li');li.textContent='· '+o;ou.appendChild(li);});
  if(stopChanged){
    curIdx=d.current_index;
    var qs=s.student_questions||[],qa=s.student_answers||[];
    var qu=document.getElementById('qs-ul');qu.innerHTML='';
    qs.forEach(function(q,i){
      var li=document.createElement('li');
      var h='<span class="qa-q">'+(i+1)+'. '+q+'</span>';
      if(qa[i])h+='<br><button class="ans-btn" onclick="showAns(this)">💡 정답 보기</button><span class="qa-a">💡 '+qa[i]+'</span>';
      li.innerHTML=h;qu.appendChild(li);
    });
  }
  document.getElementById('btn-prev').disabled=(d.current_index===0);
  document.getElementById('btn-next').disabled=(d.current_index===d.total_stops-1);
  if(s.lat&&s.lon){
    curSvLat=s.lat;curSvLon=s.lon;
    if(stopChanged){
      map.setView([s.lat,s.lon],5);
      if(mk)map.removeLayer(mk);
      mk=L.marker([s.lat,s.lon]).addTo(map)
        .bindPopup('<b>'+(isD?'🏜️':'🏔️')+' '+s.name+'</b><br>강수량 '+s.rainfall_mm+'mm/년<br>기온 '+s.temp_winter+'~'+s.temp_summer+'°C').openPopup();
    }
  }
}

var curSvLat=0,curSvLon=0;
function openSV(){if(curSvLat)window.open('https://www.google.com/maps/@'+curSvLat+','+curSvLon+',3a,75y,0h,90t/data=!3m1!1e1','_blank')}
function openMap(){if(curSvLat)window.open('https://www.google.com/maps/search/?api=1&query='+curSvLat+','+curSvLon,'_blank')}
function navClick(action){
  var btn=document.getElementById(action==='next'?'btn-next':'btn-prev');
  btn.disabled=true;
  fetch('/climate-nav/'+action,{method:'POST'}).then(function(r){return r.json();})
    .then(applyState).catch(function(){}).finally(function(){btn.disabled=false;});
}

function upd(){fetch('/climate-state').then(function(r){return r.json();}).then(applyState).catch(function(){});}
upd();setInterval(upd,600);
</script>
</body>
</html>"""


# ── 기후 비교 지도 HTML ────────────────────────────────────────────────────────
CLIMATE_MAP_HTML = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>기후지대 비교 지도</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d1a;display:flex;flex-direction:column;height:100vh;font-family:'Segoe UI',sans-serif;color:#ccd}
#hdr{background:#12122a;padding:7px 14px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #2a2a50;flex-shrink:0}
#hdr h1{font-size:.95em;color:#4ecca3}
#hdr p{font-size:.76em;color:#888}
#mapwrap{flex:1;position:relative}
#mapframe{width:100%;height:100%}
#legend{position:absolute;bottom:18px;left:12px;z-index:500;background:#12122add;
  border:1px solid #2a2a50;border-radius:8px;padding:10px 14px;font-size:.76em;backdrop-filter:blur(4px)}
#legend h3{font-size:.82em;color:#4ecca3;margin-bottom:8px}
.lr{display:flex;align-items:center;gap:8px;margin-bottom:5px}
.ls{width:22px;height:13px;border-radius:3px;border:1px solid rgba(255,255,255,.25);flex-shrink:0}
#latinfo{position:absolute;top:10px;right:12px;z-index:500;background:#12122add;
  border:1px solid #2a2a50;border-radius:6px;padding:8px 12px;font-size:.72em;
  backdrop-filter:blur(4px);line-height:1.8}
</style>
</head>
<body>
<div id="hdr">
  <h1>🌍 한랭지대 · 건조지대 비교 지도</h1>
  <p>위도·경도 굵은선 표시 | 영역별 색상 구분 | 마우스 올리면 지역명</p>
</div>
<div id="mapwrap">
  <div id="mapframe"></div>
  <div id="legend">
    <h3>범례</h3>
    <div class="lr"><div class="ls" style="background:rgba(255,140,0,.45)"></div>🏜️ 건조지대 (연강수 &lt;250mm)</div>
    <div class="lr"><div class="ls" style="background:rgba(30,120,220,.45)"></div>🏔️ 한랭지대 (연평균 &lt;0°C)</div>
    <div class="lr"><div class="ls" style="height:3px;border:none;background:#FFD700"></div>━ 적도·회귀선·극권</div>
    <div class="lr"><div class="ls" style="height:1px;border:none;background:#ffffff55"></div>━ 30° 위·경도선</div>
  </div>
  <div id="latinfo">
    <span style="color:#FFD700">━━</span> 적도 0° &nbsp;|&nbsp;
    <span style="color:#ff8c00">━━</span> 북·남회귀선 ±23.5°<br>
    <span style="color:#4fc3f7">━━</span> 북·남극권 ±66.5° &nbsp;|&nbsp;
    <span style="color:#ffffff44">━━</span> 30° 격자선
  </div>
</div>
<script>
var worldBounds=[[-85,-180],[85,180]];
var map=L.map('mapframe',{
  zoomControl:true,
  attributionControl:false,
  minZoom:2,
  maxZoom:18,
  maxBounds:worldBounds,
  maxBoundsViscosity:1,
  worldCopyJump:false,
  scrollWheelZoom:'center',
  bounceAtZoomLimits:false
}).setView([20,10],2);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,noWrap:true,bounds:worldBounds}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,opacity:.45,noWrap:true,bounds:worldBounds}).addTo(map);

// ── 위·경도 격자선 ─────────────────────────────────────────────────
var gs={color:'#ffffff',weight:1,opacity:.2,dashArray:'4,8'};
for(var lo=-180;lo<=180;lo+=30) L.polyline([[-90,lo],[90,lo]],gs).addTo(map);
[-60,-30,30,60].forEach(function(la){L.polyline([[la,-180],[la,180]],gs).addTo(map);});

// 주요 위도선 (굵게)
L.polyline([[0,-180],[0,180]],{color:'#FFD700',weight:4,opacity:.9}).addTo(map)
  .bindTooltip('적도 (0°)',{permanent:false,direction:'right'});
[[23.5,'#ff8c00','북회귀선 23.5°N'],[-23.5,'#ff8c00','남회귀선 23.5°S'],
 [66.5,'#4fc3f7','북극권 66.5°N'],[-66.5,'#4fc3f7','남극권 66.5°S']].forEach(function(r){
  L.polyline([[r[0],-180],[r[0],180]],{color:r[1],weight:3,opacity:.85,dashArray:'10,5'})
    .addTo(map).bindTooltip(r[2],{permanent:false,direction:'right'});
});

// ── 건조지대 영역 (주황) ───────────────────────────────────────────
var DS={stroke:true,color:'#bf360c',weight:2,fill:true,fillColor:'#ff8c00',fillOpacity:.45};
[['사하라 사막',[[15,-17],[35,55]]],
 ['아라비아 사막',[[15,35],[30,62]]],
 ['이란·중앙아 사막',[[25,55],[45,78]]],
 ['고비 사막',[[38,88],[50,120]]],
 ['타클라마칸 사막',[[36,74],[43,90]]],
 ['오스트레일리아 내륙',[[-35,113],[-17,140]]],
 ['아타카마 사막',[[-30,-73],[-15,-65]]],
 ['파타고니아 사막',[[-55,-72],[-38,-65]]],
 ['나미브·칼라하리',[[-32,12],[-18,28]]],
 ['소노란·치와와 사막',[[25,-117],[35,-105]]],
].forEach(function(d){
  L.rectangle(d[1],DS).addTo(map).bindTooltip('🏜️ '+d[0],{sticky:true});
});

// ── 한랭지대 영역 (파랑) ───────────────────────────────────────────
var CS={stroke:true,color:'#0d47a1',weight:2,fill:true,fillColor:'#29b6f6',fillOpacity:.45};
[['북부 시베리아',[[65,55],[75,180]]],
 ['시베리아 중부',[[55,55],[65,160]]],
 ['캐나다 북부',[[58,-142],[75,-60]]],
 ['알래스카',[[58,-168],[72,-140]]],
 ['그린란드',[[60,-55],[85,-14]]],
 ['스칸디나비아 북부',[[65,10],[72,32]]],
 ['아이슬란드',[[63,-25],[68,-12]]],
 ['남극 대륙',[[-90,-180],[-65,180]]],
].forEach(function(d){
  L.rectangle(d[1],CS).addTo(map).bindTooltip('🏔️ '+d[0],{sticky:true});
});

// ── 지역 라벨 ─────────────────────────────────────────────────────
function lbl(lat,lon,text,color){
  L.marker([lat,lon],{icon:L.divIcon({className:'',
    html:'<div style="color:'+color+';font-size:.7em;font-weight:bold;white-space:nowrap;text-shadow:0 0 5px #000,0 0 10px #000;pointer-events:none">'+text+'</div>',
    iconSize:[140,20],iconAnchor:[70,10]})}).addTo(map);
}
lbl(25,12,'🏜️ 사하라','#ffb74d'); lbl(24,47,'🏜️ 아라비아','#ffb74d');
lbl(43,100,'🏜️ 고비','#ffb74d'); lbl(-25,128,'🏜️ 아웃백','#ffb74d');
lbl(-22,-69,'🏜️ 아타카마','#ffb74d'); lbl(38,81,'🏜️ 타클라마칸','#ffb74d');
lbl(67,110,'🏔️ 시베리아','#81d4fa'); lbl(65,-100,'🏔️ 캐나다 북부','#81d4fa');
lbl(65,-18,'🏔️ 아이슬란드','#81d4fa'); lbl(74,-38,'🏔️ 그린란드','#81d4fa');
lbl(-82,0,'🏔️ 남극','#81d4fa');
</script>
</body>
</html>"""


def get_climate_state():
    if not CLIMATE_STATE_FILE.exists():
        return {"error": "기후 탐방이 시작되지 않았습니다."}
    with open(CLIMATE_STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    idx   = state.get("current_index", 0)
    stops = state.get("stops", [])
    if not stops or idx >= len(stops):
        return {"error": "정류장 정보 없음"}
    return {"current_index": idx, "total_stops": state["total_stops"],
            "zone": state.get("zone",""), "stop": stops[idx]}


def cmd_climate(args):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    zone  = args.zone
    stops_raw = CLIMATE_STOPS.get(zone, [])
    stops = []
    for i, s in enumerate(stops_raw, 1):
        stops.append({
            "index": i,
            "name":  s["name"], "country": s["country"],
            "lat":   s["lat"],  "lon": s["lon"],
            "climate_type": s["climate_type"],
            "rainfall_mm":  s["rainfall_mm"],
            "temp_summer":  s["temp_summer"],
            "temp_winter":  s["temp_winter"],
            "temp_avg":     s["temp_avg"],
            "historical_significance": s["historical_significance"],
            "features":          s.get("features", []),
            "observation_points":s.get("observation_points", []),
            "student_questions": s.get("student_questions", []),
            "student_answers":   s.get("student_answers", []),
        })
    state = {"zone": zone, "current_index": 0,
             "total_stops": len(stops), "stops": stops}
    with open(CLIMATE_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    out({"status": "ok", "zone": zone, "total_stops": len(stops),
         "url": "http://localhost:8765/climate"})


def cmd_climate_map(_args):
    out({"status": "ok", "url": "http://localhost:8765/climate-map"})


def cmd_terrain(args):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ocean = getattr(args, "ocean", False)
    state = {
        "name":      args.name,
        "lat":       args.lat,
        "lon":       args.lon,
        "radius_km": args.radius,
        "ocean":     ocean,
    }
    with open(TERRAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    out({"status": "ok", "name": args.name, "lat": args.lat, "lon": args.lon,
         "radius_km": args.radius, "ocean": ocean,
         "url": "http://localhost:8765/terrain"})


def cmd_worksheet(_args):
    if not STATE_FILE.exists():
        print("탐방 상태 파일이 없습니다."); return
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    lines = [f"# 📚 {state['tour_name']} — 학생 활동지", "",
             f"**이름:** ____________  **반:** ____  **번호:** ____  **날짜:** {datetime.now().strftime('%Y-%m-%d')}",
             "", "---"]
    for stop in state["stops"]:
        lines += ["---", f"## {circle_num(stop['index']-1)} {stop['name']}", ""]
        for o in stop.get("observation_points", []):
            lines.append(f"- {o}")
        lines.append("")
        for i, q in enumerate(stop.get("student_questions", [])):
            lines += [f"{i+1}. {q}", "", "   답: _______________________________________________", ""]
        lines += ["**느낀 점:** _______________________________________________", ""]
    lines += ["---", "## 전체 소감", "", "_______________________________________________"]
    print("\n".join(lines))


def cmd_report(_args):
    if not STATE_FILE.exists():
        print("탐방 상태 파일이 없습니다."); return
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    lines = [f"# 🗺️ {state['tour_name']} — 탐방 보고서", "",
             f"**생성일:** {state.get('created_at','')[:10]}  |  **정류장 수:** {state['total_stops']}개", "", "---"]
    for stop in state["stops"]:
        lines += [f"## {circle_num(stop['index']-1)} {stop['name']}", "",
                  f"**위치:** {stop['lat']:.4f}°N, {stop['lon']:.4f}°E", "",
                  f"**안내:** {stop.get('historical_significance','')}", ""]
        for o in stop.get("observation_points", []):
            lines.append(f"- {o}")
        lines.append("")
    print("\n".join(lines))


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="우리동네/역사탐방 네비게이터")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("neighborhood")
    s.add_argument("--region",     required=True)
    s.add_argument("--data",       default="{}")
    s.add_argument("--data-file",  default="", dest="data_file")
    s.add_argument("--center-lat", type=float, default=None, dest="center_lat")
    s.add_argument("--center-lon", type=float, default=None, dest="center_lon")
    s.add_argument("--radius",     type=float, default=2.0)

    s = sub.add_parser("tour")
    s.add_argument("--event",          required=True)
    s.add_argument("--locations",      default="[]")
    s.add_argument("--locations-file", default="", dest="locations_file")

    s = sub.add_parser("tour-nav")
    s.add_argument("--action", choices=["start","next","prev"], required=True)

    sub.add_parser("worksheet")
    sub.add_parser("report")
    sub.add_parser("serve")

    s = sub.add_parser("terrain")
    s.add_argument("--name",   required=True,  help="지형/산 이름")
    s.add_argument("--lat",    required=True,  type=float)
    s.add_argument("--lon",    required=True,  type=float)
    s.add_argument("--radius", type=float, default=15.0, help="반경(km), 해저지형은 200+ 권장")
    s.add_argument("--ocean",  action="store_true", help="해저/해양 지형 모드 (ETOPO1 사용)")

    s = sub.add_parser("climate")
    s.add_argument("--zone", choices=["desert","cold"], required=True, help="desert=건조지대, cold=한랭지대")

    sub.add_parser("climate-map")

    args = p.parse_args()
    dispatch = {
        "neighborhood": cmd_neighborhood,
        "tour":         cmd_tour,
        "tour-nav":     cmd_tour_nav,
        "worksheet":    cmd_worksheet,
        "report":       cmd_report,
        "serve":        cmd_serve,
        "terrain":      cmd_terrain,
        "climate":      cmd_climate,
        "climate-map":  cmd_climate_map,
    }
    dispatch[args.cmd](args)

if __name__ == "__main__":
    main()
