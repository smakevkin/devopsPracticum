# devopsPracticum

Мини-сервис с полным циклом: приложение на Python, контейнеризация, CI, мониторинг, инфраструктура как код и деплой в Kubernetes. Проект учебный, сделан на выходные


## Что внутри

| Область | Инструменты |
|---|---|
| Приложение | Python, FastAPI, PostgreSQL |
| Контейнеры | Docker, docker-compose |
| Веб-сервер | Nginx (reverse proxy) |
| Мониторинг | Prometheus, Grafana, node_exporter |
| CI | Github actions (test, build, push) |
| IaC | Terraform (провайдер `kreuzwerker/docker`), Ansible |
| Оркестрация | Kubernetes (minikube) |


## Структура репозитория

```
app/          приложение и Dockerfile
compose/      docker-compose со всем стеком (app, postgres, nginx, prometheus, grafana)
terraform/    описание контейнера-«сервера», сети и volume
ansible/      inventory и плейбук настройки «сервера»
k8s/          манифесты Kubernetes
```

## Эндпоинты приложения

| Путь | Что делает |
|---|---|
| `/health` | Проверка живости, используется в healthcheck и probes |
| `/visit` | Увеличивает счётчик в PostgreSQL и возвращает значение |
| `/metrics` | Метрики в формате Prometheus |

## Идеи на потом

- Доступ к «серверу» через OpenVPN.
- Helm-чарт вместо «голых» манифестов.
- Небольшой экспортер метрик на Go.
- Сравнить запуск стека на Podman и Docker.
