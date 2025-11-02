# Research Metrics Implementation - Sesuai Bab 2 & Bab 3

## 📋 Overview

Dokumen ini menjelaskan implementasi lengkap metrik penelitian yang sesuai dengan narasi Bab 2 (Evaluation Metrics) dan Bab 3 (Perancangan Sistem & Algoritma Q-Learning) untuk keperluan analisis di Bab 4.

## 🎯 Metrik yang Diimplementasikan

### 1. Metrik 2.1.4.1: Tingkat Keterlibatan Pengguna (User Engagement)

#### Model: `LoginActivityLog`
**Tujuan:** Melacak frekuensi login dan pola interaksi pengguna

**Fields:**
- `user`: User yang login
- `login_timestamp`: Waktu login
- `logout_timestamp`: Waktu logout
- `session_duration_seconds`: Durasi sesi
- `ip_address`: IP address
- `user_agent`: Browser/device info
- `activities_performed`: Aktivitas yang dilakukan

**Metrik yang Dihasilkan:**
- Total logins dalam periode tertentu
- Unique users yang login
- Average logins per user
- Daily login distribution
- Average session duration

**Cara Menggunakan:**
```python
from qlearning.analytics import AnalyticsService

# Get login metrics for last 30 days
login_metrics = AnalyticsService.get_login_frequency_metrics(days=30)
```

---

### 2. Metrik 2.1.4.2: Tingkat Keberhasilan/Akurasi (Success Rate/Accuracy)

#### Model: `AdaptationEffectivenessLog`
**Tujuan:** Mengukur efektivitas adaptasi sistem dengan membandingkan performa SEBELUM vs SESUDAH adaptasi

**Fields:**
- `user`: User yang mengalami adaptasi
- `adaptation_event`: Link ke ResponseToAdaptationLog
- `success_rate_before`: Success rate sebelum adaptasi (%)
- `avg_time_before`: Rata-rata waktu sebelum adaptasi
- `attempts_before`: Jumlah attempts sebelum
- `success_rate_after`: Success rate setelah adaptasi (%)
- `avg_time_after`: Rata-rata waktu setelah adaptasi
- `attempts_after`: Jumlah attempts setelah
- `success_rate_change`: Perubahan success rate (%)
- `time_efficiency_change`: Perubahan efisiensi waktu (%)
- `continued_session`: Apakah user melanjutkan sesi
- `attempts_until_quit`: Jumlah attempts sebelum quit
- `measurement_window_days`: Window pengukuran (default 7 hari)

**Metrik yang Dihasilkan:**
- Total adaptations
- Average success rate improvement
- Average time efficiency improvement
- Continuation rate (% user yang melanjutkan setelah adaptasi)
- Positive/Negative/Neutral adaptations count

**Cara Menggunakan:**
```python
# Get adaptation effectiveness metrics
adaptation_metrics = AnalyticsService.get_adaptation_effectiveness_metrics()
```

---

### 3. Metrik 2.1.4.3: Respon Terhadap Adaptasi (Response to Adaptation)

#### Model: `UserSurveyResponse`
**Tujuan:** Mengumpulkan feedback kualitatif dan kuantitatif dari pengguna

**Fields:**
- `user`: User yang memberikan feedback
- `survey_type`: Jenis survey (post_adaptation, session_end, weekly_feedback, difficulty_feedback)
- `satisfaction_rating`: Rating kepuasan (1-5)
- `difficulty_rating`: Rating kesesuaian difficulty (1-5)
- `engagement_rating`: Rating engagement (1-5)
- `feedback_text`: Feedback teks terbuka
- `would_continue`: Apakah akan melanjutkan menggunakan sistem
- `adaptation_helpful`: Apakah adaptasi membantu
- `context_data`: Konteks saat survey diambil

**Metrik yang Dihasilkan:**
- Total survey responses
- Average satisfaction rating
- Average difficulty rating
- Average engagement rating
- Would continue percentage
- Adaptation helpful percentage
- Satisfaction distribution
- Recent feedback

**Cara Menggunakan:**
```python
# Get survey feedback summary
survey_metrics = AnalyticsService.get_survey_feedback_summary()
```

**Cara Membuat Survey:**
```python
from qlearning.models import UserSurveyResponse

UserSurveyResponse.objects.create(
    user=request.user,
    survey_type='post_adaptation',
    satisfaction_rating=4,
    difficulty_rating=4,
    engagement_rating=5,
    feedback_text="Sistem adaptasinya bagus!",
    would_continue=True,
    adaptation_helpful=True,
    context_data={
        'level': 'intermediate',
        'difficulty': 'medium',
        'session_duration': 300
    }
)
```

---

### 4. Metrik 2.1.4.4: Kinerja Algoritma Q-Learning

#### Model: `QLearningDecisionLog`
**Tujuan:** Melacak proses decision-making Q-Learning (Exploration vs Exploitation)

**Fields:**
- `user`: User
- `state_hash`: Current state
- `decision_type`: 'exploration' atau 'exploitation'
- `epsilon_value`: Nilai epsilon saat keputusan dibuat
- `action_chosen`: Action yang dipilih
- `q_value_chosen`: Q-value dari action yang dipilih
- `best_q_value`: Q-value terbaik yang tersedia
- `all_q_values`: Semua Q-values untuk state ini
- `is_optimal`: Apakah action optimal yang dipilih

**Metrik yang Dihasilkan:**
- Total decisions
- Exploration rate (%)
- Exploitation rate (%)
- Optimal action rate (%)
- Average epsilon value
- Q-value trend over time
- Exploration vs Exploitation distribution

**Cara Menggunakan:**
```python
# Get Q-Learning evolution metrics
qlearning_evolution = AnalyticsService.get_qlearning_evolution_metrics()
```

**Cara Logging Decision:**
```python
from qlearning.models import QLearningDecisionLog

QLearningDecisionLog.objects.create(
    user=user,
    state_hash=state_hash,
    decision_type='exploitation',  # atau 'exploration'
    epsilon_value=0.15,
    action_chosen='medium',
    q_value_chosen=0.85,
    best_q_value=0.85,
    all_q_values={'easy': 0.70, 'medium': 0.85, 'hard': 0.60},
    is_optimal=True
)
```

---

### 5. Bab 3.1.1: State Distribution (Student Levels)

#### Menggunakan: `StudentProfile` model yang sudah ada
**Tujuan:** Melihat distribusi siswa across states (Beginner, Intermediate, Advanced, Expert)

**Metrik yang Dihasilkan:**
- Total students
- State distribution (count per level)
- State percentages
- Average time in each state

**Cara Menggunakan:**
```python
# Get state distribution
state_distribution = AnalyticsService.get_state_distribution_metrics()
```

---

## 📊 Admin Dashboard

### Lokasi
`/dashboards/admin/`

### Sections Baru yang Ditambahkan

#### 1. **2.1.4.1 - Login Frequency & Engagement Trends**
- Total Logins (30 days)
- Avg Logins/User
- Avg Session Duration
- Engagement Trend

#### 2. **2.1.4.2 - Adaptation Effectiveness (Before vs After)**
- Total Adaptations
- Success Rate Δ (Delta/Change)
- Time Efficiency Δ
- Continuation Rate
- Adaptation Impact Distribution (Positive/Neutral/Negative)

#### 3. **2.1.4.3 - Survey & User Feedback**
- Survey Responses
- Avg Satisfaction
- Would Continue %
- Adaptation Helpful %
- Recent User Feedback Table

#### 4. **2.1.4.4 - Q-Learning Evolution & Decision Making**
- Total Decisions
- Exploration Rate
- Exploitation Rate
- Optimal Action Rate
- Q-Value Evolution Chart (Line chart showing Q-values over time)

#### 5. **Bab 3.1.1 - State Distribution**
- Student Distribution Across States
- State Percentages
- Bar Chart Visualization

---

## 📈 Visualizations

### 1. Q-Value Evolution Chart
**Type:** Line Chart (Chart.js)
**Data:** Q-values and Rewards over time
**Purpose:** Menunjukkan bagaimana Q-Learning "belajar" dan nilai Q converge

### 2. State Distribution Chart
**Type:** Bar Chart (Chart.js)
**Data:** Number of students per level
**Purpose:** Menunjukkan distribusi siswa across states

---

## 🔧 Analytics Management

### Admin Panel Links
Semua model baru dapat diakses melalui Django Admin:

1. **Survey Responses** - `/admin/qlearning/usersurveyresponse/`
2. **Login Activity** - `/admin/qlearning/loginactivitylog/`
3. **Adaptation Effectiveness** - `/admin/qlearning/adaptationeffectivenesslog/`
4. **Q-Learning Decisions** - `/admin/qlearning/qlearningdecisionlog/`

### Export Functionality
Semua data dapat di-export ke CSV:

```python
from qlearning.analytics import AnalyticsService

# Export survey data
output, fieldnames, filename = AnalyticsService.export_logs_to_csv('surveys')

# Export login activity
output, fieldnames, filename = AnalyticsService.export_logs_to_csv('login_activity')

# Export adaptation effectiveness
output, fieldnames, filename = AnalyticsService.export_logs_to_csv('adaptation_effectiveness')

# Export Q-Learning decisions
output, fieldnames, filename = AnalyticsService.export_logs_to_csv('qlearning_decisions')
```

---

## 🎓 Penggunaan untuk Penelitian (Bab 4)

### Data yang Tersedia untuk Analisis

#### 1. **Analisis Keterlibatan Pengguna**
```python
# Get comprehensive engagement data
login_metrics = AnalyticsService.get_login_frequency_metrics(days=30)

# Analisis:
# - Frekuensi login menunjukkan minat berkelanjutan
# - Session duration menunjukkan engagement depth
# - Daily distribution menunjukkan pola usage
```

#### 2. **Analisis Efektivitas Adaptasi**
```python
# Get adaptation effectiveness
adaptation_metrics = AnalyticsService.get_adaptation_effectiveness_metrics()

# Analisis:
# - Success rate improvement menunjukkan efektivitas adaptasi
# - Continuation rate menunjukkan user acceptance
# - Positive vs negative adaptations menunjukkan accuracy sistem
```

#### 3. **Analisis Feedback Pengguna**
```python
# Get survey feedback
survey_metrics = AnalyticsService.get_survey_feedback_summary()

# Analisis:
# - Satisfaction rating menunjukkan user satisfaction
# - Adaptation helpful % menunjukkan perceived usefulness
# - Qualitative feedback memberikan insights mendalam
```

#### 4. **Analisis Q-Learning Performance**
```python
# Get Q-Learning evolution
qlearning_evolution = AnalyticsService.get_qlearning_evolution_metrics()

# Analisis:
# - Exploration vs exploitation menunjukkan learning strategy
# - Optimal action rate menunjukkan learning effectiveness
# - Q-value trend menunjukkan convergence
```

---

## 📝 Cara Menggunakan Data untuk Bab 4

### Step 1: Collect Data
Jalankan sistem dengan siswa real selama periode penelitian (misal 4 minggu)

### Step 2: Export Data
```bash
# Login ke admin dashboard
# Klik Export buttons untuk setiap metrik
# Data akan di-download sebagai CSV
```

### Step 3: Analyze Data
```python
import pandas as pd

# Load exported data
surveys = pd.read_csv('surveys_logs_20250129.csv')
adaptations = pd.read_csv('adaptation_effectiveness_logs_20250129.csv')
decisions = pd.read_csv('qlearning_decisions_logs_20250129.csv')

# Perform statistical analysis
# - Descriptive statistics
# - Correlation analysis
# - Hypothesis testing
# - Visualization
```

### Step 4: Report Findings
Gunakan metrik yang telah dikumpulkan untuk menjawab:

1. **RQ1:** Bagaimana tingkat keterlibatan pengguna?
   - Data: `login_frequency`, `engagement_logs`

2. **RQ2:** Seberapa efektif adaptasi sistem?
   - Data: `adaptation_effectiveness`, `success_rate_change`

3. **RQ3:** Bagaimana respon pengguna terhadap adaptasi?
   - Data: `survey_feedback`, `continuation_rate`

4. **RQ4:** Bagaimana kinerja algoritma Q-Learning?
   - Data: `qlearning_evolution`, `optimal_action_rate`

---

## 🚀 Next Steps

### Untuk Mengumpulkan Data Lengkap:

1. **Integrate Login Tracking**
   - Tambahkan logging di `accounts/views.py` saat login/logout
   
2. **Integrate Adaptation Logging**
   - Tambahkan logging di Q-Learning agent saat melakukan adaptasi
   
3. **Create Survey Forms**
   - Buat form survey untuk siswa
   - Tampilkan setelah adaptasi atau end of session
   
4. **Integrate Decision Logging**
   - Tambahkan logging di Q-Learning agent saat membuat keputusan

### Example Integration:

```python
# In qlearning/agent.py
from qlearning.models import QLearningDecisionLog

def choose_action(self, state, epsilon):
    # ... existing code ...
    
    # Log the decision
    QLearningDecisionLog.objects.create(
        user=self.user,
        state_hash=state_hash,
        decision_type='exploration' if random.random() < epsilon else 'exploitation',
        epsilon_value=epsilon,
        action_chosen=action,
        q_value_chosen=q_values[action],
        best_q_value=max(q_values.values()),
        all_q_values=q_values,
        is_optimal=(action == max(q_values, key=q_values.get))
    )
    
    return action
```

---

## ✅ Checklist Implementasi

- [x] Model `UserSurveyResponse` created
- [x] Model `LoginActivityLog` created
- [x] Model `AdaptationEffectivenessLog` created
- [x] Model `QLearningDecisionLog` created
- [x] Analytics methods implemented
- [x] Admin dashboard updated
- [x] Visualizations added (Chart.js)
- [x] Export functionality added
- [x] Admin panel registered
- [x] Documentation created

## 🔄 Checklist untuk Data Collection

- [ ] Integrate login/logout tracking
- [ ] Integrate adaptation logging
- [ ] Create survey forms
- [ ] Integrate Q-Learning decision logging
- [ ] Test with real users
- [ ] Collect data for research period
- [ ] Export and analyze data
- [ ] Write Bab 4 based on findings

---

## 📞 Support

Jika ada pertanyaan atau butuh bantuan implementasi lebih lanjut, silakan hubungi developer atau lihat dokumentasi Django dan Chart.js.

---

**Last Updated:** 2025-01-29
**Version:** 1.0
**Status:** ✅ Fully Implemented
