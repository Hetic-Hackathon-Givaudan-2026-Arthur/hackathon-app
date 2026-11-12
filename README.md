# hackathon-app

Prérequis : Docker Desktop démarré et extension Dev Containers installée dans VS Code , Ollama avec le modèle llama3.2:1b téléchargé
Installer Ollama : ollama.com/download

Pull le modele :

```bash
ollama pull llama3.2:1b       # 1,3 Go
ollama run llama3.2:1b "Réponds en une phrase : qui es-tu ?"
```

Démarrer le projet :

```bash
git clone https://github.com/Hetic-Hackathon-Givaudan-2026-Arthur/hackathon-app
cd hackathon-app
code .
```

Dans VS Code, sélectionner Dev Containers: Reopen in Container.

Dans le terminal du Dev Container :

```bash
cp -n backend/.env.example backend/.env
```

```bash
npm run dev
```

Dans un second terminal du Dev Container :

```bash
cd backend && python -m pip install -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Ouvrir ensuite :

Application web : http://localhost:5173

Backend : http://localhost:8000/health
