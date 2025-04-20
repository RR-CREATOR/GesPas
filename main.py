import sys
import cv2
import time
import json
import numpy as np
import mediapipe as mp

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QStackedLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class GestureApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🔒 Gesture Password Manager")
        self.setFixedSize(640, 720)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('#fdfdfd'))
        self.setPalette(palette)

        self.hands = mp_hands.Hands(
            model_complexity=0,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.saved_passwords = {}
        self.current_save = ''
        self.record_interval = 3.0
        self.recorded_gestures = []
        self.match_gestures = []
        self.current_index = 0
        self.start_time = 0.0
        self.mode = ''  # 'record', 'preview', 'match'

        self.stack = QStackedLayout()
        self.home_page = self.init_home()
        self.record_page = self.init_record()
        self.match_page = self.init_match()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.record_page)
        self.stack.addWidget(self.match_page)

        container = QWidget()
        container.setLayout(self.stack)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(container)
        self.setLayout(main_layout)

        self.load_data()

    def closeEvent(self, event):
        self.timer.stop()
        self.capture.release()
        cv2.destroyAllWindows()
        super().closeEvent(event)

    def load_data(self):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
            for name, entry in data.items():
                entry['gestures'] = [np.array(g) for g in entry.get('gestures', [])]
            self.saved_passwords = data
        except:
            self.saved_passwords = {}
        self.refresh_list()

    def save_data(self):
        output = {}
        for name, entry in self.saved_passwords.items():
            output[name] = {
                'password': entry['password'],
                'gestures': [g.tolist() for g in entry['gestures']]
            }
        with open('data.json', 'w') as f:
            json.dump(output, f)

    def refresh_list(self):
        self.pw_list.clear()
        for name in self.saved_passwords:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)

            label = QLabel(name)
            label.setFont(QFont('Arial', 14))

            delete_btn = QPushButton('🗑️')
            delete_btn.setFixedSize(24, 24)
            delete_btn.setStyleSheet('border:none;')
            delete_btn.clicked.connect(lambda _, n=name: self.delete_password(n))

            layout.addWidget(label)
            layout.addStretch()
            layout.addWidget(delete_btn)

            item.setSizeHint(widget.sizeHint())
            self.pw_list.addItem(item)
            self.pw_list.setItemWidget(item, widget)

    def init_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel('🔐 Saved Passwords')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QHBoxLayout()
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText('Save Name')
        self.name_in.setFixedHeight(36)

        self.pwd_in = QLineEdit()
        self.pwd_in.setPlaceholderText('Password')
        self.pwd_in.setEchoMode(QLineEdit.Password)
        self.pwd_in.setFixedHeight(36)

        self.eye_btn = QPushButton('🙈')
        self.eye_btn.setFixedSize(28, 28)
        self.eye_btn.setCheckable(True)
        self.eye_btn.setStyleSheet('border:none;')
        self.eye_btn.clicked.connect(self.toggle_eye)

        form.addWidget(self.name_in)
        form.addWidget(self.pwd_in)
        form.addWidget(self.eye_btn)
        layout.addLayout(form)

        add_btn = QPushButton('➕ Add Password')
        add_btn.setStyleSheet('background:#4caf50;color:white;padding:8px;border-radius:4px;')
        add_btn.clicked.connect(self.add_password)
        layout.addWidget(add_btn)

        self.pw_list = QListWidget()
        self.pw_list.setFixedHeight(300)
        self.pw_list.itemClicked.connect(self.select_item)
        layout.addWidget(self.pw_list)

        self.home_pw = QLabel('')
        self.home_pw.setFont(QFont('Arial', 16))
        self.home_pw.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.home_pw)

        return page

    def init_record(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel('🎥 Record Gestures')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.total_lbl = QLabel('Total gestures: 0')
        self.total_lbl.setFont(QFont('Arial', 16))
        self.total_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.total_lbl)

        self.gest_lbl = QLabel('Gesture 1')
        self.gest_lbl.setFont(QFont('Arial', 16))
        self.gest_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.gest_lbl)

        self.count_lbl = QLabel('Waiting...')
        self.count_lbl.setFont(QFont('Arial', 16))
        self.count_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_lbl)

        self.notify_lbl = QLabel('')
        self.notify_lbl.setFont(QFont('Arial', 14))
        self.notify_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.notify_lbl)

        interval_layout = QHBoxLayout()
        self.int_in = QLineEdit()
        self.int_in.setPlaceholderText('Seconds between gestures')
        self.int_in.setFixedHeight(36)

        set_btn = QPushButton('✔ Set')
        set_btn.clicked.connect(self.set_interval)
        interval_layout.addWidget(self.int_in)
        interval_layout.addWidget(set_btn)
        layout.addLayout(interval_layout)

        rec_layout = QHBoxLayout()
        self.start_btn = QPushButton('⏺ Start')
        self.start_btn.setStyleSheet('background:#2196f3;color:white;')
        self.start_btn.clicked.connect(self.start_record)

        self.stop_btn = QPushButton('⏹ Stop')
        self.stop_btn.setStyleSheet('background:#f44336;color:white;')
        self.stop_btn.clicked.connect(self.stop_record)

        rec_layout.addWidget(self.start_btn)
        rec_layout.addWidget(self.stop_btn)
        layout.addLayout(rec_layout)

        preview_btn = QPushButton('🔍 Preview')
        preview_btn.clicked.connect(self.preview)
        layout.addWidget(preview_btn)

        done_btn = QPushButton('✔ Done')
        done_btn.setStyleSheet('background:#ff9800;color:white;')
        done_btn.clicked.connect(self.finish_setup)
        layout.addWidget(done_btn)

        return page

    def init_match(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel('🔓 Match Gestures')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.match_lbl = QLabel('Gesture 1')
        self.match_lbl.setFont(QFont('Arial', 16))
        self.match_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.match_lbl)

        self.match_pw = QLabel('')
        self.match_pw.setFont(QFont('Arial', 18))
        self.match_pw.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.match_pw)

        self.back_to_record_btn = QPushButton('↩ Back')
        self.back_to_record_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.back_to_record_btn.hide()
        layout.addWidget(self.back_to_record_btn)

        self.back_to_home_btn = QPushButton('↩ Back')
        self.back_to_home_btn.clicked.connect(self.to_home)
        self.back_to_home_btn.hide()
        layout.addWidget(self.back_to_home_btn)

        return page

    def toggle_eye(self):
        if self.eye_btn.isChecked():
            self.pwd_in.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText('👁️')
        else:
            self.pwd_in.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText('🙈')

    def add_password(self):
        name = self.name_in.text().strip()
        pwd = self.pwd_in.text().strip()

        if not name or not pwd:
            QMessageBox.warning(self, 'Error', 'Enter both')
            return

        if name in self.saved_passwords:
            QMessageBox.warning(self, 'Error', 'Name exists')
            return

        self.saved_passwords[name] = {'password': pwd, 'gestures': []}
        self.save_data()
        self.refresh_list()
        self.name_in.clear()
        self.pwd_in.clear()
        self.home_pw.clear()
        self.current_save = name
        self.start_record()

    def delete_password(self, name):
        if name in self.saved_passwords:
            del self.saved_passwords[name]
        self.save_data()
        self.refresh_list()
        self.home_pw.clear()

    def select_item(self, item):
        idx = self.pw_list.row(item)
        self.current_save = list(self.saved_passwords.keys())[idx]
        self.start_match()

    def set_interval(self):
        try:
            self.record_interval = float(self.int_in.text())
        except:
            self.record_interval = 3.0

    def start_record(self):
        self.recorded_gestures = []
        self.current_index = 1
        self.mode = 'record'
        self.start_time = time.time()
        self.stack.setCurrentIndex(1)
        self.timer.start(50)

    def preview(self):
        if not self.recorded_gestures:
            QMessageBox.information(self, 'Info', 'No gestures')
            return

        self.match_gestures = self.recorded_gestures
        self.current_index = 0
        self.match_pw.clear()
        self.mode = 'preview'
        self.back_to_record_btn.show()
        self.back_to_home_btn.hide()
        self.stack.setCurrentIndex(2)
        self.timer.start(50)

    def start_match(self):
        self.match_gestures = self.saved_passwords[self.current_save]['gestures']
        self.current_index = 0
        self.match_pw.clear()
        self.mode = 'match'
        self.back_to_record_btn.hide()
        self.back_to_home_btn.show()
        self.stack.setCurrentIndex(2)
        self.timer.start(50)

    def stop_record(self):
        self.timer.stop()
        self.saved_passwords[self.current_save]['gestures'] = self.recorded_gestures
        self.save_data()
        self.gest_lbl.setText('Gesture 0')
        self.count_lbl.setText('0s')
        self.start_btn.setText('🔄 Restart')

    def finish_setup(self):
        self.stop_record()
        self.to_home()

    def to_home(self):
        self.timer.stop()
        self.stack.setCurrentIndex(0)

    def update_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        disp = frame.copy()

        if not results.multi_hand_landmarks:
            cv2.imshow('Camera', disp)
            if cv2.waitKey(1) & 0xFF == 27:
                self.to_home()
            return

        lands = list(results.multi_hand_landmarks)
        if len(lands) == 1:
            lands.append(lands[0])

        all_lm = [p for h in lands for p in h.landmark]
        for p in all_lm:
            x = int(p.x * frame.shape[1])
            y = int(p.y * frame.shape[0])
            cv2.circle(disp, (x, y), 6, (0, 128, 255), -1)

        data = self.calculate_distances(all_lm)
        total = (len(self.recorded_gestures)
                 if self.mode == 'record' else len(self.match_gestures))

        if self.mode == 'record':
            elapsed = time.time() - self.start_time
            left = max(0, self.record_interval - elapsed)
            self.count_lbl.setText(f'{int(left) + 1}s')
            self.gest_lbl.setText(f'Gesture {self.current_index}')
            self.total_lbl.setText(f'Total gestures: {total}')

            if elapsed >= self.record_interval:
                self.recorded_gestures.append(data)
                self.notify_lbl.setText('Gesture saved')
                QTimer.singleShot(500, lambda: self.notify_lbl.setText(''))
                self.current_index += 1
                self.start_time = time.time()
        else:
            self.match_lbl.setText(f'Gesture {self.current_index + 1}')
            target = self.match_gestures[self.current_index]
            if data.shape == target.shape and np.allclose(data, target, rtol=0.08, atol=0.12):
                self.current_index += 1
                time.sleep(0.3)
                if self.current_index >= total:
                    if self.mode == 'match':
                        self.match_pw.setText(
                            f'Password: {self.saved_passwords[self.current_save]["password"]}'
                        )
                    else:
                        self.match_pw.setText('All gestures matched successfully!')
                    self.timer.stop()

        cv2.imshow('Camera', disp)
        if cv2.waitKey(1) & 0xFF == 27:
            self.to_home()

    def calculate_distances(self, lm):
        dists = []
        for i in range(len(lm)):
            for j in range(i + 1, len(lm)):
                dx = lm[i].x - lm[j].x
                dy = lm[i].y - lm[j].y
                dists.append(np.hypot(dx, dy))
        return np.array(dists)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = GestureApp()
    win.show()
    sys.exit(app.exec_())
