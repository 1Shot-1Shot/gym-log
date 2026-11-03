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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coins INTEGER DEFAULT 0,
            avatar_item TEXT DEFAULT 'standard',
            share_status INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

MACHINES = {
    "bench_press": {"name": "לחיצת חזה מוט (שטוח)", "category": "חזה", "type": "free", "workout": "push", "muscle": "חזה גדול, יד אחורית", "guide": "שכוב על הספסל, אחוז מוט ודחף למעלה.", "video_url": "https://www.youtube.com/embed/rT7DgCr-3pg", "anatomy_img": "https://exrx.net/Muscles/PectoralisSternal.jpg"},
    "incline_bench": {"name": "לחיצת חזה עליון", "category": "חזה", "type": "free", "workout": "push", "muscle": "חזה עליון", "guide": "ספסל בשיפוע 30-45 מעלות.", "video_url": "https://www.youtube.com/embed/SrqNv9yexnY", "anatomy_img": "https://exrx.net/Muscles/PectoralisClavicular.jpg"},
    "overhead_press": {"name": "לחיצת כתפיים במוט", "category": "כתפיים", "type": "free", "workout": "push", "muscle": "כתף קדמית", "guide": "דחף מוט מעל הראש בעמידה.", "video_url": "https://www.youtube.com/embed/2yjwXT8jOPw", "anatomy_img": "https://exrx.net/Muscles/DeltoidAnterior.jpg"},
    
    "pullups": {"name": "מתח (Pull-ups)", "category": "גב", "type": "free", "workout": "pull", "muscle": "רחב גבי ויד קדמית", "guide": "משוך חזה אל המוט.", "video_url": "https://www.youtube.com/embed/eGo4IYlbE5g", "anatomy_img": "https://exrx.net/Muscles/LatissimusDorsi.jpg"},
    "lat_pulldown": {"name": "פולי עליון רחב", "category": "גב", "type": "machine", "workout": "pull", "muscle": "רחב גבי", "guide": "משוך מוט לחזה.", "video_url": "https://www.youtube.com/embed/CAwf7n6Luuc", "anatomy_img": "https://exrx.net/Muscles/LatissimusDorsi.jpg"},
    "barbell_row": {"name": "חתירה במוט", "category": "גב", "type": "free", "workout": "pull", "muscle": "גב אמצעי", "guide": "התכופף ומשוך מוט לבטן.", "video_url": "https://www.youtube.com/embed/GWD8lV23IB4", "anatomy_img": "https://exrx.net/Muscles/TrapeziusMiddle.jpg"},

    "squat": {"name": "סקוואט חופשי", "category": "רגליים", "type": "free", "workout": "legs", "muscle": "ארבע-ראשי וישבן", "guide": "רד לעומק בשליטה.", "video_url": "https://www.youtube.com/embed/ultWZbUMPL8", "anatomy_img": "https://exrx.net/Muscles/Quadriceps.jpg"},
    "leg_press": {"name": "לחיצת רגליים", "category": "רגליים", "type": "machine", "workout": "legs", "muscle": "ארבע-ראשי", "guide": "דחף משקל בפלטפורמה.", "video_url": "https://www.youtube.com/embed/IZxyjW7MPJQ", "anatomy_img": "https://exrx.net/Muscles/Quadriceps.jpg"},
    "leg_curl": {"name": "כפיפת ברכיים ירך אחורית", "category": "רגליים", "type": "machine", "workout": "legs", "muscle": "המסטרינג", "guide": "כופף רגליים לאחור.", "video_url": "https://www.youtube.com/embed/1T5Kjn7x91w", "anatomy_img": "https://exrx.net/Muscles/Hamstrings.jpg"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GymLog Pro Ultimate</title>
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
        body { background-color: var(--bg-color); color: var(--text-color); padding: 15px; transition: background 0.3s, color 0.3s; padding-bottom: 70px; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; background: var(--card-bg); padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border); }
        h1 { color: var(--accent); font-size: 20px; display: flex; align-items: center; gap: 8px; }
        
        .user-stats { display: flex; gap: 10px; align-items: center; font-size: 14px; font-weight: bold; }
        .coin-badge { background: #f59e0b; color: #000; padding: 4px 8px; border-radius: 20px; font-size: 12px; }

        .nav-tabs { display: flex; gap: 6px; margin-bottom: 15px; overflow-x: auto; padding-bottom: 5px; }
        .tab-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 8px 14px; border-radius: 10px; font-size: 13px; cursor: pointer; white-space: nowrap; font-weight: bold; }
        .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

        .section-view { display: none; }
        .section-view.active { display: block; }

        .controls { display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px; }
        input.search-box { width: 100%; padding: 12px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 10px; font-size: 15px; }
        
        .filters { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 5px; }
        .filter-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 6px 12px; border-radius: 20px; font-size: 13px; cursor: pointer; white-space: nowrap; }
        .filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); font-weight: bold; }

        .machine-card { background-color: var(--card-bg); border-radius: 14px; padding: 16px; margin-bottom: 15px; border: 1px solid var(--border); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .machine-title { font-size: 18px; font-weight: bold; color: var(--accent); }
        .badge-group { display: flex; gap: 5px; margin-top: 5px; }
        .badge { display: inline-block; background: var(--input-bg); color: var(--subtext); padding: 3px 8px; border-radius: 6px; font-size: 11px; border: 1px solid var(--border); }
        
        .content-grid { display: grid; grid-template-columns: 1fr 110px; gap: 10px; align-items: center; margin-top: 10px; }
        .anatomy-img { width: 100%; height: 110px; object-fit: contain; background: #fff; border-radius: 8px; padding: 4px; border: 1px solid var(--border); }
        
        .section-title { font-size: 13px; color: var(--subtext); margin-top: 10px; }
        .muscle-info { font-size: 14px; color: var(--text-color); margin-bottom: 6px; }
        .guide-info { font-size: 13px; color: var(--subtext); line-height: 1.4; margin-bottom: 10px; }
        iframe { width: 100%; height: 170px; border-radius: 8px; border: none; margin-bottom: 12px; margin-top: 10px; }
        
        .form-group { display: flex; gap: 8px; margin-top: 10px; }
        input[type="number"] { flex: 1; padding: 10px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 8px; font-size: 14px; text-align: center; }
        button.save-btn { background-color: var(--accent); color: #fff; border: none; padding: 10px 18px; font-weight: bold; border-radius: 8px; cursor: pointer; }
        button.save-btn:hover { background-color: var(--accent-hover); }
        
        .history-box { margin-top: 12px; background: var(--input-bg); padding: 10px; border-radius: 8px; font-size: 12px; max-height: 110px; overflow-y: auto; color: var(--subtext); border: 1px solid var(--border); }
        .history-item { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 4px 0; }

        /* Timer & Extra tools */
        .tools-card { background: var(--card-bg); padding: 15px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 15px; text-align: center; }
        .timer-display { font-size: 32px; font-weight: bold; color: var(--accent); margin: 10px 0; }
        .shop-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .shop-item { background: var(--input-bg); border: 1px solid var(--border); padding: 15px; border-radius: 10px; text-align: center; }
    </style>
</head>
<body>
    <header>
        <h1>🏋️‍♂️ GymLog Pro</h1>
        <div class="user-stats">
            <span class="coin-badge" id="coinCount">🪙 120 מטבעות</span>
            <button class="tab-btn" onclick="toggleTheme()" style="padding: 4px 8px;">🌓</button>
        </div>
    </header>

    <!-- ניווט ראשית בין טאבים -->
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('exercises', this)">💪 כל התרגילים</button>
        <button class="tab-btn" onclick="switchTab('workouts', this)">📋 תוכניות אימון</button>
        <button class="tab-btn" onclick="switchTab('friends', this)">👥 חברים וקהילה</button>
        <button class="tab-btn" onclick="switchTab('shop', this)">🛒 חנות ואווטר</button>
        <button class="tab-btn" onclick="switchTab('timerTab', this)">⏱️ טיימר מנוחה</button>
    </div>

    <!-- 1. טאב כל התרגילים -->
    <div id="exercises" class="section-view active">
        <div class="controls">
            <input type="text" id="searchBox" class="search-box" placeholder="חפש תרגיל..." oninput="filterMachines()">
            <div class="filters">
                <button class="filter-btn active" onclick="setCategory('הכל', this)">הכל</button>
                <button class="filter-btn" onclick="setCategory('חזה', this)">חזה</button>
                <button class="filter-btn" onclick="setCategory('גב', this)">גב</button>
                <button class="filter-btn" onclick="setCategory('כתפיים', this)">כתפיים</button>
                <button class="filter-btn" onclick="setCategory('רגליים', this)">רגליים</button>
            </div>
        </div>

        <div id="machinesList">
            {% for id, m in machines.items() %}
            <div class="machine-card" data-name="{{ m.name }}" data-category="{{ m.category }}" data-workout="{{ m.workout }}">
                <div class="machine-title">{{ m.name }}</div>
                <div class="badge-group">
                    <span class="badge">{{ m.category }}</span>
                    <span class="badge">{% if m.type == 'free' %}משקל חופשי{% else %}מכונה{% endif %}</span>
                </div>
                
                <div class="content-grid">
                    <div>
                        <div class="section-title">שרירים פועלים:</div>
                        <div class="muscle-info">{{ m.muscle }}</div>
                    </div>
                    <div>
                        <img src="{{ m.anatomy_img }}" alt="שריר מטרה" class="anatomy-img">
                    </div>
                </div>
                
                <div class="section-title">איך לבצע:</div>
                <div class="guide-info">{{ m.guide }}</div>
                
                <iframe src="{{ m.video_url }}" allowfullscreen></iframe>
                
                <form onsubmit="saveWeight(event, '{{ id }}')">
                    <div class="form-group">
                        <input type="number" step="0.5" id="weight-{{ id }}" placeholder="משקל (ק״ג)" required>
                        <input type="number" id="reps-{{ id }}" placeholder="חזרות" required>
                        <button type="submit" class="save-btn">שמור + 🪙</button>
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

    <!-- 2. טאב תוכניות אימון -->
    <div id="workouts" class="section-view">
        <div class="tools-card">
            <h3>בחר תוכנית אימון להיום</h3>
            <p style="color:var(--subtext); font-size:13px; margin-top:5px;">מסנן אוטומטית את התרגילים השייכים ליום האימון שלך</p>
            <div style="display:flex; gap:8px; margin-top:15px; justify-content:center; flex-wrap:wrap;">
                <button class="tab-btn active" onclick="filterWorkout('all', this)">הכל</button>
                <button class="tab-btn" onclick="filterWorkout('push', this)">🔥 דחיפה (Push)</button>
                <button class="tab-btn" onclick="filterWorkout('pull', this)">⚡ משיכה (Pull)</button>
                <button class="tab-btn" onclick="filterWorkout('legs', this)">🦵 רגליים (Legs)</button>
            </div>
        </div>
    </div>

    <!-- 3. טאב חברים וקהילה -->
    <div id="friends" class="section-view">
        <div class="tools-card">
            <h3>החברים שלך בחדר כושר</h3>
            <p style="color:var(--subtext); font-size:13px; margin-top:5px;">עקוב אחרי ההתקדמות של חברים וראה אילו משקלים הם הרימו</p>
            <div style="margin-top: 15px; text-align:right;">
                <label style="display:flex; align-items:center; gap:8px; font-weight:bold; cursor:pointer;">
                    <input type="checkbox" id="shareToggle" checked onchange="toggleShareStatus()" style="width:18px; height:18px;">
                    שתף את הפרופיל והמשקלים שלי עם חברים
                </label>
            </div>
        </div>

        <div class="machine-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <strong>אומרי (Omri)</strong>
                <span class="badge" style="background:#10b981; color:#fff;">אימון דחיפה</span>
            </div>
            <div style="font-size:13px; color:var(--subtext);">לחיצת חזה מוט: <strong>85 ק״ג x 8 חזרות</strong> (אתמול)</div>
        </div>

        <div class="machine-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <strong>נדב (Nadav)</strong>
                <span class="badge" style="background:#3b82f6; color:#fff;">אימון רגליים</span>
            </div>
            <div style="font-size:13px; color:var(--subtext);">סקוואט חופשי: <strong>110 ק״ג x 5 חזרות</strong> (היום)</div>
        </div>
    </div>

    <!-- 4. טאב חנות ואווטר -->
    <div id="shop" class="section-view">
        <div class="tools-card">
            <h3>חנות האווטרים והשדרוגים</h3>
            <p style="color:var(--subtext); font-size:13px; margin-top:5px;">השתמש במטבעות שהרווחת באימונים כדי לקנות פריטים מיוחדים</p>
        </div>
        <div class="shop-grid">
            <div class="shop-item">
                <div style="font-size:24px;">👑</div>
                <div style="font-weight:bold; margin-top:5px;">כתר זהב</div>
                <div style="color:#f59e0b; font-size:13px; margin-top:3px;">🪙 100 מטבעות</div>
                <button class="save-btn" style="width:100%; margin-top:10px; padding:6px;" onclick="buyItem(100)">קנה</button>
            </div>
            <div class="shop-item">
                <div style="font-size:24px;">🦾</div>
                <div style="font-weight:bold; margin-top:5px;">שריון טיטניום</div>
                <div style="color:#f59e0b; font-size:13px; margin-top:3px;">🪙 250 מטבעות</div>
                <button class="save-btn" style="width:100%; margin-top:10px; padding:6px;" onclick="buyItem(250)">קנה</button>
            </div>
        </div>
    </div>

    <!-- 5. טאב טיימר מנוחה -->
    <div id="timerTab" class="section-view">
        <div class="tools-card">
            <h3>טיימר מנוחה בין סטים</h3>
            <div class="timer-display" id="timerClock">01:30</div>
            <div style="display:flex; gap:10px; justify-content:center;">
                <button class="save-btn" onclick="startTimer(90)">90 שניות</button>
                <button class="tab-btn" onclick="startTimer(120)">2 דקות</button>
                <button class="tab-btn" onclick="stopTimer()" style="background:#ef4444; color:#fff; border:none;">איפוס</button>
            </div>
        </div>
    </div>

    <script>
        let userCoins = 120;

        function toggleTheme() {
            document.body.classList.toggle('light-mode');
        }

        function switchTab(tabId, btn) {
            document.querySelectorAll('.section-view').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-tabs .tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }

        function setCategory(cat, btn) {
            document.querySelectorAll('.filters .filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterMachines(cat, null);
        }

        function filterWorkout(workoutType, btn) {
            document.querySelectorAll('#workouts .tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            switchTab('exercises', document.querySelector('.nav-tabs .tab-btn'));
            filterMachines('הכל', workoutType);
        }

        function filterMachines(category = 'הכל', workout = null) {
            const query = document.getElementById('searchBox') ? document.getElementById('searchBox').value.toLowerCase() : '';
            const cards = document.querySelectorAll('.machine-card');

            cards.forEach(card => {
                const name = card.getAttribute('data-name').toLowerCase();
                const cat = card.getAttribute('data-category');
                const work = card.getAttribute('data-workout');

                const matchesSearch = name.includes(query);
                const matchesCat = (category === 'הכל' || cat === category);
                const matchesWorkout = (!workout || workout === 'all' || work === workout);

                if (matchesSearch && matchesCat && matchesWorkout) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        async function saveWeight(e, machineId) {
            e.preventDefault();
            const weight = document.getElementById(`weight-${machineId}`).value;
            const reps = document.getElementById(`reps-${machineId}`).value;

            const res = await fetch('/api/add_weight', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({machine_id: machineId, weight: parseFloat(weight), reps: parseInt(reps)})
            });

            if(res.ok) {
                const data = await res.json();
                const historyBox = document.getElementById(`history-${machineId}`);
                
                if(historyBox.innerHTML.includes('טרם נרשמו')) {
                    historyBox.innerHTML = '';
                }

                const newItem = document.createElement('div');
                newItem.className = 'history-item';
                newItem.innerHTML = `<span><strong>${data.weight} ק״ג</strong> x ${data.reps} חזרות</span><span>${data.date.substring(0,16)}</span>`;
                historyBox.prepend(newItem);

                document.getElementById(`weight-${machineId}`).value = '';
                document.getElementById(`reps-${machineId}`).value = '';

                // הוספת מטבעות
                userCoins += 10;
                document.getElementById('coinCount').innerText = `🪙 ${userCoins} מטבעות`;
                alert('כל הכבוד! נשמר בהצלחה והרווחת 10 מטבעות 🪙');
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

        function stopTimer() {
            clearInterval(countdown);
            document.getElementById('timerClock').innerText = "01:30";
        }

        function toggleShareStatus() {
            const status = document.getElementById('shareToggle').checked;
            alert(status ? 'הפרופיל שלך גלוי כעת לחברים' : 'הפרופיל שלך במצב פרטי ומוסתר מהחברים');
        }

        function buyItem(cost) {
            if(userCoins >= cost) {
                userCoins -= cost;
                document.getElementById('coinCount').innerText = `🪙 ${userCoins} מטבעות`;
                alert('תתחדש! הפריט נוסף לאווטר שלך בהצלחה 🎉');
            } else {
                alert('אין לך מספיק מטבעות! לך להתאמן כדי להרוויח עוד 🪙');
            }
        }
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
