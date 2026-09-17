# Báo cáo Day 5 — Segmentation Data Lab

- Mã học viên theo lớp: 2A202602188
- Ngày / CVAT local: 17/09/2026 / `http://localhost:8080`
- Công cụ đã dùng: CVAT local; script EoMT-DINOv3 để tạo mask gợi ý, sau đó xem ảnh/lớp phủ và chỉnh các ca theo quy tắc task. Object Medium đầu tiên được vẽ thủ công trước khi chạy gợi ý.

## 1. Bài đã nộp

Các ảnh dưới đây đã có annotation được lưu trong CVAT và ZIP export từ chính job. Cột điểm là điểm tối đa, không phải điểm tự chấm.

| Task | File ZIP đúng tên | Hoàn thành mấy ảnh | Điểm tối đa (coach chấm sau) |
| --- | --- | ---: | ---: |
| easy_semantic | `submissions/easy_semantic.zip` | 3 / 3 | 20 |
| medium_instance | `submissions/medium_instance.zip` | 3 / 3 | 32 |
| hard_panoptic | `submissions/hard_panoptic.zip` | 2 / 2 | 30 |
| cp1_holes | `submissions/cp1_holes.zip` | 1 / 1 | 3 |
| cp2_slice | `submissions/cp2_slice.zip` | 1 / 1 | 3 |
| cp5_occlusion | `submissions/cp5_occlusion.zip` | 1 / 1 | 3 |
| cp3_thin | `submissions/cp3_thin.zip` | 1 / 1 | 3 |
| cp4_curb | `submissions/cp4_curb.zip` | 1 / 1 | 3 |
| cp6_coverage | `submissions/cp6_coverage.zip` | 1 / 1 | 3 |
| **Tổng tối đa** | | **14 / 14** | **100** |

Đã chạy `python -X utf8 scripts/inspect_submissions.py --dir submissions`: cả chín ZIP đều `OK` về cấu trúc. Điều này chưa xác nhận độ chính xác của class, số object hay đường biên so với reference.

Sau khi nhận gói reference chính thức, đã tự chấm riêng ba tier bằng scorer của repo: Easy **17,8/20**, Medium **19,0/32**, Hard **16,1/30**, tổng **52,9/82**; xem `reports/tiers/SCORECARD.md`. Đây là phản hồi tự kiểm sau khi đã xem reference, không phải điểm chính thức hoặc điểm 100 của toàn bộ chín task. Sáu checkpoint chưa có reference để tự chấm.

## 2. Một quyết định trước khi dùng gợi ý

- Ảnh, vị trí và object Medium đầu tiên vẽ thủ công: `000000181542.jpg`, người đi bộ mặc áo dài sáng màu ở giữa ảnh (khoảng x=190–304, y=131–459). Một polygon `person` được vẽ theo dáng người nhìn thấy và lưu trong CVAT trước khi chạy gợi ý model.
- Class và quy tắc chọn biên: `person`; bám phần đầu, tay, thân, chân và giày nhìn thấy, dừng ở ranh với mặt đường/xe bên cạnh; không kéo mask qua vật khác.
- Nếu dùng gợi ý sau đó: gợi ý cho cùng người này không được nhập đè lên polygon thủ công để tránh tạo hai instance. Với các object khác, lớp phủ được xem lại và chỉ giữ class có trong `classes.json` của task.

## 3. Một lỗi tôi tìm thấy và sửa

- Task/ảnh/vùng: `medium_instance` / `000000181542.jpg` / góc dưới bên trái ảnh.
- Lỗi thuộc loại: thừa vật và sai lớp.
- Bằng chứng tôi nhìn thấy: mask gợi ý `bicycle` nằm trên phần xe bị cắt ở mép ảnh, trong khi không có một xe đạp riêng biệt để đếm tại vị trí này.
- Quy tắc và hành động sửa: xóa mask thừa đó trong CVAT, đồng thời rà các mảng kính xe buýt bị nhận nhầm thành `person`/`car`; bổ sung những người nhìn thấy rõ nhưng bị bỏ sót. Vật đếm được phải là từng instance thật, không phải mảnh ảnh hoặc phần của vật khác.
- Sau sửa đã Save và export lại chưa? Đã lưu trong CVAT, export lại `medium_instance.zip` và kiểm ZIP `OK`.

Lượt tự chấm đầu của Medium là **11,1/32** (P@0.5 **0,68**, R@0.5 **0,73**); sau các sửa trên và một lượt chỉnh biên là **19,0/32** (P@0.5 **0,89**, R@0.5 **0,89**). Kết quả này phản ánh cả nhóm sửa, không quy toàn bộ mức tăng cho riêng mask `bicycle`. Ở `cp3_thin`, gợi ý ban đầu bỏ sót `traffic sign` và `pole`; đã vẽ bổ sung biển/cột mảnh thủ công, lưu và export lại. Checkpoint này chưa có điểm reference.

## 4. Ba ca chưa chắc hoặc đã cân nhắc

| Ảnh/vị trí | Hai cách hiểu có thể | Quy tắc/chứng cứ | Quyết định hoặc câu hỏi cho coach |
| --- | --- | --- | --- |
| `000000144300.jpg`, bánh xe mô-tô lớn ở giữa (`cp1_holes`) | Khoét các khoảng tối trong nan hoa, hoặc giữ chúng trong mask của mô-tô | Quy tắc checkpoint nói kính/khe nằm trong mask vật, không khoét tùy tiện | Giữ các lỗ bên trong thuộc cùng một mask `motorcycle`; không tách bánh xe thành object mới. |
| `000000460147.jpg`, các làn xe bên trái dải cây giữa đường (`hard_panoptic`) | Gán `road` theo chức năng, hoặc `sidewalk` theo một vùng trong reference | Ảnh cho thấy ô-tô đang chạy trên làn này; khi so tự kiểm, một phần vùng đó trong reference lại mang lớp `sidewalk` | Giữ `road` theo quy tắc chức năng; xin coach xác nhận reference/ranh ở ảnh này vì khác biệt lớn làm giảm PQ `road`–`sidewalk`. |
| `7daa6479-67988f3f.jpg`, xe buýt trắng lớn ở giữa (`cp6_coverage`) | Ép xe buýt vào `car` để phủ thêm pixel, hoặc để trống vì không có `bus` trong schema | `classes.json` chỉ có `road`, `sidewalk`, `building`, `vegetation`, `sky`, `car`, `person`; sai class không giúp coverage đúng | Không gán xe buýt thành `car`. Cần coach xác nhận “phủ mọi pixel” ở checkpoint này nghĩa là mọi pixel thuộc lớp được cung cấp, không phải mọi pixel của ảnh. |
