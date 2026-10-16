# Selenium Python Testing

ชุดทดสอบ UI และ Validation ของ Pet Hydro-Feed Calculator สำหรับ Tester สมาชิกคนที่ 2 ใช้ Selenium Python และ pytest ตามโครงสร้างตัวอย่างอาจารย์

## เตรียมระบบ

ติดตั้ง Python 3.12 ขึ้นไป, uv และ Google Chrome โดย Selenium Manager จะเตรียม ChromeDriver ให้อัตโนมัติ

เปิดแอป pet-hydro-feed-calculator แยกจากชุดทดสอบนี้ หากใช้ Docker ให้เปิด Docker Desktop แล้วรันในโฟลเดอร์แอป:

```powershell
docker compose up --build -d
docker compose ps
```

ตรวจพอร์ตที่เปิดให้เครื่องเข้าถึง เช่น `8100->3000/tcp` ใช้ URL `http://127.0.0.1:8100` และเปิดแอปค้างไว้ขณะทดสอบ

## รันชุดทดสอบ

เปิด Terminal ในโฟลเดอร์ selenium-python-testing:

```powershell
uv sync --locked
uv run pytest --base-url http://127.0.0.1:8100
```

รันแบบไม่แสดงหน้าต่าง Chrome และบันทึกผล:

```powershell
uv run pytest --headless --base-url http://127.0.0.1:8100 --junitxml=test-results/results.xml
```

รันเฉพาะการตรวจน้ำหนัก:

```powershell
uv run pytest -v -k ft_val_06
```

เปลี่ยนพอร์ตใน --base-url ให้ตรงกับแอปที่เปิดไว้ ใช้ระบบทดสอบในเครื่อง ชุดทดสอบสร้างข้อมูลผ่านหน้าเว็บและลบเฉพาะรายการที่มี UUID ของตัวเองหลังจบ

## ขอบเขต 25 เทส

| รหัส | เรื่องที่ทดสอบ | จำนวน |
|---|---|---:|
| FT-VAL-02 | ฟอร์มว่าง ข้อความเตือนสีแดง และไม่ส่งคำขอบันทึก | 1 |
| FT-VAL-03 | ชื่อว่างและช่องว่างล้วน | 2 |
| FT-VAL-04 | ป้องกันตัวอักษรในน้ำหนัก โดย abc เหลือว่างและไม่บันทึก ส่วน 10abc เหลือ 10 และบันทึกน้ำหนัก 10 ได้ | 4 |
| FT-VAL-05 | น้ำหนักว่าง ศูนย์ และติดลบ | 3 |
| FT-VAL-06 | สุนัขน้ำหนัก 0.1 ต้องเตือนช่วง 0.5–100 kg และไม่บันทึก ส่วน 2.5 และ 10 บันทึกได้ | 3 |
| FT-VAL-07 | ไม่เลือกประเภทหรือกิจกรรม และทดสอบคู่สุนัข/แมวกับกิจกรรม 3 ระดับ | 8 |
| FT-VAL-08 | แก้ไขข้อมูลหลังแจ้งเตือนแล้วบันทึก | 1 |
| FT-VAL-09 | องค์ประกอบหน้าและการอัปเดต Preview | 1 |
| FT-VAL-10 | หน้าจอมือถือ 375×812 และเดสก์ท็อป 1366×768 | 2 |

การแทรกข้อความทั้งชุดใน FT-VAL-04 ใช้ Chrome Input.insertText ไม่ใช่ clipboard ของระบบปฏิบัติการ ส่วน Responsive ตรวจขอบหน้าจอและการใช้งาน ควรตรวจความเรียบร้อยด้วยสายตาเพิ่มเติม

## โครงสร้างไฟล์

- tests/test_ui_validation.py ขั้นตอนทดสอบและเงื่อนไข assert
- tests/conftest.py เตรียม Chrome สังเกตคำขอบันทึก และล้างข้อมูลทดสอบ
- main.py ตัวเรียก pytest ผ่าน Python
- pyproject.toml และ uv.lock กำหนดและล็อก dependencies
- requirements.txt สำหรับติดตั้งผ่าน pip

ผลทดสอบแสดงใน Terminal และภาพหน้าจอพร้อม HTML จะถูกเก็บใน test-results เมื่อเคสไม่ผ่าน ไม่รวมผลทดสอบเก่าหรือฐานข้อมูลใน repository
