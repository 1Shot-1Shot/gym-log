from flask import Flask, render_template_string, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = "gym.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            weight REAL NOT NULL,
            reps INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

MACHINES = {
    # --- חזה (PUSH) ---
    "bench_press": {
        "name": "לחיצת חזה מוט (שטוח)", "category": "חזה", "type": "free", "workout": "push",
        "muscle": "חזה גדול, יד אחורית, כתף קדמית", 
        "guide": "שכוב על הספסל, אחוז מוט ברוחב כתפיים, הורד לחזה ודחף למעלה.", 
        "video_url": "https://www.youtube.com/embed/rT7DgCr-3pg",
        "anatomy_img": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=300&auto=format&fit=crop"
    },
    "incline_bench": {
        "name": "לחיצת חזה עליון במוט/דאמבלים", "category": "חזה", "type": "free", "workout": "push",
        "muscle": "חזה עליון, כתף קדמית", 
        "guide": "ספסל בשיפוע 30-45 מעלות, דחף מעלה בשליטה.", 
        "video_url": "https://www.youtube.com/embed/SrqNv9yexnY",
        "anatomy_img": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=300&auto=format&fit=crop"
    },
    "chest_fly": {
        "name": "פרפר / פרפר בכבלים", "category": "חזה", "type": "machine", "workout": "push",
        "muscle": "חזה מבודד", 
        "guide": "קירוב ידיים במרפקים מעט כפופים וקבועים.", 
        "video_url": "https://www.youtube.com/embed/Z57CtZuYxug",
        "anatomy_img": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=300&auto=format&fit=crop"
    },

    # --- כתפיים (PUSH) ---
    "overhead_press": {
        "name": "לחיצת כתפיים במוט/דאמבלים", "category": "כתפיים", "type": "free", "workout": "push",
        "muscle": "כתף קדמית ואמצעית", 
        "guide": "דחף את המשקל מעל הראש בעמידה או ישיבה.", 
        "video_url": "https://www.youtube.com/embed/2yjwXT8jOPw",
        "anatomy_img": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=300&auto=format&fit=crop"
    },
    "lateral_raise": {
        "name": "הרחקת כתפיים לצדדים", "category": "כתפיים", "type": "free", "workout": "push",
        "muscle": "כתף אמצעית", 
        "guide": "הרם משקולות לצדדים בגובה הכתפיים.", 
        "video_url": "https://www.youtube.com/embed/3VcKaXpzqRo",
        "anatomy_img": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=300&auto=format&fit=crop"
    },

    # --- יד אחורית (PUSH) ---
    "triceps_pushdown": {
        "name": "פשיטת מרפקים בפולי (חבל/מוט)", "category": "ידיים", "type": "machine", "workout": "push",
        "muscle": "יד אחורית (Triceps)", 
        "guide": "יישר מרפקים כלפי מטה כשהם צמודים לגוף.", 
        "video_url": "https://www.youtube.com/embed/2-w9bqa5t1s",
        "anatomy_img": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=300&auto=format&fit=crop"
    },

    # --- גב (PULL) ---
    "pullups": {
        "name": "מתח (Pull-ups)", "category": "גב", "type": "free", "workout": "pull",
        "muscle": "רחב גבי (Lats), יד קדמית", 
        "guide": "אחיזה רחבה, משוך חזה אל המוט.", 
        "video_url": "https://www.youtube.com/embed/eGo4IYlbE5g",
        "anatomy_img": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=300&auto=format&fit=crop"
    },
    "lat_pulldown": {
        "name": "פולי עליון רחב", "category": "גב", "type": "machine", "workout": "pull",
        "muscle": "רחב גבי", 
        "guide": "משוך את המוט אל החזה העליון.", 
        "video_url": "https://www.youtube.com/embed/CAwf7n6Luuc",
        "anatomy_img": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=300&auto=format&fit=crop"
    },
    "barbell_row": {
        "name": "חתירה במוט / דאמבלים", "category": "גב", "type": "free", "workout": "pull",
        "muscle": "גב אמצעי, רחב גבי", 
        "guide": "התכופף עם גב ישר ומשוך לכיוון הטבור.", 
        "video_url": "https://www.youtube.com/embed/GWD8lV23IB4",
        "anatomy_img": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=300&auto=format&fit=crop"
    },

    # --- יד קדמית (PULL) ---
    "biceps_curl": {
        "name": "כפיפת מרפקים במוט / דאמבלים", "category": "ידיים", "type": "free", "workout": "pull",
        "muscle": "יד קדמית (Biceps)", 
        "guide": "כופף מרפקים והרם משקל בלי להזיז את הגב.", 
        "video_url": "https://www.youtube.com/embed/ykJmrZ5v0Oo",
        "anatomy_img": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=300&auto=format&fit=crop"
    },

    # --- רגליים (LEGS) ---
    "squat": {
        "name": "סקוואט חופשי במוט", "category": "רגליים", "type": "free", "workout": "legs",
        "muscle": "ארבע-ראשי, ישבן", 
        "guide": "רד לעומק בשליטה כשהגב ישר ודחף חזרה.", 
        "video_url": "https://www.youtube.com/embed/ultWZbUMPL8",
        "anatomy_img": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=300&auto=format&fit=crop"
    },
    "leg_press": {
        "name": "לחיצת רגליים במכונה", "category": "רגליים", "type": "machine", "workout": "legs",
        "muscle": "ארבע-ראשי וישבן", 
        "guide": "דחף פלטפורמה בלי לנעול ברכיים לחלוטין.", 
        "video_url": "https://www.youtube.com/embed/IZxyjW7MPJQ",
        "anatomy_img": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=300&auto=format&fit=crop"
    },
    "leg_curl": {
        "name": "כפיפת ברכיים (ירך אחורית)", "category": "רגליים", "type": "machine", "workout": "legs",
        "muscle": "המסטרינג (Hamstrings)", 
        "guide": "כופף את הרגליים לאחור כנגד ההתנגדות.", 
        "video_url": "https://www.youtube.com/embed/1T5Kjn7x91w",
        "anatomy_img": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=300&auto=format&fit=crop"
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GymLog Pro</title>
    <style>
        :root {
            --bg-color: #0f1115;
            --card-bg: #1a1d24;
            --text-color: #ffffff;
            --subtext: #9ca3af;
            --accent: #10b981;
            --accent-hover: #059669;
            --border: #2d3748;
            --input-bg: #222631;
        }
        .light-mode {
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
            --text-color: #1f2937;
            --subtext: #4b5563;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --border: #e5e7eb;
            --input-bg: #f9fafb;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; }
        body { background-color: var(--bg-color); color: var(--text-color); padding: 15px; transition: background 0.3s; padding-bottom: 50px; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; background: var(--card-bg); padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border); }
        h1 { color: var(--accent); font-size: 20px; }
        
        .nav-tabs { display: flex; gap: 8px; margin-bottom: 15px; }
        .tab-btn { flex: 1; background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 10px; border-radius: 10px; font-size: 14px; cursor: pointer; font-weight: bold; text-align: center; }
        .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

        .section-view { display: none; }
        .section-view.active { display: block; }

        .controls { display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px; }
        input.search-box { width: 100%; padding: 12px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 10px; font-size: 15px; }
        
        .filters { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 5px; }
        .filter-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer; white-space: nowrap; }
        .filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); font-weight: bold; }

        .machine-card { background-color: var(--card-bg); border-radius: 14px; padding: 16px; margin-bottom: 15px; border: 1px solid var(--border); position: relative; }
        .machine-card.completed { border-color: var(--accent); opacity: 0.7; }
        
        .card-header { display: flex; justify-content: space-between; align-items: center; }
        .machine-title { font-size: 18px; font-weight: bold; color: var(--accent); }
        
        .done-checkbox { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: bold; cursor: pointer; background: var(--input-bg); padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border); }
        .done-checkbox input { width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer; }

        .badge-group { display: flex; gap: 5px; margin-top: 5px; }
        .badge { display: inline-block; background: var(--input-bg); color: var(--subtext); padding: 3px 8px; border-radius: 6px; font-size: 11px; border: 1px solid var(--border); }
        
        .section-title { font-size: 12px; color: var(--subtext); margin-top: 10px; }
        .muscle-info { font-size: 14px; color: var(--text-color); margin-bottom: 6px; }
        .guide-info { font-size: 13px; color: var(--subtext); line-height: 1.4; margin-bottom: 10px; }
        iframe { width: 100%; height: 170px; border-radius: 8px; border: none; margin-bottom: 10px; margin-top: 8px; }
        
        .form-group { display: flex; gap: 8px; margin-top: 10px; }
        input[type="number"] { flex: 1; padding: 10px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 8px; font-size: 14px; text-align: center; }
        button.save-btn { background-color: var(--accent); color: #fff; border: none; padding: 10px 16px; font-weight: bold; border-radius: 8px; cursor: pointer; }
        
        .history-box { margin-top: 12px; background: var(--input-bg); padding: 10px; border-radius: 8px; font-size: 12px; max-height: 110px; overflow-y: auto; color: var(--subtext); border: 1px solid var(--border); }
        .history-item { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 4px 0; }

        .program-selector { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 15px; }
        .timer-bar { background: var(--card-bg); border: 1px solid var(--border); padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <header>
        <h1>🏋️‍♂️ GymLog Pro</h1>
        <button class="tab-btn" onclick="toggleTheme()" style="padding: 6px 12px; width: auto;">🌓 תצוגה</button>
    </header>

    <!-- טיימר מנוחה מהיר -->
    <div class="timer-bar">
        <span>⏱️ מנוחה בין סטים: <strong id="timerClock">00:00</strong></span>
        <div>
            <button class="filter-btn" onclick="startTimer(90)">90 שניות</button>
            <button class="filter-btn" onclick="startTimer(120)">2 דקות</button>
        </div>
    </div>

    <!-- ניווט ראשית -->
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('workoutTab', this)">📋 תוכנית אימון</button>
        <button class="tab-btn" onclick="switchTab('allExercisesTab', this)">💪 כל התרגילים</button>
    </div>

    <!-- 1. טאב תוכנית אימון מובנית עם סימון V -->
    <div id="workoutTab" class="section-view active">
        <div class="program-selector">
            <button class="filter-btn active" onclick="selectProgram('push', this)">🔥 דחיפה (Push)</button>
            <button class="filter-btn" onclick="selectProgram('pull', this)">⚡ משיכה (Pull)</button>
            <button class="filter-btn" onclick="selectProgram('legs', this)">🦵 רגליים (Legs)</button>
        </div>

        <div id="programList">
            {% for id, m in machines.items() %}
            <div class="machine-card program-card" data-workout="{{ m.workout }}" id="card-{{ id }}">
                <div class="card-header">
                    <div class="machine-title">{{ m.name }}</div>
                    <label class="done-checkbox">
                        <input type="checkbox" onchange="toggleDone('{{ id }}', this)">
                        בוצע בV
                    </label>
                </div>

                <div class="badge-group">
                    <span class="badge">{{ m.category }}</span>
                    <span class="badge">{% if m.type == 'free' %}משקל חופשי{% else %}מכונה{% endif %}</span>
                </div>
                
                <div class="section-title">שריר מרכזי:</div>
                <div class="muscle-info">{{ m.muscle }}</div>
                
                <iframe src="{{ m.video_url }}" allowfullscreen></iframe>
                
                <form onsubmit="saveWeight(event, '{{ id }}')">
                    <div class="form-group">
                        <input type="number" step="0.5" id="weight-{{ id }}" placeholder="משקל (ק״ג)" required>
                        <input type="number" id="reps-{{ id }}" placeholder="חזרות" required>
                        <button type="submit" class="save-btn">שמור</button>
                    </div>
                </form>

                <div class="history-box" id="history-{{ id }}">
                    {% if history[id] %}
                        {% for h in history[id] %}
                        <div class="history-item">
                            <span><strong>{{ h[0] }} ק״ג</strong> x {{ h[1] }} חזרות</span>
                            <span>{{ h[2][:16] }}</span>
                        </div>
                        {% endfor %}
                    {% else %}
                        <span>טרם נרשמו אימונים לתרגיל זה</span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- 2. טאב כל התרגילים (חיפוש וסינון חופשי) -->
    <div id="allExercisesTab" class="section-view">
        <div class="controls">
            <input type="text" id="searchBox" class="search-box" placeholder="חפש תרגיל..." oninput="filterAllMachines()">
            <div class="filters">
                <button class="filter-btn active" onclick="setCategory('הכל', this)">הכל</button>
                <button class="filter-btn" onclick="setCategory('חזה', this)">חזה</button>
                <button class="filter-btn" onclick="setCategory('גב', this)">גב</button>
                <button class="filter-btn" onclick="setCategory('כתפיים', this)">כתפיים</button>
                <button class="filter-btn" onclick="setCategory('רגליים', this)">רגליים</button>
                <button class="filter-btn" onclick="setCategory('ידיים', this)">ידיים</button>
            </div>
        </div>

        <div id="allList">
            {% for id, m in machines.items() %}
            <div class="machine-card all-card" data-category="{{ m.category }}" data-name="{{ m.name }}">
                <div class="machine-title">{{ m.name }}</div>
                <div class="badge-group">
                    <span class="badge">{{ m.category }}</span>
                    <span class="badge">{% if m.type == 'free' %}משקל חופשי{% else %}מכונה{% endif %}</span>
                </div>
                
                <div class="section-title">שריר מרכזי:</div>
                <div class="muscle-info">{{ m.muscle }}</div>
                <div class="guide-info">{{ m.guide }}</div>
                
                <iframe src="{{ m.video_url }}" allowfullscreen></iframe>
                
                <form onsubmit="saveWeight(event, '{{ id }}-all')">
                    <div class="form-group">
                        <input type="number" step="0.5" id="weight-{{ id }}-all" placeholder="משקל (ק״ג)" required>
                        <input type="number" id="reps-{{ id }}-all" placeholder="חזרות" required>
                        <button type="submit" class="save-btn">שמור</button>
                    </div>
                </form>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        let currentProgram = 'push';
        let currentCategory = 'הכל';

        function toggleTheme() {
            document.body.classList.toggle('light-mode');
        }

        function switchTab(tabId, btn) {
            document.querySelectorAll('.section-view').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-tabs .tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }

        function selectProgram(prog, btn) {
            currentProgram = prog;
            document.querySelectorAll('.program-selector .filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.program-card').forEach(card => {
                if (card.getAttribute('data-workout') === prog) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function toggleDone(id, checkbox) {
            const card = document.getElementById(`card-${id}`);
            if (checkbox.checked) {
                card.classList.add('completed');
            } else {
                card.classList.remove('completed');
            }
        }

        function setCategory(cat, btn) {
            currentCategory = cat;
            document.querySelectorAll('.filters .filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterAllMachines();
        }

        function filterAllMachines() {
            const query = document.getElementById('searchBox').value.toLowerCase();
            document.querySelectorAll('.all-card').forEach(card => {
                const name = card.getAttribute('data-name').toLowerCase();
                const cat = card.getAttribute('data-category');
                const matchesSearch = name.includes(query);
                const matchesCat = (currentCategory === 'הכל' || cat === currentCategory);

                if (matchesSearch && matchesCat) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        async function saveWeight(e, inputSuffix) {
            e.preventDefault();
            const cleanId = inputSuffix.replace('-all', '');
            const weight = document.getElementById(`weight-${inputSuffix}`).value;
            const reps = document.getElementById(`reps-${inputSuffix}`).value;

            const res = await fetch('/api/add_weight', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({machine_id: cleanId, weight: parseFloat(weight), reps: parseInt(reps)})
            });

            if(res.ok) {
                const data = await res.json();
                const historyBox = document.getElementById(`history-${cleanId}`);
                
                if(historyBox && historyBox.innerHTML.includes('טרם נרשמו')) {
                    historyBox.innerHTML = '';
                }

                if(historyBox) {
                    const newItem = document.createElement('div');
                    newItem.className = 'history-item';
                    newItem.innerHTML = `<span><strong>${data.weight} ק״ג</strong> x ${data.reps} חזרות</span><span>${data.date.substring(0,16)}</span>`;
                    historyBox.prepend(newItem);
                }

                document.getElementById(`weight-${inputSuffix}`).value = '';
                document.getElementById(`reps-${inputSuffix}`).value = '';
                alert('נשמר בהצלחה! 💪');
            }
        }

        let countdown;
        function startTimer(seconds) {
            clearInterval(countdown);
            let timeLeft = seconds;
            const display = document.getElementById('timerClock');
            
            countdown = setInterval(() => {
                let m = Math.floor(timeLeft / 60);
                let s = timeLeft % 60;
                display.innerText = `${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
                if (timeLeft <= 0) {
                    clearInterval(countdown);
                    alert('נגמרה המנוחה! קח סט חדש 🏋️‍♂️');
                }
                timeLeft--;
            }, 1000);
        }

        // טעינה ראשונית של תוכנית PUSH
        selectProgram('push', document.querySelector('.program-selector .filter-btn'));
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT machine_id, weight, reps, date FROM weights ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    history = {}
    for r in rows:
        m_id, w, reps, d = r[0], r[1], r[2], r[3]
        if m_id not in history:
            history[m_id] = []
        history[m_id].append((w, reps, d))

    return render_template_string(HTML_TEMPLATE, machines=MACHINES, history=history)

@app.route('/api/add_weight', methods=['POST'])
def add_weight():
    data = request.json
    machine_id = data.get('machine_id')
    weight = data.get('weight')
    reps = data.get('reps')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO weights (machine_id, weight, reps) VALUES (?, ?, ?)", (machine_id, weight, reps))
    conn.commit()
    cursor.execute("SELECT datetime('now', '+3 hours')")
    date_str = cursor.fetchone()[0]
    conn.close()

    return jsonify({"success": True, "weight": weight, "reps": reps, "date": date_str})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
