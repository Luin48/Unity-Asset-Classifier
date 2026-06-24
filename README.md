# Unity Asset Classifier

Unity 프로젝트의 `Assets` 폴더를 스캔하고, 기존에 임포트된 에셋 폴더를 태그별로 정리하는 Windows용 로컬 도구입니다.

## 주요 기능

- Unity `Assets` 폴더 스캔
- 에셋 폴더 태그 지정
- 선택 항목 일괄 정리
- `태그 없음` 선택 시 태그 폴더를 만들지 않고 `Assets` 최상위 기준으로 정리
- 판매자 그룹과 단일 에셋 구조 전환
- 현재 화면 기준 전체 선택
- 정리 완료 후 비어 있는 기존 최상단 폴더와 `.meta` 삭제
- 다크/라이트 모드

## 다운로드

GitHub Releases에서 `UnityAssetClassifier.exe`를 내려받아 실행합니다.

[Releases](https://github.com/Luin48/Unity-Asset-Classifier/releases)

## 초기 설정

1. `UnityAssetClassifier.exe`를 실행합니다.
2. 브라우저에 로컬 화면이 열립니다.
3. 왼쪽 `Assets 폴더`에 정리할 Unity 프로젝트의 `Assets` 경로를 입력합니다.
   예:
   ```text
   C:\Users\사용자명\UnityProjects\MyProject\Assets
   ```
4. 필요한 태그를 오른쪽 태그 패널에서 추가하거나 수정합니다.
5. `설정 저장`을 누릅니다.

`스캔 제외 최상위 폴더`는 태그명과 자동으로 동기화됩니다. 이미 정리된 태그 폴더가 다시 스캔 대상에 들어가지 않게 하기 위한 설정입니다.

## 사용법

1. `다시 스캔`을 눌러 현재 `Assets` 폴더를 읽습니다.
2. 정리할 항목을 클릭하거나 체크박스로 선택합니다.
3. 각 항목의 태그를 선택합니다.
4. 여러 항목에 같은 태그를 적용하려면 상단 태그 선택 후 `태그 적용`을 누릅니다.
5. `선택 항목 정리`를 누릅니다.

정리 결과 예:

```text
Assets\Seller\Asset
-> Assets\의상\Seller\Asset
```

`태그 없음`을 선택한 경우:

```text
Assets\Seller\Asset
-> Assets\Seller\Asset
```

## 판매자 그룹 / 단일 에셋

스캔 결과는 폴더 구조에 따라 자동으로 나뉩니다.

- `판매자 그룹`: `Assets\<판매자>\<에셋>` 구조로 보이는 폴더
- `단일 에셋`: 최상위 폴더 하나가 그대로 에셋인 경우

판매자 그룹이 실제로는 하나의 에셋이면 그룹 헤더의 `단일 에셋으로 보기`를 누릅니다.

단일 에셋을 다시 하위 폴더별 에셋으로 나누고 싶으면 항목을 선택한 뒤 `판매자 그룹으로 보기`를 누릅니다.

## 정리 규칙

- 태그 폴더는 스캔 대상에서 제외됩니다.
- 이동은 `선택 항목 정리`를 눌렀을 때만 실행됩니다.
- 이동 기록은 `move_log.jsonl`에 저장됩니다.
- 정리 완료 후 비어 있는 원래 최상단 폴더는 삭제됩니다.
- 폴더 안에 아직 파일이나 폴더가 남아 있으면 삭제하지 않습니다.

## 개발 실행

Python 3.12 이상 기준입니다.

```powershell
cd "Unity-Asset-Classifier"
python local_app\launcher.py
```

## 빌드

PyInstaller가 필요합니다.

```powershell
python -m pip install pyinstaller pillow
.\scripts\build-exe.ps1
```

결과:

```text
dist\UnityAssetClassifier.exe
```

## 주의

- 정리 작업은 실제 Unity 프로젝트의 폴더를 이동합니다.
- 실행 전 Unity 프로젝트를 백업하거나 버전 관리 상태를 확인하는 것을 권장합니다.
- Unity가 켜져 있으면 폴더 이동 후 Unity가 자동으로 다시 임포트할 수 있습니다.
