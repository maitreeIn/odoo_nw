# Print Server

Print Server สำหรับ Odoo - รับ PDF จาก Odoo และส่งไปยังเครื่องพิมพ์โดยตรง

## คุณสมบัติ

- ✅ **Cross-Platform**: รองรับทั้ง Windows และ Linux (Auto-detect)
- ✅ **Mock Mode**: ทดสอบได้โดยไม่ต้องมีเครื่องพิมพ์จริง
- ✅ **REST API**: สื่อสารผ่าน HTTP API
- ✅ **Logging**: บันทึก log ทุก print job
- ✅ **Multiple Printers**: รองรับหลายเครื่องพิมพ์

## โครงสร้างโปรเจค

```
print_server/
├── app.py                      # Flask main application
├── config.py                   # Configuration
├── printers/
│   ├── __init__.py            # Factory (auto-detect OS)
│   ├── base.py                # Abstract base class
│   ├── mock_printer.py        # Mock printer for testing
│   ├── windows_printer.py     # Windows implementation
│   └── linux_printer.py       # Linux/CUPS implementation
├── utils/
│   ├── __init__.py
│   ├── pdf_handler.py         # PDF utilities
│   └── logger.py              # Logging configuration
├── requirements/
│   ├── base.txt               # Core dependencies
│   ├── windows.txt            # Windows dependencies
│   └── linux.txt              # Linux dependencies
├── logs/                       # Log files
└── .env.example               # Environment config template
```

## การติดตั้ง

### 1. ติดตั้ง Dependencies

**Linux:**
```bash
cd print_server
pip install -r requirements/linux.txt
```

**Windows:**
```bash
cd print_server
pip install -r requirements/windows.txt
```

### 2. Configuration

สร้างไฟล์ `.env` (หรือตั้งค่า environment variables):

```bash
cp .env.example .env
```

แก้ไขค่าใน `.env`:

```bash
# Mock Mode - ใช้สำหรับทดสอบ
MOCK_MODE=True

# ชื่อเครื่องพิมพ์จริง (เมื่อปิด Mock Mode)
PRINTER_A_NAME=YourDotMatrixPrinterName
PRINTER_B_NAME=YourThermalPrinterName
```

### 3. เริ่มใช้งาน

```bash
python app.py
```

Server จะรันที่ `http://localhost:5000`

## API Endpoints

### 1. Health Check
```bash
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-06T11:00:00",
  "mock_mode": true,
  "printer_handler": "MockPrinter"
}
```

### 2. List Printers
```bash
GET /api/printers
```

**Response:**
```json
{
  "success": true,
  "printers": [
    {
      "name": "PrinterA",
      "status": "ready",
      "type": "dot_matrix",
      "description": "Mock Dot Matrix Printer"
    },
    {
      "name": "PrinterB",
      "status": "ready",
      "type": "thermal",
      "description": "Mock Thermal Printer"
    }
  ],
  "count": 2
}
```

### 3. Print Document
```bash
POST /api/print
Content-Type: application/json

{
  "printer": "PrinterA",
  "pdf_data": "base64_encoded_pdf_here",
  "report_type": "invoice_delivery",
  "order_id": "SO001"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "mock_20251206_110000_123456",
  "printer": "PrinterA",
  "printer_alias": "PrinterA",
  "report_type": "invoice_delivery",
  "order_id": "SO001",
  "pdf_info": {
    "valid": true,
    "version": "1.4",
    "size": 12345,
    "size_kb": 12.06
  },
  "timestamp": "2025-12-06T11:00:00"
}
```

### 4. Get Job Status
```bash
GET /api/status/<job_id>
```

### 5. Mock Mode Only - List Jobs
```bash
GET /api/mock/jobs
```

### 6. Mock Mode Only - Clear Jobs
```bash
POST /api/mock/clear
```

## การทดสอบ

### 1. ทดสอบด้วย Mock Mode (ไม่ต้องมีเครื่องพิมพ์)

```bash
# ตั้งค่า Mock Mode
export MOCK_MODE=True

# เริ่ม server
python app.py

# ทดสอบ print (ในหน้าต่างใหม่)
curl -X POST http://localhost:5000/api/print \
  -H "Content-Type: application/json" \
  -d '{
    "printer": "PrinterA",
    "report_type": "invoice_delivery",
    "pdf_data": "'"$(base64 -w 0 test.pdf)"'",
    "order_id": "SO001"
  }'

# ตรวจสอบไฟล์ที่บันทึก
ls -lh /tmp/mock_prints/

# ดู log
cat logs/print_jobs.log
```

### 2. สร้างไฟล์ PDF ทดสอบ

```bash
# สร้าง PDF ทดสอบง่ายๆ
echo "Test Print" | ps2pdf - test.pdf
```

### 3. ทดสอบด้วย Virtual Printer (Linux)

```bash
# ติดตั้ง CUPS-PDF
sudo apt-get install cups-pdf

# ตั้งค่าให้ใช้เครื่องพิมพ์จริง
export MOCK_MODE=False
export PRINTER_A_NAME="PDF"
export PRINTER_B_NAME="PDF"

# เริ่ม server
python app.py

# ทดสอบพิมพ์ - ไฟล์จะปรากฏที่ ~/PDF/
```

### 4. ทดสอบด้วย Virtual Printer (Windows)

```powershell
# ใช้ Microsoft Print to PDF
$env:MOCK_MODE="False"
$env:PRINTER_A_NAME="Microsoft Print to PDF"
$env:PRINTER_B_NAME="Microsoft Print to PDF"

# เริ่ม server
python app.py
```

## Printer Mapping

| Printer Alias | ประเภท | ใช้สำหรับ |
|--------------|--------|-----------|
| PrinterA | Dot Matrix | บิลเงินสด/ใบส่งของ |
| PrinterB | Thermal | บิลเงินสด |

## Troubleshooting

### ปัญหา: Import Error

**Linux:**
```bash
# ติดตั้ง CUPS development files
sudo apt-get install libcups2-dev

# ติดตั้งใหม่
pip install -r requirements/linux.txt
```

**Windows:**
```bash
# ติดตั้ง pywin32
pip install pywin32
```

### ปัญหา: Printer Not Found

1. ตรวจสอบชื่อเครื่องพิมพ์:
```bash
# Linux
lpstat -p -d

# Windows
wmic printer get name
```

2. แก้ไขชื่อใน `.env`:
```bash
PRINTER_A_NAME=ชื่อเครื่องพิมพ์จริง
```

### ปัญหา: Permission Denied (Linux)

```bash
# เพิ่ม user เข้า lpadmin group
sudo usermod -a -G lpadmin $USER

# Logout และ login ใหม่
```

## Logs

Log files จะถูกบันทึกที่:
- **File**: `logs/print_jobs.log`
- **Console**: stdout

ตัวอย่าง log:
```
2025-12-06 11:00:00 - print_server - INFO - Print Job | ID: mock_20251206_110000 | Printer: PrinterA | Type: invoice_delivery | Order: SO001 | Size: 12.06 KB
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PRINT_SERVER_HOST` | `0.0.0.0` | Server host |
| `PRINT_SERVER_PORT` | `5000` | Server port |
| `DEBUG` | `False` | Debug mode |
| `MOCK_MODE` | `True` | Mock printer mode |
| `PRINTER_A_NAME` | `PrinterA` | Dot Matrix printer name |
| `PRINTER_B_NAME` | `PrinterB` | Thermal printer name |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_RETRIES` | `3` | Max print retries |
| `RETRY_DELAY` | `2` | Retry delay (seconds) |

## Production Deployment

### 1. ใช้ Production WSGI Server

```bash
# ติดตั้ง gunicorn
pip install gunicorn

# รัน server
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. ตั้งค่า Systemd Service (Linux)

สร้างไฟล์ `/etc/systemd/system/print-server.service`:

```ini
[Unit]
Description=Odoo Print Server
After=network.target

[Service]
Type=simple
User=odoo
WorkingDirectory=/path/to/print_server
Environment="MOCK_MODE=False"
Environment="PRINTER_A_NAME=YourPrinterA"
Environment="PRINTER_B_NAME=YourPrinterB"
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable และ start:
```bash
sudo systemctl enable print-server
sudo systemctl start print-server
sudo systemctl status print-server
```

## License

MIT
