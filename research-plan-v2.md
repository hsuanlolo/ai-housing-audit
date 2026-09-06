# Research Plan v2 — Auditing the Cost of Algorithmic Omission

(Revised 2026-08-23. Supersedes v1. Changes summarized at the end.)

## Proposed title

**What It Costs to Be Overlooked: Auditing Constraint Fidelity, Forgone Opportunity, and Identity-Conditioned Disparity in AI Housing Search**

Short form: *The Price of Algorithmic Omission in High-Stakes Search*

**研究定位：** 以住宅搜尋作為 high-stakes recommendation 場景，測量 AI 推薦「漏掉了什麼」的**可驗證成本**（以美元與通勤分鐘計），並檢驗這個成本是否隨使用者身分線索而不同。

**研究範圍：** 紐約市租屋市場；listing-level 資料；synthetic user profiles；in-context ranking audit（非 deployed product audit）；不招募真人、不使用平台內部行為資料。

---

## 1. Research gap

到 2026 年 8 月為止，相關文獻已有三條成熟路線：

1. **Housing steering audits。** LLM 是否因使用者族裔而推薦不同區位。Liu et al. (EAAMO '24) 以 168,000 prompts 測試 GPT-4，發現 racial steering、default whiteness，以及將少數族裔導向 lower-opportunity-index 社區。2606.06694 (AIES '26) 擴大到 7 個模型、4 個城市，並指出 steering 是 interpretive 行為而非固定模型屬性。
2. **產業端 ranking evaluation。** 2607.14835（QuintoAndar）以 960k query-item pairs 評估 LLM re-ranker，production A/B 顯示 +5.3% CTR、+4.8% scheduled visits。
3. **Omission / coverage audits。** 2608.07069（*Invisible to the Machine*, 2026-08）以**完整市場普查**為基準，列舉 Bali 兩地全部 4,776 家店，測試 2,208 筆回應，發現 85.6% 的店家從未被推薦，並指出主要失效模式是 staleness 而非 hallucination。

**必須誠實面對的一點：** v1 宣稱的 gap（「AI 漏掉了什麼」）在餐飲領域已於三週前被做完。單純的 omission audit 不再是新貢獻。

真正尚未被處理的，是這三條線的**交集**：

> 現有 omission audit 沒有受保護身分（protected class），也沒有使用者可驗證的硬性條件；現有 steering audit 沒有 oracle，也沒有把傷害換算成成本。因此目前**沒有任何研究能說出這句話**：
>
> *「在完全相同的需求與完全相同的房源集合下，僅改變身分線索，使用者被推薦的房源平均貴 $X／月、通勤多 Y 分鐘，且有 Z% 的推薦被同一集合中的其他房源嚴格支配。」*

本研究的貢獻定位因此是：

> **Not "AI misses things" (already known), and not "AI steers" (already known), but: the forgone opportunity is measurable in dollars and minutes against a verifiable ground truth, it is unequally distributed across identity cues, and a specific architectural change reduces it.**

住宅是少數同時具備下列三個條件的領域，這是本研究選址的理由，不是便利性：

* 硬性條件可**客觀驗證**（租金、房間數、通勤時間），不需依賴 LLM-as-judge。
* 存在**法定公平性制度**（Fair Housing Act；紐約市另有 NYC Human Rights Law 對 source of income 的保護）。
* 遺漏的成本可直接以**貨幣與時間**表示，不需效用假設。

---

## 2. Research questions and hypotheses

| Research question | Hypotheses |
| --- | --- |
| **RQ1. Constraint fidelity:** AI 是否遵守使用者明確陳述的硬性條件？ | **H1a:** 在候選集合中同時存在合格與不合格房源時，LLM 推薦會出現 confirmed violations（超預算、房間數不足、超過通勤上限）。**H1b:** 違反率隨同時作用的條件數上升。*(註：H1b 在一般 instruction-following 文獻中已知（compositional constraint satisfaction，如 2608.12426、SEQUOR 2605.06353）。本研究貢獻是 domain-specific magnitude 與其分佈，不宣稱發現此現象。)* |
| **RQ2. Forgone opportunity:** 在推薦看似合理時，AI 是否仍漏掉客觀上更好的房源？ | **H2a:** 相當比例的推薦房源會被同一候選集合中的其他房源 **strictly dominated**（更便宜 **且** 通勤更短 **且** 房間數不少）。**H2b:** dominance rate 隨候選集合密度與偏好模糊度上升。 |
| **RQ3. Identity-conditioned disparity:** 這些失效是否隨身分線索不均等分布？ | **H3a:** 在相同 profile、相同候選集合、相同排序條件下，僅改變身分線索，會改變 RentGap、CommuteGap、dominance rate 或 neighborhood exposure。**H3b:** 顯性受保護屬性（housing voucher）的效果大於姓名線索的效果。 |
| **RQ4. Mitigation and its side effects:** 架構設計能否降低這些失效，代價是什麼？ | **H4a:** Constraint-first 架構消除 verifiable violations（**依定義成立，非實證發現**），但其對 opportunity loss 與 identity gap 的影響為 open question。**H4b:** 觸發 fair-housing guardrail 的 prompt 會提高 refusal / information-withholding rate，並可能同時降低 steering 與降低推薦實用性。 |

**核心紀律：** 只研究這四件事。不延伸到真人偏好變化、實際成交、長期福利，或全美市場。

---

## 3. Data sources

### Core（load-bearing，缺一不可）

| Source | Variables | Purpose |
| --- | --- | --- |
| **RentCast API** `/listings/rental/long-term` | 租金、地址、座標、房型、bed/bath、面積、status、days on market、listing history | Listing universe |
| **ACS 5-year (tract)** | 中位所得、租金負擔、人口組成、租屋比例 | Neighborhood exposure outcome only |
| **GTFS + GTFS-RT static (MTA)** | 站點、路線、時刻表 | Transit commute matrix |

### Cut from v1（明確刪除，並說明理由）

| Dropped | 理由 |
| --- | --- |
| **LEHD/LODES** | 不服務任何一個 RQ。通勤已由 GTFS 計算；就業可及性不是 outcome。 |
| **Opportunity Insights** | 只在 neighborhood exposure 敘述中出現，ACS 已足夠。保留會增加一週工作量且無對應假設。 |
| **NYC Housing Connect** | eligibility 規則無法完整重建（v1 自己也承認）。以「不完整 eligibility 做 robustness」會製造新的 validity 問題，不是解決它。 |

### 資料量與覆蓋率

* 目標 **3,000–5,000** 筆 NYC active long-term rental listings。
* **API 額度算術：** free tier 50 requests/month × 500 records/request = 25,000 record-slots/month。以 city + pagination 抓取可行；**不要**以 zip code 逐個抓（NYC 約 180 個 zip，一輪即超額）。建議預算一個月 Foundation tier（$74）作為保險。
* **必做的 coverage benchmark（v1 沒有）：** NYC 租屋市場以 StreetEasy / REBHS 管道為主，MLS syndication 覆蓋可能系統性低估 no-fee 與小房東物件。須以 ACS 租金分佈與 NYC Housing and Vacancy Survey 的租金分位數，比對 listing 樣本的租金與 borough 分佈，並在論文中以一張表呈現偏誤方向。這是 housing 期刊審查者必問的問題。
* **資料釋出：** 檢查 RentCast ToS 後，預設只釋出 code、derived aggregates 與 listing IDs，**不釋出 raw listings**。Week 1 就要確認，不要等到 Week 12。

---

## 4. Study design

### Step 1. Build the listing universe

保留條件：active、租金在 P1–P99 之內、地址可 geocode、bedrooms 可辨識、可對應 census tract。

清理：重複 listing（address + bed + rent 指紋）、同物件多次上架（取最新）、不合理租金／面積、無法定位者。

**缺漏欄位一律標記為 `unknown`，不得推定為符合或不符合。** 這直接對應 outcome 中的 "unverifiable" 類別。

### Step 2. Commute matrix

* 工具：`r5py` 或 OpenTripPlanner。**固定一個出發時間（平日 08:00 EST）**，不做 time-of-day 變化。
* 目的地：**3 個**（Midtown Manhattan、Downtown Manhattan/FiDi、Downtown Brooklyn）。v1 的 5–10 個沒有對應假設，只增加計算量。
* 規模：約 4,000 listings × 3 destinations ≈ 12,000 routings。
* **這是整個計畫最大的排程風險。** 若過去沒有架設過 OTP，先做 Week 1 的 spike，失敗就退回 tract-to-tract travel-time matrix（精度損失可接受且可說明）。

### Step 3. Synthetic user profiles

**150 base scenarios**（v1 為 250；此處以較少 profile 換取每格 replicates，見 Step 7）。

每個 profile 的變異維度：

* Budget（分位數對應真實租金分佈，非任意數字）
* Unit type：studio / 1BR / 2BR
* Work location：3 個之一
* Max commute：30 / 45 / 60 min
* Priority ordering：rent-first / commute-first / location-first
* Request specificity：explicit constraints vs. lifestyle-phrased（對應 H2b）

**Identity conditions（4 個，v1 為 3 個）：**

1. **Neutral** — 無任何身分線索（baseline）
2. **Name cue A** — 姓名線索組 A
3. **Name cue B** — 姓名線索組 B
4. **Housing voucher disclosure** — 「I have a CityFHEPS / Section 8 voucher」

關於身分線索的三點紀律（v1 未處理）：

* 姓名**不自行發明**，須取自已發表的 name-perception 資料集，並回報該姓名在 race 與 SES 兩個維度上的感知分數，直接面對 Gaddis 的 SES confound 批評。
* 每個 profile 從 name pool 中**隨機輪替**多組姓名，姓名 identity 為 random effect，不是固定的兩個名字。
* 加入 voucher 條件的理由：source of income 在紐約市受法律保護、政策相關性最高，且它是一個**正當的實質限制**（會改變合法可得的房源集合），因此可以區分「合法的條件調整」與「不當的品質降級」。這是本研究相對於既有 name-only steering audit 的實質推進。

### Step 4. Candidate pool construction（v1 完全缺漏的關鍵步驟）

這一步決定整個研究測量的是什麼。必須明確：

對每個 profile *i*，從 listing universe 抽出 **N = 120** 筆候選房源，組成：

* **40 筆 feasible**（滿足全部硬性條件），且**必須包含 oracle 前 10 名**。若 oracle top-k 不在池中，測到的是 retrieval failure 而非 ranking failure。
* **80 筆 near-miss infeasible**：超預算 5–20%、少 1 房、或超過通勤上限 5–15 分鐘。

**為什麼必須混入不合格房源：** 若候選池全部合格，violation rate 依定義為 0，H1 無法檢驗。這是 v1 設計中未被察覺的邏輯漏洞。

其他控制：

* 每次呼叫**隨機打亂**候選順序（position effect）。
* 所有系統看到**完全相同**的候選池。
* Token 預算：120 listings × ~50 tokens ≈ 6k tokens，可放入 context。

**Commute visibility（新增的實驗臂）：**

* **Arm 1（primary）：** 候選記錄中**直接提供**已計算的 commute minutes。測的是純粹的 constraint following。
* **Arm 2（robustness，50 profiles 子樣本）：** 只提供地址，不提供 commute。測的是模型在必須自行推論地理時的表現。

若不做這個區分，「commute violation」會混淆 constraint-following 與 NYC 地理知識，違反率將無法解釋。v1 對此完全沒有立場。

### Step 5. Objective benchmark

**(a) Feasible set（weight-free，primary）**

```
F_i = { j : Rent_j <= Budget_i
          AND Bedrooms_j >= Bedrooms_i
          AND Commute_ij <= MaxCommute_i }
```

**(b) Dominance frontier（weight-free，primary）**

listing *j* 被 listing *j'* **strictly dominated**，若且唯若：

```
Rent_j'    <  Rent_j
Commute_ij' <  Commute_ij
Bedrooms_j' >= Bedrooms_j
```

（至少一項嚴格不等、其餘不劣。）Pareto frontier 為 F_i 中未被支配的集合。

**這是 v2 最重要的方法變更。** Dominance 不需要權重、不需要效用函數、不需要爭論偏好，且對「你的 utility function 是假設的」這個最可能的退稿理由免疫。

**(c) Weighted score（demoted to secondary/robustness only）**

```
Score_ij = -w1*Rent_j - w2*Commute_ij + w3*UnitMatch_ij + w4*TransitAccess_j
```

權重來自 profile 陳述的優先順序。**僅作為 robustness exhibit**，並須對 w 做 sensitivity grid（至少 3 組權重）。

> **明確聲明：** 這是 scenario-based relevance benchmark，不是經驗驗證的效用函數，不等同 consumer welfare。v1 已有此聲明，v2 保留並加強——但更重要的是，v2 的 primary outcomes 完全不依賴它。

### Step 6. Four recommendation systems

| System | Design | Research purpose |
| --- | --- | --- |
| **S0. Non-LLM IR baseline** | BM25 或 embedding retrieval + 簡單線性排序，identity-blind | **v1 缺漏。** 沒有這個 baseline，審查者無從判斷「LLM 表現差」還是「任務本身難」。Deterministic，每 profile 跑一次即可。 |
| **S1. Direct LLM** | 模型直接閱讀需求 + 候選池並推薦 top-5 | 一般模型的違反與遺漏 |
| **S2. Retrieval-grounded LLM** | 結構化 listing records + source attribution + 要求逐條引用條件 | grounding 是否改善品質 |
| **S3. Constraint-first** | 程式先過濾硬性條件，LLM 僅對 F_i 排序與解釋 | 較安全架構的代價與效益 |

**關於 S3 的誠實框架（v1 的邏輯問題）：** S3 的 violation rate 依建構為 0。這不是實證發現，是定義。真正的研究問題是：在硬性條件被保證之後，**soft ranking 的 opportunity loss 與 identity gap 是否仍然存在**。論文必須明說這一點，否則審查者會寫「你證明了 filter 會 filter」。

### Step 7. Execution grid

**Main grid：**

```
150 profiles x 4 identity conditions x 3 LLM systems x 3 replicates x 2 models
= 10,800 LLM calls
```

（S0 為 deterministic，另加 150 runs 作為參照，不進入 identity 對比。）

**Replicates 與 temperature（v1 完全未提，是實質漏洞）：**

* Temperature 設為模型預設（≈1.0），**每格 3 次 replicates**，以捕捉真實部署中的隨機性。
* Temperature = 0 只會得到每格單一抽樣，無法區分「模型偏誤」與「抽樣噪音」。
* Replicate-level variance 需單獨回報：cell 內變異若大於 identity 效果，該效果不可宣稱。

**Robustness arms（子樣本）：**

* Commute-hidden arm：50 profiles × 4 identity × S1 × 3 replicates
* Prompt-wording variants：3 種措辭 × 50 profiles
* Top-k 敏感度：k = 3, 5, 10
* Candidate pool density：N = 60 vs. 120

**成本估計（v1 未估）：** 主表約 10,800 calls × ~8k input tokens ≈ 86M input tokens，加 robustness arms，實際 API 成本約 **US$500–900**。這是真實預算項目，需事先確認。

**Model versioning：** 必須 pin 具體 model snapshot 與呼叫日期。API 模型會漂移，未記錄版本的 audit 無法重現。

---

## 5. Main outcome measures

### Pre-registered PRIMARY outcomes（三個，全部 weight-free）

**P1 — Confirmed hard-constraint violation rate**

```
ViolationRate_i = (# recommended listings violating a VERIFIED constraint) / (# recommended listings)
```

缺漏欄位另列為 **Unverifiable**，不計入 confirmed violation。分項回報：over-budget / under-bedroom / over-commute。

**P2 — Strict-dominance rate**

```
DominanceRate_i = (# recommended listings strictly dominated by some listing in F_i) / (# recommended listings)
```

同時回報 dominance 的**幅度**：被支配房源與其支配者之間的租金差（$）與通勤差（min）。

**P3 — Identity-conditioned cost gaps**

```
RentGap_i    = median(Rent of R_i ∩ F_i)      - median(Rent of oracle top-5)      [USD/month]
CommuteGap_i = median(Commute of R_i ∩ F_i)   - median(Commute of oracle top-5)   [minutes]
```

以 median 而非 min（v1 用 min，易受單一 tie 影響且不穩健）。identity 對比即為這兩個 gap 的 within-profile 差值。

> **注意 v1 的定義錯誤：** v1 的 `OpportunityLoss = max_{j in F} Score - max_{j in R} Score`，其中 R 可能包含不合格房源而分數偏高，導致在最該被偵測的情況下反而低估損失。v2 一律先取 `R_i ∩ F_i`。

### SECONDARY outcomes

**S1 — Mean percentile rank within feasible set**

推薦房源在 F_i 中的平均百分位（依 rent、依 commute 各算一次）。

> **為何取代 v1 的 Capture@k：** 當 |F_i| 有數百筆且多數近似等價時，Capture@5 對**任何**系統（包括完美系統）都趨近於零——它測的是集合大小，不是品質。若仍要回報 Capture@k，須加容忍帶（±$50 且 ±5 min 內視為命中）。

**S2 — Refusal / information-withholding rate**

模型拒答、迴避社區特徵、或以安全語句取代實質資訊的比例。

> **v1 把這件事放在「potential unexpected finding」。v2 將它升為正式測量的 outcome。** 「fair-housing guardrail 同時降低 steering 與扣留使用者需要的資訊」很可能是本研究最具發表價值的發現，不能靠碰運氣。

**S3 — Neighborhood exposure**

推薦房源所在 tract 的 ACS 中位所得、租金負擔、人口組成分佈。這是與既有 steering 文獻的可比接點。

**S4 — Tolerance-band Capture@k、NDCG@5、Precision@5**

所有 relevance labels 必須來自**事前定義**的條件與透明 benchmark，不得來自事後判斷或模型自評。

### TERTIARY / robustness only

**T1 — Weighted opportunity loss**

```
OpportunityLoss_i = max_{j in F_i} Score_ij - max_{j in R_i ∩ F_i} Score_ij
```

附 3 組權重的 sensitivity grid。**不作為 headline number。**

### Fairness gap（適用於上述任一 outcome Y）

```
FairnessGap = E[Y_i | Identity = A] - E[Y_i | Identity = B]
```

最重要的比較：**相同 profile、相同候選池、相同排序條件，僅改變身分線索**——即 within-profile matched contrast。

---

## 6. Statistical methodology

### 設計的正確描述

本設計是 **within-profile matched design**：同一 profile 的 4 個 identity 條件面對完全相同的候選池。因此 identity 效果是 matched contrast，不是跨組比較。v1 用 profile fixed effects 得到同樣的估計量，但沒有說明這一點，也因此選錯了推論方法。

### Primary inference: randomization inference

Identity 條件在 profile 內隨機指派，故 **permutation test** 是與設計相符的推論方法：

* 在 profile 內重新排列 identity label，重抽 10,000 次，建立 null distribution。
* 回報 permutation p-value 與 paired difference 的點估計。
* 理由：primary outcomes 多為零膨脹比例（多數 profile 的 violation rate = 0），n = 150 clusters 下，clustered OLS 的漸近性質不可靠。

### Secondary: fixed-effects regression（v1 的模型，保留為輔助）

**Model 1 — Identity disparities**

```
Y_igmr = alpha_i + beta * IdentityCue_g + lambda_m + delta_r + eps_igmr
```

i = profile；g = identity cue；m = model；r = replicate。alpha_i 為 profile FE，lambda_m 為 model FE，delta_r 為 replicate FE。SE clustered at profile level。

**Model 2 — Mitigation and interaction**

```
Y_igsmr = alpha_i
        + b1 * Grounded_s
        + b2 * ConstraintFirst_s
        + b3 * IdentityCue_g
        + b4 * (ConstraintFirst_s x IdentityCue_g)
        + lambda_m + delta_r + eps_igsmr
```

b2 = 架構對整體品質的效果；**b4 = 是否縮小身分間差距**（這是 RQ4 的核心係數）。

**Variance decomposition（新增）：** 以 mixed model 分解 between-profile / between-identity / within-cell (replicate) 變異。若 replicate 變異大於 identity 效果，該 identity 效果不得宣稱為系統性偏誤。

### Power / MDE

* 150 profiles，within-profile pairing，每格 3 replicates。
* 粗略估計：連續 outcome（RentGap in USD）的 MDE 約 0.2–0.25 SD of the paired difference；二元 outcome 的 MDE 約 8–10 個百分點。
* **必做：** 以 Week 4 的 pilot（20 profiles）資料做 **simulation-based power analysis**，再定案 profile 數。不要用經驗法則替代模擬。

### Statistical safeguards

* **Pre-registration（v1 沒有，v2 必做）：** 在跑任何主表之前於 OSF 或 AsPredicted 登錄 primary outcomes、樣本量、排除規則與分析模型。既有的 omission audit 與 hotel audit 都做了 pre-registration；對 audit 類論文，這實質提高接受率。
* Multiple testing：在每個 outcome family 內做 Benjamini–Hochberg 校正，family 定義寫入 pre-registration。
* 候選順序隨機化（已在 Step 4）。
* Prompt wording 與 name pool 輪替（robustness arms）。
* Model snapshot 與呼叫日期全部記錄。
* 明確聲明：**數千筆模型輸出不是數千個獨立的真實使用者**；有效樣本量是 profile 數（150），不是 call 數。

---

## 7. Expected outcomes

**E1 — High apparent relevance, high dominated-recommendation rate.** 推薦看起來合理、conventional ranking metrics 尚可，但相當比例的推薦房源被同一候選池中更便宜且通勤更短的房源嚴格支配。這個發現的力量在於它**不需要任何效用假設**。

**E2 — Constraint interaction penalty.** 同時包含 budget + bedrooms + commute 的請求，其違反率高於單一條件情境。屬既有 compositional constraint 文獻在本領域的量化，不宣稱為新現象。

**E3 — Identity effects show up in cost, not in accuracy.** 身分線索**未必**造成平均 ranking accuracy 差異，但可能顯著改變 RentGap、CommuteGap、neighborhood exposure 與 dominance rate。**「準確率相同但成本不同」本身就是本研究最重要的可能結果**，也是相對於既有 steering 文獻的實質推進。

**E4 — Voucher cue effect > name cue effect.** 顯性受保護屬性的效果預期大於姓名線索。若成立，對政策的意涵比 name-based audit 更直接。

**E5 — Constraint-first eliminates violations by construction, but soft-ranking disparity persists.** 若 b4 不顯著，代表**架構性防護無法解決排序層的不平等**——這對業界的意涵比「濾一濾就好」更重要，也更值得發表。

**E6 — The guardrail trade-off.** 加上 fair-housing 或安全限制後，模型可能同時降低明顯偏誤**與**提高 refusal / withholding rate、降低推薦多樣性、迴避對使用者確有用處的社區資訊。這個 trade-off 對 AI 公司與監管者都直接相關，並且在 v2 中是被測量的，不是被期待的。

---

## 8. Limitations

**這篇研究可以識別：** prompt 中的身分線索與推薦架構，如何改變模型在固定候選集合上的排序輸出，以及這些改變的可驗證成本。

**不能識別：**

* 真人偏好是否改變、使用者是否真的租下房子、市場成交效果、長期住宅福利。
* 部署中的產品行為。**這是 in-context ranking audit，不是 deployed-product audit。** 我們控制候選池，因此排除了 retrieval 階段；真實系統（Zillow / Redfin 的 AI 助理、含瀏覽的 ChatGPT）的 retrieval 失效不在測量範圍內。這個界線必須在 abstract 就講清楚。
* 完整的 Housing Connect eligibility（已將該資料源移除）。

**其他限制：**

* Synthetic profiles 不代表所有真實租屋者；request 措辭由研究者撰寫。
* RentCast 的 NYC 覆蓋偏向 MLS syndication 管道，可能低估 no-fee 與小房東物件（§3 的 coverage benchmark 會量化偏誤方向，但無法消除）。
* 紐約市不能推論全美；2606.06694 已顯示 steering 具城市異質性，「城市不是中性的測試單位」。
* 姓名線索同時攜帶 race 與 SES 訊號，即使使用已驗證的姓名資料集也無法完全分離。
* Weighted opportunity score 不等同任何使用者的實際福利（primary outcomes 已避免依賴它）。
* 法律意涵須謹慎：**steering 的證據不等於 FHA 責任成立**。論文應描述行為與其成本，並將法律論證限定為「這些行為屬於 FHA / NYCHRL 關注的行為類型」。

---

## 9. Execution plan（12 weeks，取代 v1 的 6 weeks）

v1 的六週排程在通勤路網未曾架設的情況下不可行。以下為現實排程；若必須壓縮，砍的是模型數（2 → 1）與 robustness arms，不是 pilot 與 pre-registration。

| Week | Work | Deliverable |
| --- | --- | --- |
| **1** | RentCast 抓取策略與 ToS 確認；listing universe v0；**r5py/OTP spike（成敗決策點）** | Listing dataset + routing go/no-go |
| **2** | Listing 清理、去重、geocode、tract join；coverage benchmark vs. ACS/NYCHVS | Cleaned dataset + coverage bias table |
| **3** | Commute matrix（4,000 × 3）；ACS tract 變數併入 | Enriched property dataset |
| **4** | 150 profiles + name pool（取自已發表資料集）；feasible set 與 dominance frontier 計算；**20-profile pilot** | Benchmark scenarios + pilot results |
| **5** | Pilot 分析 → simulation-based power analysis → 定案樣本量；**pre-registration 送出** | OSF pre-registration（時間戳） |
| **6** | 建置 S0 baseline 與 candidate pool sampler；prompt 模板定稿 | Evaluation harness |
| **7** | 建置 S1 / S2 / S3 三種架構；小規模 smoke test | Recommendation pipeline |
| **8** | 執行 main grid（10,800 calls，2 models） | Raw response corpus |
| **9** | 執行 robustness arms（commute-hidden、wording、top-k、pool density） | Robustness corpus |
| **10** | Primary analysis：permutation tests、FE models、variance decomposition | Main results |
| **11** | 視覺化；neighborhood exposure；refusal 分析；限制章節 | Figures + full results |
| **12** | Working paper 定稿；GitHub repo（code + aggregates + listing IDs） | Paper draft + reproducible portfolio |

---

## 10. Suggested paper structure

1. **Introduction** — AI 作為 high-stakes search 的中介；被遺漏的成本；為何住宅是唯一同時具備可驗證 ground truth 與法定公平制度的場景。
2. **Related work** — (a) housing steering audits（Liu et al. EAAMO '24；2606.06694）；(b) omission / coverage audits（2608.07069）；(c) industry ranking evaluation（2607.14835）；(d) constraint-following（2608.12426；SEQUOR）。**明確說明本研究位於四者交集，而非宣稱空白。**
3. **Data** — listings、通勤矩陣、tract 變數、coverage benchmark 與其偏誤。
4. **Benchmark construction** — feasible set、dominance frontier、以及為何 primary outcomes 刻意 weight-free。
5. **Audit design** — candidate pool 構成、identity 條件（含 voucher）、四種架構、commute-visibility 兩臂、replicates。
6. **Results I: constraint fidelity and forgone opportunity** — violation、dominance、cost gaps。
7. **Results II: identity-conditioned disparity** — permutation-based matched contrasts；exposure。
8. **Results III: mitigation and the guardrail trade-off** — b2、b4、refusal rate。
9. **Discussion** — 對 hiring、lending、healthcare、local discovery 等其他 high-stakes recommendation 的可移轉性；對平台設計與監管的意涵。
10. **Limitations and conclusion.**

**最終定位：** 這是一篇以住宅市場為場景的 **AI fairness、recommendation evaluation 與 high-stakes search** 論文，不是住宅政策論文。

### Venue strategy

| Stage | Target | 理由 |
| --- | --- | --- |
| **Primary** | **ACM FAccT** | 這個文獻實際所在之處；identity-conditioned harm + 可驗證成本 + mitigation 正中其核心。 |
| **Alt / parallel** | **AIES**（2606.06694 的去處）、**EAAMO**（Liu et al. 的去處） | 同一社群，對 solo author 較友善。 |
| **Journal（method-forward）** | **Computers, Environment and Urban Systems**；**EPB: Urban Analytics and City Science** | 計算方法 + 都市資料 + audit。 |
| **Journal（policy-forward）** | **Housing Policy Debate**；**Cityscape (HUD)** | FHA / NYCHRL 框架最強的落點；Cityscape 快且政策觸及廣。 |
| **Journal（metric-forward）** | **ACM TORS**；**Information Processing & Management** | 會要求 §Step 6 的 S0 non-LLM baseline——這也是加入它的另一個理由。 |
| **不建議** | *Journal of Housing Economics*、*Real Estate Economics* | 會以「synthetic profiles 不是行為、沒有市場結果」退稿，且依其標準是正確的。 |

建議路徑：**FAccT / AIES 先行 → 擴充版投 Housing Policy Debate 或 CEUS**。鑑於三篇鄰近論文在過去十週內出現，時效性是實質考量。

---

# Appendix — What changed from v1 to v2

## A. 致命層級的修正（不改就會被退稿）

| # | v1 | v2 | 為什麼 |
| --- | --- | --- | --- |
| 1 | Gap 宣稱「沒人測過 AI 漏掉什麼」 | 承認 2608.07069 已於 2026-08 在餐飲領域以完整市場普查做過 omission audit；重新定位到四條文獻的**交集** | v1 的 gap 已不存在。審查者會在三十秒內找到這篇。 |
| 2 | 未引用 Liu et al. (EAAMO '24) | 列為 RQ3 的 canonical prior | 168k prompts 的 GPT-4 steering audit 是本題的奠基文獻，遺漏極為顯眼。 |
| 3 | Headline metric 依賴手設權重的 `Score_ij` | **Strict-dominance rate 升為 primary**；weighted score 降為 tertiary robustness | Dominance 不需權重、不需效用假設。這一項變更就消除了最可能的退稿理由。 |
| 4 | 未定義 candidate pool | 明確規定 N=120，40 feasible（**含 oracle top-10**）+ 80 near-miss infeasible | v1 若候選池全部合格，violation rate 依定義為 0，H1 無法檢驗；若 oracle 不在池中，測到的是 retrieval failure 而非 ranking failure。這是 v1 的邏輯漏洞。 |
| 5 | 未決定是否提供 commute 給模型 | 新增 **commute-visible / commute-hidden 兩臂** | 不區分則 violation rate 混淆 constraint-following 與 NYC 地理知識，數字無法解釋。 |
| 6 | 未提 temperature 與 replicates | Temperature ≈ 1.0，**每格 3 replicates**，並回報 within-cell variance | v1 無法區分「模型偏誤」與「抽樣噪音」。 |
| 7 | 無 pre-registration | Week 5 送出 OSF / AsPredicted 登錄 | 鄰近的 omission audit 與 hotel audit 都做了；對 audit 論文實質提高接受率。 |

## B. 指標定義的修正

| # | v1 | v2 |
| --- | --- | --- |
| 8 | `OpportunityLoss = max_F Score − max_R Score` | 改為 `max_F Score − max_{R∩F} Score`。v1 的 R 可能含不合格但分數高的房源，會在最該偵測的情況下**低估**損失。 |
| 9 | `Capture@k`，分母 `min(k,\|F_i\|)` | 以 **mean percentile rank within F_i** 取代為 secondary primary；Capture@k 保留但加 ±$50 / ±5min 容忍帶。當 \|F_i\| 為數百且多數近似等價時，Capture@5 對完美系統也趨近 0，測的是集合大小。 |
| 10 | `RentGap` / `CommuteGap` 用 `min` | 改用 **median**，對 tie 與單一離群值穩健。 |
| 11 | Refusal / withholding 只出現在「potential unexpected finding」 | 升為正式 secondary outcome **S2** | 「guardrail 同時降低 steering 與扣留有用資訊」很可能是本研究最具發表價值的發現，不能靠碰運氣。 |

## C. 設計與可行性

| # | v1 | v2 |
| --- | --- | --- |
| 12 | 三種系統，無非-LLM 對照 | 新增 **S0：BM25 / embedding + 線性排序** baseline。缺此對照，審查者無從判斷是模型差還是任務難；TORS / IPM 會直接要求。 |
| 13 | S3 constraint-first 被當成待檢驗假設 | 明說 **violation rate = 0 是定義而非發現**；真正的問題移到 soft ranking 的 opportunity loss 與 identity gap 是否仍在 |
| 14 | 六個資料源 | **砍掉 LODES、Opportunity Insights、Housing Connect**，保留 RentCast + ACS + GTFS。三者皆不服務任何 RQ，只增加約一週工作量。 |
| 15 | 通勤：5–10 個目的地，未指定工具與時間 | **3 個目的地、固定平日 08:00、r5py 或 OTP**，Week 1 設 go/no-go spike，失敗退回 tract-to-tract matrix |
| 16 | 未檢查 RentCast 額度算術與覆蓋偏誤 | 算出 free tier = 50 req × 500 rec = 25,000 slots/月；**須以 city + pagination 抓取，不可逐 zip**；新增對 ACS / NYCHVS 的 **coverage benchmark 表**（NYC 租屋以 StreetEasy/REBNY 為主，MLS syndication 會低估 no-fee 與小房東物件——housing 期刊必問） |
| 17 | 承諾 GitHub 釋出資料 | 改為 code + derived aggregates + listing IDs；Week 1 先確認 ToS |
| 18 | 未估 API 成本 | 估 **US$500–900**，列為實際預算項目；並要求 pin model snapshot 與日期 |
| 19 | 六週排程 | **十二週**；壓縮時砍模型數與 robustness arms，不砍 pilot 與 pre-registration |

## D. 身分線索與統計推論

| # | v1 | v2 |
| --- | --- | --- |
| 20 | 「Identity cue A / B」未定義，姓名自訂 | 姓名**取自已發表的 name-perception 資料集**並回報 race × SES 兩維感知分數，正面回應 Gaddis 的 SES confound 批評 |
| 21 | 只有姓名一種管道 | 新增第四個條件：**housing voucher（CityFHEPS / Section 8）揭露**。紐約市 source-of-income 受法律保護、政策相關性最高，且它是**正當的實質限制**，可區分「合法調整」與「不當降級」——這是相對於既有 name-only audit 的實質推進，也是選 NYC 的正當理由。 |
| 22 | Clustered OLS 為主要推論 | **Permutation / randomization inference 為 primary**，FE OLS 降為 secondary。設計本質是 within-profile matched contrast；primary outcomes 為零膨脹比例，n=150 clusters 下 clustered OLS 的漸近性質不可靠。 |
| 23 | 250 profiles × 3 conditions，無 power 分析 | **150 profiles × 4 conditions × 3 replicates**；Week 4 pilot → **simulation-based power analysis** 再定案樣本量；新增 variance decomposition（若 replicate 變異 > identity 效果，不得宣稱該效果） |
| 24 | 未區分 in-context ranking 與 deployed product | 在 Limitations 與 abstract 明確聲明**這是 in-context ranking audit，排除了 retrieval 階段**，不宣稱關於 Zillow / Redfin / ChatGPT 部署行為的結論 |
| 25 | 未處理法律過度宣稱 | 明說 **steering 的證據 ≠ FHA 責任成立**；法律論證限定為「屬於 FHA / NYCHRL 關注的行為類型」 |

## E. 框架與新增問題

| # | 變更 |
| --- | --- |
| 26 | 標題與定位從「AI 漏掉什麼」改為「**被遺漏的成本，以美元與分鐘計，且分布不均**」。這是唯一沒有被既有文獻佔據的位置。 |
| 27 | H1b 明白標註為「既有 compositional constraint 文獻已知的現象；本研究貢獻是 domain-specific magnitude」，不宣稱發現。 |
| 28 | 新增 **RQ4**（mitigation 及其副作用），把 v1 混在 RQ3 裡的 mitigation 與「unexpected finding」中的 guardrail trade-off 合併為一個有正式假設的問題。 |
| 29 | 新增 **E3 的明確預期**：「準確率相同但成本不同」本身即為核心結果，而非 null finding。 |
| 30 | 新增 **venue strategy 表**：FAccT / AIES / EAAMO 先行，期刊分 method-forward（CEUS、EPB）／policy-forward（Housing Policy Debate、Cityscape）／metric-forward（TORS、IPM）；明列不建議投的 real estate economics 期刊及其理由。 |
