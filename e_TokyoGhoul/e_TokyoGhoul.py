import sys
import numpy as np
import glob
import subprocess
import os
from PyQt6.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QHBoxLayout
from collections import deque


# -----------------------------
# ずっと動かすメイン抽選
# -----------------------------
class RouletteThread(QThread):
    update_signal = pyqtSignal(int)  # 乱数更新通知
    st_hit_signal = pyqtSignal()     # 先バレ

    def __init__(self, is_st=False, parent=None):
        super().__init__(parent)
        self.is_st = is_st # True or False
        self.rng = np.random.default_rng()
        self.value = 0

    def run(self):
        while True:
            if self.is_st:
                self.value = self.rng.integers(0, 76239)
            else:
                self.value = self.rng.integers(0, 79999)
            self.update_signal.emit(self.value)
            self.msleep(1) # これ入れないとロンフリ

    def stop(self):
        self.running = False

# -----------------------------
# 画面表示
# -----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("e東京喰種")
        self.setGeometry(100, 100, 800, 600)
        
        # 動画のqueue
        self.video_queue_normal = deque()
        self.video_queue_st = deque()
        self.video_queue_hit = deque()
        self.video_queue_miss = deque()

        self.load_video("通常")
        self.load_video("ST")
        self.load_video("当たり")
        self.load_video("はずれ")

        # 状態変数
        self.random = 0
        self.cnt = 0
        self.now = 0
        self.ren = 0
        self.tokuzu2 = 0
        self.is_st = False
        self.rd_queue = deque(maxlen=4) #保留は4個まで 0から貯まる際は即消化されるため

        # 保留を監視する(100msごと)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)

        # UI
        self.label_random = QLabel("乱数: 0")
        self.label_state = QLabel("状態: 通常")
        self.label_cnt = QLabel("回転数: 0")
        self.label_now = QLabel("差玉: 0")
        self.label_ren = QLabel("連荘数: 0")
        self.label_tokuzu = QLabel("保留: 0")

        # 左右レイアウト
        main_layout = QHBoxLayout(self)

        # 左側（情報表示）
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.label_random)
        left_layout.addWidget(self.label_state)
        left_layout.addWidget(self.label_cnt)
        left_layout.addWidget(self.label_now)
        left_layout.addWidget(self.label_ren)
        left_layout.addWidget(self.label_tokuzu)

        main_layout.addLayout(left_layout, 1)  # 左は少しだけ広く

        # 動画表示（右側）
        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)  # 黒帯防止
        main_layout.addWidget(self.video_widget, 3)  # 右を広く

        # プレイヤー設定
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        self.is_playing = False  # 再生中フラグ
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

        # レイアウト反映
        self.setLayout(main_layout)

        # 抽選スレッド
        self.thread_normal = RouletteThread(is_st=False)
        self.thread_st = RouletteThread(is_st=True)

        self.thread_normal.update_signal.connect(self.update_random)
        self.thread_st.update_signal.connect(self.update_random)
        self.thread_st.st_hit_signal.connect(self.play_video)

        self.thread_normal.start()
        self.thread_st.start()

    # キー入力で乱数取得
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Down:
            self.rd_queue.append(self.random) # 保留(乱数保存)

    # 乱数表示(これは常に変動している乱数を取るもの)
    def update_random(self, value):
        self.random = value
        self.label_random.setText(f"乱数: {value}")

    # 通常
    def normal(self,random_value):
        self.random = random_value
        if self.random <= 1:
            self.is_st = True
            self.now += 270
            self.ren += 1
            self.cnt = 0
            self.label_state.setText("状態: ST")
        elif self.random < 200:
            self.now += 270
            self.cnt = 0
            self.label_state.setText("状態: 喰種CHARGE")
        elif self.random < 300:
            self.now += 1400
            self.cnt = 0
            self.label_state.setText("状態: 通常当たり")
        elif self.random < 400:
            self.play_video("先バレ.mp4")
            self.is_st = True
            self.now += 1400
            self.ren += 1
            self.cnt = 0
            self.label_state.setText("状態: ST")
        else:
            self.play_video_from_queue("通常")
            self.now -= 15
            self.label_state.setText("状態: ハズレ")
        self.label_now.setText(f"差玉: {self.now}")
        self.label_ren.setText(f"連荘数: {self.ren}")

    # ST
    def rush(self,random):
        if self.tokuzu2 > 0:
            self.now += 1390
            self.tokuzu2 -= 1
            self.cnt = 0
            if self.random < 2287 and self.tokuzu2 == 0:
                self.tokuzu2 = 2
        elif self.cnt < 130:
            if self.random < 800:
                self.tokuzu2 = 2
                self.ren += 1
                self.label_state.setText("状態: 当たり")
            else:
                self.label_state.setText("状態: ハズレ")
        else:
            self.is_st = False
            self.now -= 15
            self.ren = 0
            self.label_state.setText("状態: ST終了")
        self.label_now.setText(f"差玉: {self.now}")
        self.label_tokuzu.setText(f"保留: {self.tokuzu2}")
        self.label_ren.setText(f"連荘数: {self.ren}")

    # 動画リストをqueueへ
    def load_video(self,folder):
        name = os.path.basename(folder)
        files = glob.glob(f"{folder}/*.mp4")
        files.sort(key=lambda x: int(''.join(c for c in os.path.basename(x) if c.isdigit()) or 0))

        if "通常" in name:
            self.video_queue_normal.extend(files)
        elif "ST" in name:
            self.video_queue_st.extend(files)
        elif "当たり" in name:
            self.video_queue_hit.extend(files)
        elif "はずれ" in name:
            self.video_queue_miss.extend(files)

    # 動画再生
    def play_video(self,filename):
        if self.is_playing:
            return  # 再生中なら無視
        self.is_playing = True
        url = QUrl.fromLocalFile(filename)
        self.player.setSource(url)
        self.player.play()

    # 保留消化
    def consume(self):
        random = self.rd_queue.popleft()
        return random

    # 保留のチェック
    def check_queue(self):
        if self.rd_queue and not self.is_playing: # 保留があり、非動画再生時
            random_value = self.consume()

            self.cnt += 1
            self.label_cnt.setText(f"回転数: {self.cnt}")

            if self.is_st:
                self.rush(random_value)
            else:
                self.normal(random_value)

    def play_video_from_queue(self, state):
        if state == "通常" and self.video_queue_normal:
            filename = self.video_queue_normal.popleft()
            self.video_queue_normal.append(filename)  # 元に戻す(動画の循環を実現)
        elif state == "ST" and self.video_queue_st:
            filename = self.video_queue_st.popleft()
            self.video_queue_st.append(filename)
        elif state == "当たり" and self.video_queue_hit:
            filename = self.video_queue_hit.popleft()
            self.video_queue_hit.append(filename)
        elif state == "はずれ" and self.video_queue_miss:
            filename = self.video_queue_miss.popleft()
            self.video_queue_miss.append(filename)

        self.play_video(filename)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.is_playing = False
            self.check_queue()  # 終了したら次の保留を再生

# -----------------------------
# main
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
