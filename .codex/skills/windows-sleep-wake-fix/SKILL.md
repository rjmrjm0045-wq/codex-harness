---
name: windows-sleep-wake-fix
description: Windows PC가 절전 모드에서 깨어난 뒤 잠금/로그인 화면이 멈추고 마우스만 움직이는 문제를 진단하고 예방 설정을 적용한다. 사용자가 "절전 후 화면 멈춤", "로그인 화면 반응 없음", "잠금 화면에서 안 넘어감"을 말하거나 이 설정을 갱신·되돌리려 할 때 사용한다.
---

# Windows 절전 후 화면 멈춤 해결

## 증상
- 절전에서 깨어나면 잠금 화면 배경만 보이고 시계/로그인 창이 없다.
- 마우스 커서는 움직이지만 클릭해도 반응이 없다.

## 지금 멈춰 있을 때 (응급 조치, 순서대로)
1. `Space` / `Enter` / `Esc` 키 누르기
2. `Ctrl + Alt + Delete`
3. `Win + Ctrl + Shift + B` (그래픽 드라이버 재시작)
4. 키보드 Caps Lock 불빛 확인 → 안 켜지면 다른 USB 포트에 다시 꽂기
5. 다중 모니터라면 `Win + P` → "PC 화면만"
6. 최후 수단: 전원 버튼 5~10초 (저장 안 된 작업 손실)

## 재발 방지 (로그인한 뒤 1회 실행)
`scripts/run-fix.cmd` 를 더블클릭 → 관리자 권한 허용.

직접 실행하려면 관리자 PowerShell에서:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\fix-sleep-wake.ps1
```

스크립트가 하는 일:
| 설정 | 변경 | 이유 |
|---|---|---|
| 빠른 시작 (`HiberbootEnabled`) | 끔 | 절전/재개 시 드라이버 상태 꼬임 방지 |
| USB 선택적 절전 (AC/DC) | 끔 | 키보드·마우스가 늦게 깨어나는 문제 방지 |
| PCI Express 링크 상태 전원 관리 (AC/DC) | 끔 | 그래픽 카드가 깨어나지 못하는 문제 방지 |
| 진단 | 보고 | 그래픽 카드 드라이버 버전, 최근 7일 이벤트 4101(디스플레이 드라이버 응답 중지) |

- 변경 전 전원 관리 옵션을 `%ProgramData%\SleepWakeFix\` 에 `.pow` 로 백업한다.
- 적용 후 **재부팅**해야 빠른 시작 설정까지 반영된다.
- 이벤트 4101이 있으면 그래픽 드라이버를 제조사(NVIDIA/AMD/Intel) 사이트에서 최신으로 설치하도록 안내한다.

## 되돌리기
`run-fix.cmd undo` 또는:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\fix-sleep-wake.ps1 -Undo
```
빠른 시작은 최초 실행 전 값으로, 나머지는 Windows 기본값으로 복원한다.

## 업데이트 규칙
- 이 문제와 관련된 설정을 추가/변경하면 `scripts/fix-sleep-wake.ps1`, 위 표, 그리고 `scripts/test_windows_sleep_wake_fix.py`(저장소 루트)를 함께 고친다.
- `.ps1` 은 **UTF-8 BOM** 으로 저장한다 (Windows PowerShell 5.1 한글 깨짐 방지).
- `.cmd` 는 **ASCII만** 사용한다.
- 테스트: `python3 -m pytest scripts/test_windows_sleep_wake_fix.py -q`
