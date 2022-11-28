# Xây dựng 1 ứng dụng chat dùng hybrid architecture
Ứng dụng chat được xây dụng dùng ngôn ngữ Python và thư viện Tkinter cho phần giao diện. Ứng dụng là một phần của bài tập lớn 1 môn Mạng Máy Tính học kì 1 năm 2022-2023 tại trường Đại học Bách Khoa Tp.HCM
## Center Server
Center Server theo dõi, cập nhật danh sách các peer đang online. Peer cần ping lại cho center server sau 1 khoảng thời gian cố định nếu không sẽ bị disconnected.

Cách khởi tạo center server
```python
python center-server.py
```
## Peer
Mỗi peer sẽ đóng vai trò của server và client khi giao tiếp với các peer khác.

Cách khởi tạo peer
```python
python client.py
```
