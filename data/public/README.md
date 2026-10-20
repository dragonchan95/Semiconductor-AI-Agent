# SECOM 공개 데이터 출처

- McCann, M. & Johnston, A. (2008). SECOM. UCI Machine Learning Repository.
- 원본: https://archive.ics.uci.edu/dataset/179/secom
- 다운로드: https://archive.ics.uci.edu/static/public/179/secom.zip
- 라이선스: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
- SHA-256: `eea568baf3c2229096d7d294cf0b096b5502bd96d92c0b80a65b84714059be8e`

원본 ZIP을 보관합니다. 변환한 CSV는 `var/`에서 생성하고 커밋하지 않습니다. 변환 내용: 590개 센서 열 이름 부여, -1 pass→0 normal, 1 fail→1 defect, 인용된 일시를 ISO 형식으로 변환, 단일 집단 `SECOM` 표시. 원본에는 실제 A/B/C 제품 식별자가 없습니다.
