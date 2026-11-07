# Учебный проект для практики DevOps инструментов

Мини-сервис с полным циклом разработки: приложение на Python+FastAPI, контейнеризация через Docker, CI через GitHub Actions, мониторинг с Prometheus/Node-Exporter/Grafana, IaC с Ansible и Terraform, оркестрация в Kubernetes (minikube). Проект учебный, чтобы вспомнить DevOps инструменты.

## Статус

| Состояние | Что |
|---|---|
| Готово | Приложение и тесты, Docker и docker-compose, Nginx, Prometheus и Grafana (настройки из файлов), healthcheck у всех сервисов, CI на GitHub Actions, Terraform (контейнер-«сервер»), Ansible-плейбук для "сервера", Kubernetes (minikube): приложение в Deployment на 3 реплики с liveness/readiness-пробами, PostgreSQL в StatefulSet с PVC, Ingress |
| В планах | Helm, проверка k8s-манифестов в CI, доступ к "серверу" через OpenVPN |

## Что внутри

| Область | Инструменты |
|---|---|
| Приложение | Python, FastAPI, PostgreSQL |
| Контейнеры | Docker, docker-compose |
| Веб-сервер | Nginx (reverse proxy) |
| Мониторинг | Prometheus, Grafana, node_exporter |
| CI | GitHub Actions (test, build, push) |
| IaC | Terraform (провайдер `kreuzwerker/docker`), Ansible |
| Оркестрация | Kubernetes (minikube), Ingress-nginx |

## Структура репозитория

```
.github/      GitHub Actions workflow
ansible/      inventory и playbook для настройки "сервера"
app/          приложение на FastAPI и Dockerfile для него
compose/      docker-compose для развертки приложения/бд/nginx/мониторинга
k8s/          манифесты Kubernetes: namespace, configmap, бд, приложение, ingress
monitoring/   конфигурационные файлы для prometheus и grafana
nginx/        конфигурация nginx
terraform/    манифесты Terraform
```

## Эндпоинты

| Путь | Что делает |
|---|---|
| `/health` | Проверка живости приложения |
| `/ready` | Проверка работоспособности приложения + бд |
| `/visit` | Увеличивает счётчик в PostgreSQL и возвращает значение |
| `/healthn` | Проверка nginx сервера (только compose) |
| `/grafana` | Дашборд Grafana (только compose) |

Эндпоинт `/metrics` приложения намеренно закрыт снаружи: в compose Nginx отвечает на него 404, Prometheus собирает метрики напрямую по внутренней сети. В Kubernetes наружу через Ingress открыт только `/visit`, на всё остальное ingress-nginx отвечает 404. `/health` и `/ready` использует сам Kubernetes для проб, они ходят в под напрямую.

## Мониторинг

Prometheus собирает метрики приложения (`http_requests_total`, `http_request_duration_seconds`), Grafana подключается к нему и подхватывает источник данных и дашборд из файлов в `monitoring/`, поэтому настраивать вручную ничего не нужно.

## CI

Workflow запускается на pull request и push в `dev` и `main`:

| Job | Что делает |
|---|---|
| `lint` | `ruff check` и `ruff format --check` |
| `test` | `pytest` на Python 3.11 |
| `test-compose` | `docker compose config` с шаблоном `.env.example` |
| `test-terraform` | `terraform fmt -check`, `init -backend=false`, `validate` |
| `build` | сборка образа, а на push ещё и публикация в GHCR |

## Быстрый старт

Нужно: Docker с compose. 
Для варианта 2 ещё Terraform, Ansible и публичный ssh-ключ. 
Для варианта 3 ещё minikube и kubectl.

### Вариант 1. Стек приложения

```bash
cp compose/.env.example compose/.env      # задайте пароли в .env
docker compose -f compose/docker-compose.yml up -d --build
docker compose -f compose/docker-compose.yml ps   # все сервисы должны быть healthy
```

Grafana: `http://localhost:<NGINX_PORT>/grafana`, логин и пароль из `GF_SECURITY_ADMIN_USER` и `GF_SECURITY_ADMIN_PASSWORD` в `.env`.

Остановка: `docker compose -f compose/docker-compose.yml down`. Флаг `-v` дополнительно удалит данные бд и Grafana.

### Вариант 2. "Сервер" (Terraform и Ansible)

Публичный ключ по умолчанию читается из `~/.ssh/id_ed25519.pub` (путь меняется переменной Terraform).

```bash
terraform -chdir=terraform init
terraform -chdir=terraform apply
ansible-playbook -i ansible/inventory.yml ansible/linux.yml
```

### Вариант 3. Kubernetes (minikube)

```bash
minikube start --driver=docker
minikube addons enable ingress
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic db-secret -n pyapp \
  --from-literal=POSTGRES_USER=<user> \
  --from-literal=POSTGRES_PASSWORD=<password> \
  --from-literal=POSTGRES_DB=<db>
kubectl apply -f k8s/
kubectl wait --for=condition=Ready pods --all -n pyapp --timeout=120s
curl "http://$(minikube ip)/visit"
```

PostgreSQL работает в StatefulSet с PersistentVolumeClaim, поэтому данные переживают пересоздание пода; доступ к бд внутри кластера идёт через headless Service `db`. Приложение запущено в Deployment на 3 реплики: liveness-проба смотрит на `/health` и не зависит от бд, readiness-проба смотрит на `/ready`, так что при падении бд поды не перезапускаются, а только выпадают из Service. Настройки подключения лежат в ConfigMap, пароль в Secret, который создаётся командой и в репозитории не хранится.

Удаление: `kubectl delete namespace pyapp` удалит всё вместе с данными бд и Secret.

## Что ломалось
- healthcheck приложения с curl не работал, потому что в образе Alpine его нет, а есть wget;
- ключ не попадал в образ без объявления ARG и ssh в контейнер отвечал Permission denied (publickey);
- terraform init падал с 403: реестр блокирует регион, помог прокси;
- в CI тег образа 7/merge оказался недопустимым, а ssh-keygen задавал вопросы в неинтерактивной среде;
- StatefulSet не создавался: `selector.matchLabels` не совпадал с лейблами в шаблоне пода;
- `volumeClaimTemplates` был вложен в контейнер, а должен быть на уровне спецификации StatefulSet;
- опечатки в регистре и названиях полей (`clusterIp`, `limitts`) kubectl принимал не так, как ожидалось, ловил через `--dry-run=server`;
- `kubectl delete -f k8s/` удалил namespace вместе с Secret, который создавался командой, и бд не стартовала после повторного apply.