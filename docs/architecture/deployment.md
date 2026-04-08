# Deployment Architecture

## 1. Thanh phan he thong

- `frontend`: nginx/load balancer
- `backend`: ERPNext web app
- `queue-short`: xu ly tac vu ngan
- `queue-default`: xu ly tac vu trung binh
- `queue-long`: xu ly integration/report/e-invoice
- `scheduler`: cron jobs
- `websocket`: realtime events
- `db`: MariaDB
- `redis-cache`
- `redis-queue`
- `redis-socketio`

## 2. Moi truong

- `dev`
- `uat`
- `prod`

## 3. Khuyen nghi production

- 2 app nodes
- 1 worker node rieng
- 1 MariaDB primary
- 1 MariaDB read replica
- object storage cho attachments
- backup full hang ngay + binlog
- monitoring va alerting

## 4. RTO/RPO muc tieu

- RPO: 15 phut
- RTO: 4 gio

## 5. Non-functional requirements

- 99.5% uptime trong gio hanh chinh
- backup retention 30-90 ngay
- log audit toi thieu 1 nam
- TLS cho toan bo kenh tich hop
