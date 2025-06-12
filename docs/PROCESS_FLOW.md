# 방화벽 정책 처리 흐름

본 문서는 `simple_firewall_app`에서 사용하는 단계별 파일 흐름을 설명합니다.

1. **Phase 1 – 방화벽 연동**
   - 장비 접속 정보를 입력하여 연결을 확인합니다.
2. **Phase 2 – 데이터 수집**
   - `upload_policies_file`: 미리 추출된 정책 파일을 업로드할 수 있습니다.
   - `extract_policies`: 방화벽에서 정책을 추출합니다.
   - `upload_usage_file`: 미리 추출된 사용이력 파일을 업로드할 수 있습니다.
   - `extract_usage`: 사용이력 데이터를 추출합니다.
   - `upload_duplicates_file`: 미리 추출된 중복 정책 파일을 업로드할 수 있습니다.
   - `extract_duplicates`: 중복 정책을 식별합니다.
3. **Phase 3 – 정보 파싱**
   - `parse_descriptions`: 정책 설명에서 신청번호 등을 파싱하여 파일로 저장합니다.
4. **Phase 4 – 데이터 준비**
   - 신청정보 파일(`application`)과 MIS ID 파일(`mis_id`)을 업로드 합니다.
5. **Phase 5 – 데이터 통합**
   - `add_mis_info`: MIS ID를 정책 파일에 통합합니다.
   - `merge_application_info`: 업로드한 신청정보를 정책에 병합합니다.
   - `vendor_exception_handling`: 벤더별 예외 정책을 처리합니다.
   - `classify_duplicates`: 중복정책 파일을 정리/공지/삭제용으로 분류합니다.
6. **Phase 6 – 결과 생성**
   - `add_usage_info`: 사용 이력을 정책에 반영합니다.
   - `finalize_classification`: 중복 정보가 반영된 최종 정책을 만듭니다.
   - `generate_results`: 기간만료·장기미사용 등 최종 결과 파일을 생성합니다.

각 단계에서 생성되는 파일은 `날짜_IP_단계명[_세부].xlsx` 형식으로 `results/` 디렉터리에 저장됩니다.
업로드 파일 역시 동일한 규칙으로 `uploads/` 폴더에 기록됩니다.
