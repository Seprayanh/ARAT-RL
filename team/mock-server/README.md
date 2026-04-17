# Mock Server - Features Service

模拟论文 Figure 1 中的 Features Service，支持有状态操作。

## 启动

```bash
pip install -r requirements.txt
python app.py
```

服务运行在 http://localhost:8080

## 操作依赖链（producer-consumer）## 触发 500 的方式
featureName 传入 `error` 即可触发服务器错误，供 ARAT-RL 捕获。
