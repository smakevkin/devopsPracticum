# Учебный проект для практики DevOps инструментов

Мини-сервис с полным циклом разработки: приложение на Python+FastAPI, контейнеризацией через Docker, CI через GitHub actions, мониторинг с Prometheus/Node-Exporter/Grafana, IaC с Ansible и Terraform. Проект учебный для того чтобы вспомнить DevOps инструменты.

## Статус

| Состояние | Что |
|---|---|
| Готово | Приложение и тесты, Docker и docker-compose, Nginx, Prometheus и Grafana (настройки из файлов), healthcheck у всех сервисов, CI на GitHub Actions, Terraform (контейнер-«сервер»), Ansible-плейбук для "сервера" |
| В планах | Kubernetes (minikube), Helm, доступ к "серверу" через OpenVPN |

## Что внутри

| Область | Инструменты |
|---|---|
| Приложение | Python, FastAPI, PostgreSQL |
| Контейнеры | Docker, docker-compose |
| Веб-сервер | Nginx (reverse proxy) |
| Мониторинг | Prometheus, Grafana, node_exporter |
| CI | GitHub actions (test, build, push) |
| IaC | Terraform (провайдер `kreuzwerker/docker`), Ansible |

## Структура репозитория

```
.github/       GitHub Actions Workflow
ansible/      inventory и playbook для настройки "сервера"
app/          приложение с FastApi и Dockerfile для него
compose/      Docker-compose для развертки приложения/бд/nginx/мониторинга
monitoring/   конфигурационные файлы для prometheus и grafana
nginx/        конфигурация nginx
terraform/    манифесты Terraform
```

## Эндпоинты

| Путь | Что делает |
|---|---|
| `/health` | Проверка живости приложения |
| `/healthn`| Проверка nginx сервера |
| `/grafana`| Дашборд Grafana |
| `/visit` | Увеличивает счётчик в PostgreSQL и возвращает значение |
| `/ready` | Проверка работоспособности приложения + бд |

Эндпоинт `/metrics` приложения намеренно закрыт снаружи (Nginx отвечает 404), Prometheus собирает метрики напрямую по внутренней сети.

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

Нужно: Docker с compose. Для варианта 2 ещё Terraform, Ansible и публичный ssh-ключ.

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

## Что ломалось
- healthcheck приложения с curl не работал, потому что в образе Alpine его нет, а есть wget;
- ключ не попадал в образ без объявления ARG и ssh в контейнер отвечал Permission denied (publickey);
- terraform init падал с 403: реестр блокирует регион, помог прокси;
- в CI тег образа 7/merge оказался недопустимым, а ssh-keygen задавал вопросы в неинтерактивной среде.

