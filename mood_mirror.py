import cv2
import mediapipe as mp
import time

# ---------- INIT ----------
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6)

mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not working 😭")
    exit()

last_capture_time = 0

print("Press 'q' or ESC to exit")

# ---------- LOOP ----------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_results = face_mesh.process(rgb)
    hand_results = hands.process(rgb)

    emotion = "Detecting..."
    confidence = 0

    # ---------- FACE EMOTION ----------
    if face_results.multi_face_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:

            lm = face_landmarks.landmark
            h, w, _ = frame.shape

            # key points
            left = lm[61]
            right = lm[291]
            top = lm[13]
            bottom = lm[14]

            lx, ly = int(left.x * w), int(left.y * h)
            rx, ry = int(right.x * w), int(right.y * h)
            tx, ty = int(top.x * w), int(top.y * h)
            bx, by = int(bottom.x * w), int(bottom.y * h)

            # metrics
            mouth_open = abs(by - ty)

            corner_avg_y = (ly + ry) / 2
            center_y = (ty + by) / 2
            curvature = center_y - corner_avg_y

            # classification
            if curvature > 4:
                emotion = "😊 HAPPY"
                confidence = min(100, int((curvature / 12) * 100))

            elif curvature < -3:
                emotion = "😢 SAD"
                confidence = min(100, int((abs(curvature) / 10) * 100))

            else:
                emotion = "😐 NEUTRAL"
                confidence = 50

            if mouth_open > 12:
                confidence = min(100, confidence + 10)

            # clean face box
            xs = [int(p.x * w) for p in lm]
            ys = [int(p.y * h) for p in lm]

            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # ---------- HAND GESTURE (✌️ = screenshot) ----------
    if hand_results.multi_hand_landmarks:
        for handLms in hand_results.multi_hand_landmarks:

            lm = handLms.landmark

            index_tip = lm[8].y
            middle_tip = lm[12].y
            ring_tip = lm[16].y

            # ✌️ gesture logic
            if (index_tip < lm[6].y and
                middle_tip < lm[10].y and
                ring_tip > lm[14].y):

                current_time = time.time()

                if current_time - last_capture_time > 2:
                    filename = f"screenshot_{int(current_time)}.png"
                    cv2.imwrite(filename, frame)
                    print("📸 Screenshot saved:", filename)

                    last_capture_time = current_time

            # small clean hand drawing
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

    # ---------- UI BOARD ----------
    overlay = frame.copy()
    cv2.rectangle(overlay, (20, 20), (360, 150), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    cv2.putText(frame, "AI Mood Mirror",
                (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (255, 255, 255), 2)

    cv2.putText(frame, emotion,
                (30, 90), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (0, 255, 0), 2)

    cv2.putText(frame, f"Confidence: {confidence}%",
                (30, 120), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (200, 200, 200), 2)

    # ---------- CONFIDENCE BAR ----------
    bar_x, bar_y = 30, 135
    bar_w, bar_h = 300, 12

    cv2.rectangle(frame,
                  (bar_x, bar_y),
                  (bar_x + bar_w, bar_y + bar_h),
                  (80, 80, 80), -1)

    fill_w = int((confidence / 100) * bar_w)
    cv2.rectangle(frame,
                  (bar_x, bar_y),
                  (bar_x + fill_w, bar_y + bar_h),
                  (0, 255, 0), -1)

    # ---------- DISPLAY ----------
    cv2.imshow("AI Mood Mirror Pro", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):
        break

# ---------- CLEANUP ----------
cap.release()
cv2.destroyAllWindows()