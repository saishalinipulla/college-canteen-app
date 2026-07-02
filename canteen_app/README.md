# College Canteen Ordering App

A Flask web app with:
- Separate pages per section: Tiffins, Idlis, Lunch, Snacks, Biryanis, Fast Food
- Student login using **name + phone number**
- Admin login using **phone number + password**
- Admin can **Accept**, **Reject**, or **Complete** an order
  - Reject and Complete both **remove the order from the database**
- A popup alert + an "order details" box shown after placing an order, visible to both the student (My Orders) and the admin (Admin Dashboard)

---

## 1. Project structure

```
canteen_app/
├── app.py                 # all routes / app logic
├── models.py               # database tables
├── seed_admin.py           # run once to create the admin login
├── requirements.txt
├── Procfile                 # for deployment
├── .gitignore
├── templates/               # HTML pages
└── static/css/style.css
```

---

## 2. Set this up in VS Code

**Step 1 — Install prerequisites (one time only)**
1. Install [Python 3.10+](https://www.python.org/downloads/) — during install, tick "Add Python to PATH".
2. Install [VS Code](https://code.visualstudio.com/).
3. In VS Code, install the **Python** extension (Extensions icon on the left sidebar → search "Python" → Install, by Microsoft).

**Step 2 — Open the project**
1. Copy the `canteen_app` folder to your computer (e.g. `Desktop/canteen_app`).
2. In VS Code: `File → Open Folder…` → select `canteen_app`.

**Step 3 — Create a virtual environment**
Open the terminal in VS Code (`` Ctrl+` `` / `` Cmd+` ``) and run:

```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You'll see `(venv)` appear at the start of the terminal line — that means it worked.

**Step 4 — Install the dependencies**

```bash
pip install -r requirements.txt
```

**Step 5 — Create your admin login**

```bash
python seed_admin.py
```
It will ask for an admin phone number and password — type whatever you want (e.g. `9999999999` / `admin123`). Remember these, you'll use them to log into `/admin/login`.

**Step 6 — Run the app**

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000** — the app is running locally. A `canteen.db` SQLite file is created automatically with some sample menu items already in it, so you can start testing right away.

To add/edit menu items right now, the fastest way as a beginner is editing the `sample_items` list inside `seed_menu_if_empty()` in `app.py` before the first run, or directly opening `canteen.db` with the free **DB Browser for SQLite** tool later.

---

## 3. How the app behaves (so testing makes sense)

- Visit `/` → pick a section → add items with quantity → they go into `/cart`.
- Click **Place Order** in the cart → if you're not logged in, it asks you to log in with just your **name and phone number** (no password) → then the order is created and you see a popup alert confirming it, plus it appears in **My Orders**.
- Admin logs in separately at `/admin/login` with **phone + password**. A normal student account can never reach `/admin/dashboard` — it's protected and will redirect to the admin login if you're not an authenticated admin.
- In **Admin Dashboard**, every pending order shows an **Accept** / **Reject** button.
  - **Reject** deletes the order immediately.
  - **Accept** moves it to "Accepted Orders (in progress)".
  - From there, **Mark Completed & Remove** deletes it from the database — exactly as you asked.

---

## 4. Push it to GitHub

**Step 1 — Create a GitHub repository**
1. Go to [github.com](https://github.com) → click **New repository**.
2. Name it e.g. `college-canteen-app`, keep it Public or Private, **don't** tick "Add a README" (you already have one). Click **Create repository**. Keep the page open — you'll need the URL it shows you.

**Step 2 — Push your code from VS Code's terminal**

Inside the `canteen_app` folder, with the terminal open:

```bash
git init
git add .
git commit -m "Initial commit - college canteen app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/college-canteen-app.git
git push -u origin main
```

Replace the URL with the one GitHub showed you. If it's your first time using git, it may ask you to sign in through the browser — just follow the prompt.

Because of the `.gitignore` file, your `venv/` folder and the local `canteen.db` database won't be uploaded — only your actual code.

From now on, whenever you make changes:
```bash
git add .
git commit -m "describe what you changed"
git push
```

---

## 5. Deploy it online

The app currently uses SQLite, which is a simple file-based database. This matters when picking a host:

### Render.com — step by step

**Step 1 — Push your latest code to GitHub** (skip if already done)
```bash
git add .
git commit -m "Prepare for Render deployment"
git push
```

**Step 2 — Create a Render account**
Go to [render.com](https://render.com) → **Get Started** → sign up with your GitHub account (easiest, it links automatically).

**Step 3 — Create the free database first**
1. On the Render dashboard, click **New +** → **PostgreSQL**.
2. Give it a name, e.g. `canteen-db`. Leave region/plan on the free options.
3. Click **Create Database**. Wait ~1 minute until it's "Available".
4. On the database's page, scroll to **Connections** and copy the **Internal Database URL** (starts with `postgres://…`). Keep this tab open.

**Step 4 — Create the web service**
1. Click **New +** → **Web Service**.
2. Choose **Build and deploy from a Git repository** → connect your GitHub account if asked → select your `college-canteen-app` repo.
3. Fill in:
   - **Name:** `college-canteen-app` (or anything)
   - **Region:** same as your database
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
4. Scroll to **Environment Variables** → **Add Environment Variable** twice:
   - `SECRET_KEY` → any random text, e.g. `canteen-super-secret-2024`
   - `DATABASE_URL` → paste the **Internal Database URL** you copied in Step 3
5. Click **Create Web Service**. Render will now build and deploy — watch the logs, it takes 2–5 minutes. When it says "Live", your app is online at a URL like `https://college-canteen-app.onrender.com`.

**Step 5 — Create your admin login on the live site**
Your live database is empty (no admin yet). On the web service page:
1. Click the **Shell** tab (top of the page).
2. Run:
   ```bash
   python seed_admin.py
   ```
3. Enter your admin phone number and password when prompted — same as you did locally.

**Step 6 — Test it**
Visit your Render URL, place a test order, then log in at `/admin/login` with the credentials from Step 5 and try Accept/Reject/Complete.

**From now on:** every time you `git push` to `main`, Render automatically rebuilds and redeploys — that's the whole point of connecting it to GitHub. Your order/admin data stays intact because it now lives in the Postgres database, not in a file that gets wiped on redeploy.

> Free Render Postgres databases expire after 30 days unless upgraded — fine for a class project/demo; for something longer-term you'd upgrade the database plan.

### Alternative: PythonAnywhere (if you ever want a simpler free option with built-in persistent SQLite)
1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com).
2. **Consoles → Bash** → clone your repo:
   ```bash
   git clone https://github.com/YOUR-USERNAME/college-canteen-app.git
   cd college-canteen-app
   pip install --user -r requirements.txt
   python seed_admin.py
   ```
3. **Web tab → Add a new web app → Flask** → point the source code / working directory to your cloned folder, and set the WSGI file to import your `app` object from `app.py` (PythonAnywhere shows you exactly where to edit this).
4. Click **Reload** on the Web tab. Your app is now live at `yourusername.pythonanywhere.com`, and because it's a persistent filesystem, your `canteen.db` keeps its data between reloads.

---

## 6. Quick troubleshooting

- **`ModuleNotFoundError`** → your virtual environment isn't active, or you forgot `pip install -r requirements.txt`.
- **Admin login says "Invalid phone number or password"** → re-run `python seed_admin.py` to reset it.
- **Changes to templates not showing** → make sure `app.py` is running with `debug=True` (already set) and refresh the browser; if still stuck, stop the server (`Ctrl+C`) and run `python app.py` again.
- **Want to reset all data** → stop the app, delete `canteen.db`, run `python app.py` again (it recreates the DB and sample menu), then `python seed_admin.py` again for the admin login.
