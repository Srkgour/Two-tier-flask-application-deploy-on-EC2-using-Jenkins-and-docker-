# Two-Tier App with Jenkins CI/CD and Docker on AWS EC2

A two-tier web application deployed automatically by Jenkins onto a single EC2 instance.

| Tier | Technology | Exposure |
|---|---|---|
| Web tier | Flask + Gunicorn in a Docker container | Public, port 80 |
| Data tier | PostgreSQL 16 in a Docker container | Private, Docker network only |
| CI/CD | Jenkins on the EC2 host | Port 8080 |

```
Developer --git push--> GitHub --webhook--> Jenkins (EC2)
                                              |  test -> build -> deploy -> health check
                                              v
Browser --http://EC2-IP--> [web container :80] --> [db container :5432, private]
```

## Project structure

```
.
├── app/
│   ├── app.py
│   ├── templates/index.html
│   ├── tests/test_app.py
│   ├── conftest.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── scripts/setup-ec2.sh
├── docker-compose.yml
├── Jenkinsfile
├── .env.example
├── .gitignore
└── README.md
```

## Run locally (optional)

```bash
cp .env.example .env
docker compose up -d --build
# open http://localhost
```

## Deploy on EC2

### 1. Launch the instance
- AMI: Ubuntu Server 22.04 or 24.04
- Type: `t3.medium` recommended (Jenkins needs about 2 GB RAM; `t3.micro` works only with the swap file the script adds, and is slow)
- Storage: 20 GB gp3
- Key pair: create or choose one
- Security group inbound rules:

| Port | Source | Purpose |
|---|---|---|
| 22 | My IP | SSH |
| 80 | 0.0.0.0/0 | The web app |
| 8080 | My IP | Jenkins UI |

GitHub webhooks need to reach port 8080. Either allow 8080 from GitHub's webhook IP ranges (https://api.github.com/meta, "hooks" list) or skip the webhook and use "Build Now".

### 2. Install Docker and Jenkins
```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
bash scripts/setup-ec2.sh
```
The script prints the Jenkins initial admin password at the end.

### 3. Set up Jenkins
1. Open `http://<EC2-PUBLIC-IP>:8080`, paste the password, choose **Install suggested plugins**, create an admin user.
2. **Manage Jenkins > Credentials > System > Global > Add Credentials**
   - Kind: Secret text
   - Secret: a strong database password
   - ID: `db-password` (must match exactly)
3. **New Item > Pipeline** named `two-tier-app`.
   - Pipeline > Definition: *Pipeline script from SCM*
   - SCM: Git, Repository URL: your repo, Branch: `*/main`
   - Script Path: `Jenkinsfile`
   - Under Build Triggers, tick **GitHub hook trigger for GITScm polling**
4. Click **Build Now**.

### 4. Open the app
`http://<EC2-PUBLIC-IP>` shows the Task Tracker. Add a few tasks; they live in PostgreSQL.

### 5. Automatic builds on push
In GitHub: **Settings > Webhooks > Add webhook**
- Payload URL: `http://<EC2-PUBLIC-IP>:8080/github-webhook/`
- Content type: `application/json`
- Event: Just the push event

Edit `app/templates/index.html`, push, and watch Jenkins redeploy. The build number in the page header changes.

## What the pipeline does

1. **Checkout** the code from GitHub
2. **Test** with pytest inside a throwaway Python container
3. **Build image** tagged with the build number and `latest`
4. **Deploy** with `docker compose up -d --build`, injecting the DB password from Jenkins credentials
5. **Health check** by polling `/health`

## Troubleshooting

| Problem | Fix |
|---|---|
| `permission denied` on `/var/run/docker.sock` in a build | `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins` |
| Page not loading | Check the security group allows port 80, and `docker ps` shows `web` and `db` |
| `Set DB_PASSWORD` error | The `db-password` credential is missing or its ID is wrong |
| Jenkins is slow or killed | Use a larger instance; check `free -h` |
| Webhook not firing | Check port 8080 rules and GitHub's Recent Deliveries tab |
| Check logs | `docker compose -p twotier logs -f` |

## Security notes
- Do not leave 8080 or 22 open to the world; restrict to your IP.
- Attach an Elastic IP so the public IP does not change when the instance restarts.
- For real use, add HTTPS (an ALB with ACM, or Nginx with Let's Encrypt).
- Stop or terminate the instance when done to avoid charges.

## Publish to GitHub
```bash
git init && git add . && git commit -m "Two-tier app with Jenkins and Docker"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
