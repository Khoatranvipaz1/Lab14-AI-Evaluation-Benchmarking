# Báo cáo cá nhân - Trần Văn Khoa - 2A202600827

## 0. Thong tin chung

- **Họ tên:** Trần Văn Khoa
- **MSSV:** 2A202600827
- **Bai lab:** Day 14 - AI Evaluation Factory
- **File nop ca nhan:** `analysis/reflections/reflection_TranVanKhoa.md`
- **Vai tro chinh:** Regression Testing & Auto-Gate Owner
- **Hang muc phu trach theo rubric nhom:** Muc 4 - Regression Testing & Auto-Gate (10 diem)

## 1. Pham vi cong viec ca nhan

Trong bai lab nay, em phu trach phan **Regression Testing & Auto-Gate**. Muc tieu cua phan nay la bien ket qua benchmark thanh mot quyet dinh release ro rang:

- So sanh chat luong giua **Agent V1** va **Agent V2**.
- Tinh delta giua hai phien ban.
- Tu dong dua ra quyet dinh **Release** neu chat luong cai thien.
- Tu dong dua ra quyet dinh **Rollback/Block** neu chat luong bi giam hoac khong dat nguong.

Em khong phu trach truc tiep cac module Retrieval Evaluation, Dataset/SDG, Multi-Judge hay Performance. Cac module do duoc xem la nguon cung cap metric dau vao cho Auto-Gate.

## 2. Dong gop ky thuat

### 2.1. Thiet ke regression flow

Trong `main.py`, regression flow duoc thiet ke theo huong chay benchmark cho hai phien ban agent:

1. Chay benchmark cho `Agent_V1_Base`.
2. Chay benchmark cho `Agent_V2_Optimized`.
3. Lay metric tong hop cua tung phien ban.
4. Tinh delta diem trung binh:

```text
delta = avg_score_v2 - avg_score_v1
```

Neu `delta > 0`, he thong cho phep release. Neu `delta <= 0`, he thong block release de tranh dua mot phien ban kem hon len moi truong su dung.

### 2.2. Auto-Gate decision

Phan Auto-Gate trong `main.py` co nhiem vu chuyen metric thanh quyet dinh cuoi cung:

- **APPROVE / RELEASE:** Khi Agent V2 co diem trung binh cao hon Agent V1.
- **BLOCK / ROLLBACK:** Khi Agent V2 khong cai thien hoac co dau hieu regression.

Cach lam nay giup nhom khong phu thuoc vao cam tinh khi release agent. Moi quyet dinh deu dua tren ket qua benchmark co the lap lai.

### 2.3. Metric dau vao cho release gate

Trong ban hien tai, release gate su dung `avg_score` lam metric chinh. Tuy nhien, de gate chac chan hon, em de xuat dung them cac metric do cac module khac cung cap:

| Metric | Nguon | Vai tro trong Auto-Gate |
| --- | --- | --- |
| `avg_score` | Multi-Judge / benchmark summary | Do chat luong cau tra loi tong quat |
| `hit_rate` | Retrieval Evaluation | Kiem tra retriever co lay dung tai lieu hay khong |
| `mrr` | Retrieval Evaluation | Do tai lieu dung co nam o vi tri cao hay khong |
| `agreement_rate` | Multi-Judge | Kiem tra do tin cay cua diem judge |
| `latency` | Async Runner / Performance | Kiem tra toc do phan hoi |
| `cost` / `token_usage` | Cost report | Kiem tra chi phi van hanh |

Nhung metric nay khong phai phan em truc tiep trien khai, nhung la dau vao can thiet de Auto-Gate ra quyet dinh dung hon.

### 2.4. De xuat nguong gate thuc te

Neu trien khai production, em de xuat gate khong chi dua vao `avg_score`, ma nen co bo nguong nhu sau:

- `avg_score_v2 >= avg_score_v1`
- `hit_rate_v2` khong giam qua 5% so voi V1
- `agreement_rate_v2 >= 0.7`
- `latency_v2` khong tang qua 20%
- `cost_v2` khong tang qua 20%
- Hard cases khong co loi nghiem trong moi

Neu mot trong cac dieu kien quan trong bi vi pham, gate nen tra ve **BLOCK RELEASE** de nhom kiem tra lai truoc khi release.

## 3. Technical Depth

### 3.1. Tai sao regression testing quan trong voi AI Agent

AI Agent co tinh bat dinh cao hon phan mem truyen thong. Mot thay doi nho trong prompt, retriever, model hoac chunking co the lam tang diem o mot nhom case nhung lam giam chat luong o nhom case khac. Vi vay, regression testing giup tra loi cau hoi:

```text
Phien ban moi co that su tot hon phien ban cu khong?
```

Neu khong co regression gate, nhom co the release V2 chi vi mot vai vi du nhin tot hon, trong khi tong the benchmark lai te hon.

### 3.2. Cach doc delta

Delta la phan chenh lech giua metric cua V2 va V1:

```text
delta_score = avg_score_v2 - avg_score_v1
```

- `delta_score > 0`: V2 cai thien ve diem trung binh.
- `delta_score = 0`: V2 khong co cai thien ro rang.
- `delta_score < 0`: V2 bi regression.

Tuy nhien, delta diem trung binh khong du de quyet dinh release. Neu `avg_score` tang nhe nhung `hit_rate` giam manh, agent co the dang tra loi tot hon o case de nhung te hon o case can retrieval chinh xac.

### 3.3. MRR trong release gate

MRR la metric cua Retrieval Evaluation, nhung Auto-Gate can doc metric nay de tranh release agent co retrieval kem. MRR cho biet tai lieu dung xuat hien som hay muon trong danh sach retrieved documents.

Vi du:

- Expected document nam o vi tri 1: MRR = 1.0
- Expected document nam o vi tri 2: MRR = 0.5
- Khong tim thay expected document: MRR = 0.0

Neu V2 co `avg_score` tang nhung MRR giam, em se de xuat gate canh bao hoac block release, vi retrieval quality co dau hieu xau di.

### 3.4. Cohen's Kappa va agreement trong release gate

`agreement_rate` cho biet cac judge co dong thuan hay khong. Tuy nhien, trong he thong that, em de xuat bo sung **Cohen's Kappa** vi metric nay tinh den kha nang dong thuan do ngau nhien.

Y nghia voi Auto-Gate:

- Judge dong thuan cao: diem benchmark dang tin cay hon.
- Judge dong thuan thap: khong nen release chi dua vao diem trung binh.
- Judge mau thuan: can goi judge thu ba hoac review thu cong.

Vi vay, `agreement_rate` hoac Cohen's Kappa nen la dieu kien phu trong release gate.

### 3.5. Position Bias trong judge va tac dong den release

Position Bias la hien tuong judge uu tien cau tra loi o vi tri dau, vi du response A, thay vi cham dua tren chat luong that. Neu judge co bias, release gate co the approve sai phien ban.

De giam rui ro, em de xuat:

- Dao thu tu cau tra loi V1/V2 khi judge so sanh.
- An danh ten phien ban khi cham.
- Lay trung binh qua nhieu lan judge.

## 4. Problem Solving

### 4.1. Van de: Chi so trung binh co the che dau loi nghiem trong

Neu chi dung `avg_score`, V2 co the duoc release du bi fail o hard cases. Cach xu ly cua em la de xuat gate nhieu dieu kien, ket hop score, retrieval, judge agreement, latency va cost.

### 4.2. Van de: Module khac chua hoan thien

Auto-Gate phu thuoc vao metric tu Retrieval, Multi-Judge va Performance. Trong luc cac module khac chua co ket qua that, em van co the xay dung gate voi interface metric chuan hoa. Khi cac module khac hoan thien, gate chi can nhan metric that va ap dung cung logic release/block.

### 4.3. Van de: Diem judge co the khong dang tin

Neu judge disagreement cao, diem trung binh co the khong phan anh dung chat luong. Em de xuat gate khong approve neu `agreement_rate` qua thap, va can them buoc review hoac judge thu ba.

### 4.4. Van de: Chat luong tang nhung chi phi/latency tang qua cao

Mot V2 co diem cao hon nhung cham hon nhieu hoac ton chi phi hon nhieu co the khong phu hop de release. Em de xuat gate can theo doi them latency va cost, vi trong san pham that, chat luong phai can bang voi trai nghiem nguoi dung va chi phi van hanh.

## 5. Doi chieu rubric ca nhan

| Hang muc cham diem | Yeu cau trong rubric | Noi dung trong bao cao |
| --- | --- | --- |
| Engineering Contribution - 15 diem | Dong gop cu the vao module phuc tap, giai trinh ky thuat | Muc 2 trinh bay regression flow, auto-gate, metric dau vao va nguong gate |
| Technical Depth - 15 diem | Hieu MRR, Cohen's Kappa, Position Bias, trade-off chi phi/chat luong | Muc 3 giai thich cac metric nay trong vai tro dau vao cho release gate |
| Problem Solving - 10 diem | Neu van de phat sinh va cach xu ly | Muc 4 trinh bay cac rui ro cua release gate va cach giai quyet |

## 6. Bang chung doi chieu trong repo

- `main.py`: Co logic chay benchmark cho `Agent_V1_Base` va `Agent_V2_Optimized`.
- `main.py`: Co tinh `delta` giua V2 va V1.
- `main.py`: Co quyet dinh approve/block dua tren delta.
- `reports/summary.json`: La output ky vong de luu metric tong hop sau benchmark.
- `reports/benchmark_results.json`: La output ky vong de luu chi tiet tung test case sau benchmark.

Luu y: Neu giang vien yeu cau bang chung commit rieng theo tung thanh vien, can nop kem lich su commit tren repository. Bao cao nay khong tu tao commit ID de tranh dua thong tin khong dung.

## 7. Han che va huong cai tien

Phan Regression Testing & Auto-Gate hien tai co the cai tien them:

- Them nguong gate day du thay vi chi dung `avg_score`.
- Ghi ro ly do block release vao `summary.json`.
- Them so sanh theo tung nhom case: easy, hard, adversarial, out-of-context.
- Them cost va token usage vao dieu kien gate.
- Them canh bao khi `agreement_rate` thap.
- Them che do manual review neu V2 chi tang diem nhe nhung fail hard cases.

## 8. Ket luan

Phan dong gop ca nhan cua em la **Regression Testing & Auto-Gate**. Phan nay giup bien ket qua benchmark thanh quyet dinh release co co so: Agent V2 chi nen duoc release khi tot hon V1 va khong lam giam cac metric quan trong. Qua bai lab, em hieu rang voi AI Agent, release khong nen dua vao cam tinh ma can co gate tu dong dua tren quality, retrieval, judge reliability, latency va cost.
