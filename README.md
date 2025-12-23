<div>

  # 🧠 PDF_MASK
  **학습 효율 증대를 위한 PDF 핵심 키워드 자동 마스킹 서비스**

  <br/>

  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white"/>
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/GCP-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white"/>

</div>

<br/>

## 1. 프로젝트 개요 (Overview)

이 프로젝트에서 저희는 **능동적 회상(Active Recall)** 학습법을 돕기 위해, 전공 서적이나 논문의 핵심 키워드를 자동으로 빈칸 처리해주는 웹 서비스를 설계하고 구현했습니다.

많은 대학생들이 암기를 위해 직접 수정테이프로 단어를 지우거나 손으로 가리는 반복적인 수작업을 수행한다는 점에 주목했습니다. 기존의 PDF 편집 도구들은 개인정보 보호(Privacy)에 초점이 맞춰져 있어 학습용으로 활용하기엔 한계가 있었습니다.

이에 저희는 **형태소 분석(Morphological Analysis) 기술과 비동기 분산 처리 시스템**을 도입하여, 사용자가 PDF를 업로드하면 시스템이 명사 등 핵심 키워드를 식별하고 자동으로 '학습용 빈칸 문제'로 변환해주는 서비스를 개발하여 학습 효율성을 극대화하고자 했습니다. (현재 텍스트 PDF를 지원하며, 스캔 문서를 위한 OCR 기능은 개발 진행 중입니다.)

* 개발 기간 : 2025.09~2025.11
* 참여 인원 : 3명
  * 김민준 : 마스킹 엔진 개발
  * 김지원 : 백엔드 및 DevOps
  * 이가은 : 백엔드 및 프론트엔드


## 2. 주요 기능 (Key Features)

저희가 구현한 시스템의 핵심 기능은 다음과 같습니다.

* **NLP 기반 키워드 추출:** 단순한 단어 매칭이 아니라, **Kiwi 형태소 분석기**를 활용하여 문맥의 핵심이 되는 명사와 조사 앞의 주요 키워드를 문법적으로 식별해냅니다.
* **정밀 좌표 매핑:** **PyMuPDF**를 통해 식별된 단어의 문자 단위 좌표(Bbox)를 정밀하게 추적하고, 인접한 영역을 병합하여 깔끔한 마스킹 박스를 생성합니다.
* **스마트 빈칸 생성:** 해당 좌표의 텍스트를 완전히 소거하여 정답 유출을 방지하고, 그 위에 빈 박스를 그려 학습자가 답을 유추할 수 있는 환경을 제공합니다.
* **대용량 파일 비동기 처리:** 수백 페이지에 달하는 전공 서적도 처리할 수 있도록 **Celery와 Redis**를 연동하여, 웹 서버의 응답 지연(Timeout) 없이 백그라운드에서 작업을 처리합니다.

<br/>

## 3. 시스템 아키텍처 (System Architecture)

저희는 대용량 데이터 처리의 안정성을 위해 **비동기 큐(Message Queue)** 아키텍처로 시스템을 설계했습니다. 전체 데이터 처리 흐름은 다음과 같습니다.

<div>
  <table>
    <tr>
      <th width="30%">Client & Web Server</th>
      <th width="40%">Async Task Processing</th>
      <th width="30%">Result Handling</th>
    </tr>
    <tr>
      <td align="center" valign="top">
        <b>User Upload</b><br/><br/>
        🖥️ <b>Client</b><br/>
        (File Upload)<br/>
        ⬇️<br/>
        🌐 <b>Nginx</b><br/>
        (Reverse Proxy)<br/>
        ⬇️<br/>
        🐍 <b>Django</b><br/>
        (Task Producer)
      </td>
      <td align="center" valign="top">
        <b>Message Queue System</b><br/><br/>
        📨 <b>Redis</b><br/>
        (Task Broker)<br/>
        ⬇️<br/>
        ⚙️ <b>Celery Worker</b><br/>
        (Consumer / Processing)<br/>
        <br/>
        <i>"NLP & PDF Engine"</i>
      </td>
      <td align="center" valign="top">
        <b>Storage & Response</b><br/><br/>
        💾 <b>Shared Volume</b><br/>
        (File I/O)<br/>
        ⬇️<br/>
        ✅ <b>Redis Backend</b><br/>
        (Status Check)<br/>
        ⬇️<br/>
        📥 <b>User Download</b>
      </td>
    </tr>
  </table>
</div>

1.  **클라이언트 (Web):** 사용자가 PDF를 업로드하면 Nginx를 거쳐 Django 서버가 요청을 받습니다.
2.  **작업 큐 (Task Queue):** Django는 즉시 파일을 처리하지 않고, 작업 요청을 **Redis 브로커**로 보낸 뒤 사용자에게는 "처리 중" 상태를 응답합니다(Non-blocking).
3.  **비동기 워커 (Worker):** 대기 중인 **Celery 워커**가 Redis에서 작업을 가져와 무거운 형태소 분석 및 마스킹 작업을 수행합니다.
4.  **결과 처리:** 변환된 PDF는 Shared Volume(공유 볼륨)에 저장되며, 작업 완료 신호가 감지되면 사용자는 결과물을 다운로드할 수 있습니다.

<br/>

## 4. 실행 화면

<img width="1734" height="1275" alt="main" src="https://github.com/user-attachments/assets/2999b1aa-5727-44cb-b16b-accdad7217bf" />
</br>
<메인 화면>
</br>
</br>
<img width="1742" height="1280" alt="masking95" src="https://github.com/user-attachments/assets/ac5a6d19-0678-4e24-8191-7b5cdd6f5c80" />
</br>
<마스킹 비율 0.95 적용하여 변환>
</br>
</br>
<img width="1735" height="1279" alt="masking95_2" src="https://github.com/user-attachments/assets/137d50dc-e4ae-45e9-b92b-ec6036e27a0a" />
</br>
<마스킹 된 pdf>
</br>
</br>
<img width="1744" height="1274" alt="masking2" src="https://github.com/user-attachments/assets/b9332de2-c349-4de6-b5f7-71ca10a851d9" />
<마스킹 비율 0.2 pdf>
</br>
</br>
<img width="1739" height="1284" alt="ppt_to_pdf" src="https://github.com/user-attachments/assets/4f56e975-e234-46eb-9e3b-1ad1b93fe09b" />
<img width="1740" height="1281" alt="docx_to_pdf" src="https://github.com/user-attachments/assets/2b857126-051e-43ec-b703-1df14a8c3b5e" />
docx,ppt 변환 화면
</br>
</br>
https://github.com/user-attachments/assets/b6af67c2-fb77-437d-9aac-ce92d7e94ffa


## 5. 성능 개선 및 문제 해결 (Troubleshooting)

저희는 개발 과정에서 발생한 기술적 난관을 해결하며 시스템의 안정성을 확보했습니다.

* **Time-out 문제 해결:** 초기에는 단일 컨테이너에서 동기식으로 처리하다 보니, 논문과 같이 페이지가 많은 파일은 30초 이상의 시간이 소요되어 HTTP Timeout이 발생했습니다. 이를 **Celery+Redis 비동기 아키텍처**로 전환하여 사용자 경험을 개선하고 대용량 처리 능력을 확보했습니다.
* **Docker 네트워크 통신:** 배포 환경에서 컨테이너 간(Django ↔ Redis) 연결이 끊기는 문제가 발생했습니다. 이를 해결하기 위해 `docker-compose`의 내부 DNS 기능을 활용하여 호스트명을 명시하고, 서비스 간 의존성(depends_on)을 설정하여 안정적인 통신 채널을 구축했습니다.

<br/>

## 6. 한계점 및 향후 과제 (Limitations & Future Work)

프로젝트를 진행하며 다음과 같은 한계점들을 발견했습니다.

**한계점 (Limitations)**
* **문맥 이해의 한계:** 현재 형태소 분석기(Kiwi) 기반의 알고리즘은 단어의 품사(명사, 조사) 위주로 판별하므로, 복합적인 문맥 의미를 완벽하게 파악하는 데에는 일부 제약이 있습니다.
* **이미지 PDF 처리 제약 (해결 중):** 텍스트 레이어가 없는 스캔본(이미지) PDF의 경우 현재 버전에서는 인식이 불가능합니다. (하단의 OCR 도입을 통해 해결 중입니다.)
* **OCR 파인튜닝 데이터 부족: 특정 문서 형식이나 한국어 고유 특성에 최적화된 OCR 파인튜닝용 공공 데이터셋이 부족하여, 고성능 모델 학습을 위한 기초 데이터를 직접 구축해야 하는 리소스상의 한계가 있었습니다.

**개발 로드맵 (Development Roadmap)**
* **🚧 OCR 기능 통합:** Paddle OCR 엔진을 파이프라인 전단에 연동하는 작업을 **현재 진행 중**입니다. 곧 스캔된 필기 노트에서도 이미지 내의 텍스트를 추출하고 마스킹할 수 있도록 업데이트될 예정입니다.
* **🛠️ 데이터셋 자동 생성 GUI 개발: 데이터 부족 문제를 해결하기 위해 PyMuPDF 라이브러리를 활용한 자동 데이터셋 생성 GUI를 구축하고 있습니다. 이를 통해 실제 PDF 데이터를 학습용 이미지와 텍스트 쌍으로 빠르게 변환하여 OCR 모델의 정확도를 지속적으로 고도화할 계획입니다.
* **📅 LLM 기반 중요도 분석:** 단순 빈도나 품사 기반이 아닌, LLM을 활용하여 문단 내에서 의미적으로 가장 중요한 '핵심 개념'을 선별하는 고도화된 마스킹 로직을 도입할 계획입니다.
