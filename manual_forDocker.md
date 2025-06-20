# Docker - Overview
https://docs.docker.com/get-started/docker-overview/

# 映像檔（Image）: 
一個用來創建 container 的唯讀模板。包含需要部屬的 OS, App, Dependency

**建立 image 的方法**:
1. 從倉庫 pull <br>
    ex: Docker Hub
2. 在本機建立 <br>
  使用 **Dockerfile**

* 查看所有 image 資訊: `docker images [image]`
* 刪除: `docker rm [image]`
* 儲存: `docker save -o [file_name] [image]:[tag]`
* 載入: `docker load -i [file_name]`

# 容器（Container）: 
* 查看所有 container 的資訊: `docker ps -a`
* 新建並啟動: `docker run --name [container] [image]:[tag] [COMMAND] [ARG...]`
    * `--gpus`
    * `-p [host_port]:[container_port]` 
    * `-i`: 開啟 STDIN
    * `-t`: 建立虛擬終端機 (pseudo-TTY)，可以在容器中使用終端機環境模擬與 Shell 的互動。(-it 通常一起使用，單獨使用時 Ctrl-C 無法結束容器)
    * `-d`: 後臺常駐執行
    * `-v [local path (absolutely)]:[container path]`
* 啟用: `docker start [container]`
* 重啟: `docker restart [container]`
* 關閉: `docker stop [container]`
* 刪除: `docker rm [container]`
* 進入 container: `docker exec [container]`
    * `-i`
    * `-t`
    * `-d`
    * `--privileged`
    * `-u`

# Dockerfile
## 常用指令
| 指令         | 用途與說明                                                                                      | 範例語法                                                                 |
|--------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| `FROM`       | 指定基底映像作為建構的起點，可多次使用建立多階段建構                                             | `FROM python:3.12`                                                       |
| `RUN`        | 在映像中執行命令，每個 RUN 都會建立一層，建議多個命令合併寫                                       | `RUN apt-get update && apt-get install -y vim` |
| `CMD`        | 指定容器啟動時執行的預設命令，可被 `docker run` 覆蓋，只能有一個                                 | `CMD ["python", "main.py"]`                                              |
| `WORKDIR`    | 設定工作目錄，後續指令（如 `RUN`, `CMD`, `COPY` 等）皆以此為起點                                 | `WORKDIR /fundus`                                                           |
| `COPY`       | 複製檔案或資料夾至映像中                                                                          | `COPY . .`    |
| `ENV`       | 設定環境變數中                                                                          | `CUDA_HOME=/usr/local/cuda`    |

## 注意事項
若需下載 linux 套件需用 `apt-get` 而不是 `apt`
```dockerfile    
RUN apt-get update &&\ 
    ...
    # 刪除 apt 快取，降低 image 大小
    rm -rf /var/lib/apt/lists/*
```

範例:
```dockerfile
# 使用官方 Python 基礎映像
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 複製檔案到容器內
COPY . .

# 安裝依賴套件
RUN pip install --no-cache-dir -r requirements.txt

# 容器啟動時執行的指令
CMD ["python", "main.py"]
```

# Docker Compose
Docker Compose 基本上就是將 docker 指令改成 yaml 格式（通常命名為 `docker-compose.yml`），方便管理多個服務。

| 欄位       | 用途                                               |
|------------|----------------------------------------------------|
| `services` | 定義服務（例如 `web`、`db`、`redis`）               |
| `build`    | 使用當前目錄下的 Dockerfile 建構 image              |
| `image`    | 指定使用的現成映像檔（例如 `redis:7`）               |
| `ports`    | 對外開放的埠口（格式為 `"host:container"`）         |
| `volumes`  | 掛載目錄，讓主機資料夾與容器內部目錄同步             |


範例: 基本上可以將這個當模板
```yaml
services:
  ai_agent:
    build:
      context: .
      dockerfile: dockerfile
    image: rag:v0.0.1
    container_name: rag_v1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    stdin_open: true
    tty: true
    ports:
      - 8885:5000
```

# 環境建置

1 **一般深度學習應用部屬** <br>
  確定好 cuda, pytorch 版本後選擇 pytorch 官方提供 (Docker hub 上) 的對應版本的 image 做為基底 image 後就可以用上面的範例寫 dockerfile

2 **官方沒有提供專案需要的 cuda, pytorch 版本的 image** (如 mmdetection) <br>
  根據 cuda 版本使用 cuda 官方提供的對應版本的 image，再自行安裝 python, pytorch

3 **必須用其他官方 image 當作基底 image**，如 ollama <br>
  根據 cuda 官方指令自行下載對應版本的 cuda 軟體套件後安裝，再自行安裝 python, pytorch。若基底 image 的 ubuntu 版本太低可能會有 python 套件安裝錯誤的問題，需安裝 pyenv 後透過 pyenv 安裝對應版本的 python

* 建議在本地先用基底 image 創建 container 後一步步安裝所需的依賴，確認沒問題後再寫進 dockerfile。<br>
* 善用 github 上 的 issue 與 chat-GPT

## 遇到的坑 (其他不記得了哈)
* `WARNING: apt does not have a stable CLI interface` <br>
  兩個解決方法:
  1. 設定成非交互式: <br>
  `DEBIAN_FRONTEND=noninteractive`
  2. assume "yes" as answer to all prompts and run non-interactively <br>
  `apt-get install -y ...`

* 用到 cuda_extension
  * 必須使用 devel 版本的 pytorch image
  * 需安裝 g++
  ```
  apt-get install build-essential
  ```
  * 需要指定cuda架構版本 (8.0、8.6 : RTX30系列、9.0 : H100、+PTX : 支持向後兼容的未來架構)
  ```dockerfile
  ENV TORCH_CUDA_ARCH_LIST="8.0 8.6 9.0+PTX"
  ```
  * 需要設置cuda相關環境變數
  ```dockerfile
  ENV CUDA_HOME=/usr/local/cuda
  ENV PATH=$CUDA_HOME/bin:$PATH
  ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
  ```

* `/bin/bash^M: bad interpreter: No such file or directory` <br>
git 的行尾字符是使用 CRLF ，只要 pull 過需更改成 LF <br>
PS. VS Code 可在右下角調整行尾為 LF

* `cannot open shared object file No such file or directory` <br>
  可能原因:
  1. `libGL.so.1: cannot open shared object file: No such file or directory`
      * 需安裝 Linux 套件: `apt-get install libgl1 libglib2.0-0`
      * 如果錯誤訊息來源為 python import Error 要看是哪個套件出錯 <br>
        例如: opencv 需安裝 `opencv-python-headless` 而非 `opencv-python`
  2. 動態連接庫的路徑錯誤
  3. 環境變數沒設定

* 有些套件會依賴 Ubuntu 的原生套件或核心函式庫，若 Ubuntu 版本太低會無法運行

* **同一個 container 本地可以運行成功，但放上 server 就不行** 🥲
  1. 查看 error message: <br>
    舉例 : 
      * mmcv 預設安裝的是 RTX30, RTX40 系列可使用的版本，放上 server (h100) 自然無法使用
      * 有些套件並非完全由 pip 套件版本決定，而是受到底層硬體支援（如 CPU 指令集）與動態載入的 native library 影響，如 faiss-cpu
  2. 檢查資源問題: 記憶體、GPU 等 <br>
      

# 其他
* pytorch 無聯網情況下載入權重需注意 <br>
1. 需加入 `weights_only=True` 避免下載模型細節: <br>
`torch.load(model_path, weights_only=True)` <br>
2. 若模型會強制下載權重，就更改下載路徑並事先下載好 <br>
`os.environ['TORCH_HOME']=‘<download path>’`

# Reference
https://yeasy.gitbook.io/docker_practice/