import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QHBoxLayout


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
            self.msleep(1)  # 1ms休憩

    def stop(self):
        self.running = False

# -----------------------------
# メイン画面
# -----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("e東京喰種")
        self.setGeometry(100, 100, 800, 600)

        # 状態変数
        self.random = 0
        self.cnt = 0
        self.now = 0
        self.ren = 0
        self.tokuzu2 = 0
        self.is_st = False

        # UI
        
        self.label_random = QLabel("乱数: 0")
        self.label_state = QLabel("状態: 通常")
        self.label_cnt = QLabel("回転数: 0")
        self.label_now = QLabel("差玉: 0")
        self.label_ren = QLabel("連荘数: 0")
        self.label_tokuzu = QLabel("保留: 0")
        '''
        layout = QVBoxLayout()
        layout.addWidget(self.label_random)
        layout.addWidget(self.label_state)
        layout.addWidget(self.label_cnt)
        layout.addWidget(self.label_now)
        layout.addWidget(self.label_ren)
        layout.addWidget(self.label_tokuzu)

        # 動画再生用
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        self.setLayout(layout)
        '''
        # -----------------------------
        # UI（ここから差し替え）
        # -----------------------------

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

        # レイアウト反映
        self.setLayout(main_layout)


        # 抽選スレッド
        self.thread_normal = RouletteThread(is_st=False)
        self.thread_st = RouletteThread(is_st=True)

        self.thread_normal.update_signal.connect(self.update_random)
        self.thread_st.update_signal.connect(self.update_random)
        self.thread_st.st_hit_signal.connect(self.play_movie)

        self.thread_normal.start()
        self.thread_st.start()

    # キー入力で乱数取得
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Down:
            self.cnt += 1
            self.label_cnt.setText(f"回転数: {self.cnt}")
            if self.is_st:
                self.rush()
            else:
                self.normal()

    # 乱数表示
    def update_random(self, value):
        self.random = value
        self.label_random.setText(f"乱数: {value}")

    # 通常
    def normal(self):
        self.play_movie("通常.mp4")
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
            self.play_movie("先バレ.mp4")
            self.is_st = True
            self.now += 1400
            self.ren += 1
            self.cnt = 0
            self.label_state.setText("状態: ST")
        else:
            self.now -= 15
            self.label_state.setText("状態: ハズレ")
        self.label_now.setText(f"差玉: {self.now}")
        self.label_ren.setText(f"連荘数: {self.ren}")

    # ST
    def rush(self):
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

    # 動画再生
    def play_movie(self,filename):
        url = QUrl.fromLocalFile(filename)
        if self.player.source() == url:
            return

        self.player.setSource(url)
        self.player.play()

# -----------------------------
# main
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
