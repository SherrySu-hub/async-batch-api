# 非同步批次任務處理 API
[English](https://github.com/SherrySu-hub/AI_deployment/blob/main/README.md) | 中文

本專案提供一個基於 FastAPI 與 asyncio 架構的 **通用非同步批次任務處理 API 框架**。它支援所有可從批次推論中受益的任務，例如圖片分類、NLP 預測、影片畫面處理等等。

---

## 功能特色

- 使用非同步佇列與背景批次處理
- 模型與任務函式可插拔，支援不同應用情境
- 使用 Gunicorn + UvicornWorker，適用於生產環境
- 可透過 Docker 簡易部署

---

## 專案結構

```
.
├── main.py                 # FastAPI 進入點，負責處理請求與任務佇列
├── gunicorn_config.py      # Gunicorn 設定檔
├── classification/
│   └── inference.py        # 範例任務邏輯（圖片分類，可替換）
├── Dockerfile
├── docker-compose.yml
```

---

## 執行 API

### 開發模式
```bash
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```
適用於本地開發與測試，支援程式碼熱重載。

### 生產模式（Gunicorn）
```bash
gunicorn main:app -c gunicorn_config.py
```
注意：Gunicorn 僅支援 Linux/Unix 環境。  
若在 Windows 使用，請透過 Docker 部署或直接使用 uvicorn 執行。

### Docker（跨平台）
```bash
docker-compose up --build -d
```
建議使用此方式以確保跨平台一致的部署體驗。  
服務將會啟動於：
```
http://localhost:5001/cls
```

---

## API 使用方式

### POST `/cls`

**參數：**
- `file`：上傳檔案（如圖片、文件等）

**範例：**
```bash
curl -X POST http://localhost:5001/cls -F "file=@path/to/image.jpg"
```

**回傳：**
```json
{
  "prediction": [your result here]
}
```

---

## 任務自訂化

若要支援其他任務（如 NLP、影片、表格），請修改：

- `classification/inference.py`：實作 `get_model`、`preprocess` 與 `batch_classification`
- `BatchProcessor`：負責非同步任務佇列與批次處理邏輯
- API 路由可擴充以支援多任務與不同端點

---

## Gunicorn 設定（`gunicorn_config.py`）

- `workers = 1`
- `threads = 8`
- `worker_class = 'uvicorn.workers.UvicornWorker'`
- `bind = '0.0.0.0:5001'`

> 這些設定值可根據硬體資源與任務特性進行調整：
> - 多核心伺服器執行 CPU 密集任務時可增加 `workers`
> - I/O 密集或高併發情況下可提高 `threads`

---

## Python 依賴套件

範例：`requirements.txt`
```txt
fastapi
uvicorn
...
```
根據任務需求可能還需額外套件，例如 `transformers`、`opencv-python` 等。
