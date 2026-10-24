@echo off
cd /d "%~dp0"
echo Site Inter TV disponible sur http://localhost:8080  (fermez cette fenetre pour arreter)
start "" http://localhost:8080/index.html
python -m http.server 8080
