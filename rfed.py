import sys
import eyed3
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QTableWidgetItem, QMenu, QAction, QHeaderView
from PyQt5.QtCore import QUrl, QTime, pyqtSignal
from PyQt5.uic import loadUi
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


class MusicPlayerApp(QWidget):
    filesDropped = pyqtSignal(list)

    def __init__(self):
        super(MusicPlayerApp, self).__init__()
        loadUi('app/ui/music_player.ui', self)

        try:
            with open("app/resources/style.qss") as f:
                style = f.read()
                self.setStyleSheet(style)
        except FileNotFoundError:
            print("Stylesheet file not found")
        except Exception as e:
            print(f"Error loading stylesheet: {str(e)}")

        # Load icons for push buttons
        self.pushButton_2.setIcon(QIcon('app/resources/Icons/play.svg'))
        self.pushButton.setIcon(QIcon('app/resources/Icons/backward-step.svg'))
        self.pushButton_3.setIcon(QIcon('app/resources/Icons/forward-step.svg'))
        self.pushButton_4.setIcon(QIcon('app/resources/Icons/upload.svg'))
        self.pushButton_5.setIcon(QIcon('app/resources/Icons/list.svg'))
        self.pushButton_6.setIcon(QIcon('app/resources/Icons/pied-piper-alt.svg'))
        self.pushButton_7.setIcon(QIcon('app/resources/Icons/shuffle.svg'))
        self.pushButton_8.setIcon(QIcon('app/resources/Icons/repeat.svg'))

        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)

        self.media_player = QMediaPlayer()
        self.media_player.positionChanged.connect(self.update_progress)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)

        self.playlist = []
        self.current_track_index = 0

        self.tableWidget.setShowGrid(False)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.verticalHeader().setVisible(False)

        self.pushButton_2.clicked.connect(self.play_music)
        self.pushButton.clicked.connect(self.rewind)
        self.pushButton_3.clicked.connect(self.skip_song)
        self.horizontalSlider.valueChanged.connect(self.set_volume)
        self.pushButton_4.clicked.connect(self.add_to_playlist)
        self.pushButton_5.clicked.connect(self.toggle_playlist)
        self.pushButton_6.clicked.connect(self.toggle_album_sampler)

        self.tableWidget.itemDoubleClicked.connect(self.play_selected_song)

        self.label.setText("")
        self.label_2.setText("")

        initial_volume = int(self.media_player.volume() / 4)
        self.horizontalSlider.setValue(initial_volume)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.check_track_end)
        self.timer.start(1000)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Connect the filesDropped signal to the add_to_playlist method
        self.filesDropped.connect(self.add_to_playlist)

        # Context menu for playlist items
        self.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.show_context_menu)

        # Show the playlist initially
        self.playlist_visible = True
        self.update_playlist_visibility()

        # Album sampler mode
        self.album_sampler_mode = False
        self.album_sampler_timer = QtCore.QTimer(self)
        self.album_sampler_timer.timeout.connect(self.album_sampler_timeout)
        self.album_sampler_duration = 30000  # 30 seconds

    def toggle_playlist(self):
        # Toggle the playlist visibility
        self.playlist_visible = not self.playlist_visible
        self.update_playlist_visibility()

    def update_playlist_visibility(self):
        # Update the visibility of the playlist
        if self.playlist_visible:
            self.tableWidget.show()
        else:
            self.tableWidget.hide()

    def toggle_album_sampler(self):
        # Toggle the album sampler mode
        self.album_sampler_mode = not self.album_sampler_mode
        self.update_album_sampler_button()

        if self.album_sampler_mode:
            # Start the album sampler timer
            self.album_sampler_timer.start(self.album_sampler_duration)
            # Play the current song
            self.play_music()
        else:
            # Stop the album sampler timer
            self.album_sampler_timer.stop()

    def update_album_sampler_button(self):
        # Update the font color of pushButton_6 based on the album sampler mode
        if self.album_sampler_mode:
            self.pushButton_6.setStyleSheet(
                "QPushButton#pushButton_6 { color: red; }"
            )
        else:
            self.pushButton_6.setStyleSheet("QPushButton#pushButton_6 { color: black; }")

    def album_sampler_timeout(self):
        # Timeout for the album sampler mode
        self.skip_song()

    def show_context_menu(self, position):
        menu = QMenu(self)
        remove_action = QAction("Remove from Playlist", self)
        remove_action.triggered.connect(self.remove_from_playlist)
        menu.addAction(remove_action)

        menu.exec_(self.tableWidget.mapToGlobal(position))

    def remove_from_playlist(self):
        selected_items = self.tableWidget.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            if 0 <= row < len(self.playlist):
                del self.playlist[row]
                self.update_playlist_table()

    def dropEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            files = [url.toLocalFile() for url in mime_data.urls()]
            # Emit the filesDropped signal with the list of dropped files
            self.filesDropped.emit(files)

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            event.acceptProposedAction()

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if not self.album_sampler_mode:
                self.current_track_index += 1
                if self.current_track_index < len(self.playlist):
                    self.play_music()
                else:
                    self.current_track_index = 0

    def check_track_end(self):
        if (
                self.media_player.state() == QMediaPlayer.PlayingState
                and self.media_player.position() >= self.media_player.duration()
        ):
            if not self.album_sampler_mode:
                self.current_track_index += 1
                if self.current_track_index < len(self.playlist):
                    self.play_music()
                else:
                    self.current_track_index = 0

    def play_selected_song(self, item):
        row = item.row()
        self.current_track_index = row
        self.play_music()

    def play_music(self):
        if self.playlist:
            track_info = self.playlist[self.current_track_index]
            media_content = QMediaContent(QUrl.fromLocalFile(track_info['path']))
            self.media_player.setMedia(media_content)
            self.media_player.play()
            self.update_currently_playing_song()
            self.label.setText(track_info['title'])
            self.label_2.setText(track_info['artist'])

    def rewind(self):
        position = self.media_player.position() - 5000
        self.media_player.setPosition(max(position, 0))

    def skip_song(self):
        self.current_track_index += 1
        if self.current_track_index < len(self.playlist):
            self.play_music()
        else:
            self.current_track_index = 0

    def update_progress(self, position):
        duration = self.media_player.duration()
        if duration > 0:
            progress = int((position / duration) * 100)
            self.progressBar.setValue(progress)
        time_played = QTime(0, 0).addMSecs(position)
        self.label_3.setText(time_played.toString("mm:ss"))

    def update_duration(self, duration):
        remaining_time = QTime(0, 0).addMSecs(duration - self.media_player.position())
        self.label_4.setText(remaining_time.toString("mm:ss"))

    def set_volume(self, value):
        self.media_player.setVolume(value)

    def add_to_playlist(self, files):
        if files:
            for file in files:
                audiofile = eyed3.load(file)
                if audiofile and audiofile.tag:
                    title = audiofile.tag.title if audiofile.tag.title else "Unknown Title"
                    artist = audiofile.tag.artist if audiofile.tag.artist else "Unknown Artist"
                    length = audiofile.info.time_secs if audiofile.info.time_secs else 0
                    track_info = {'title': title, 'artist': artist, 'length': length, 'path': file}
                    self.playlist.append(track_info)
            self.update_playlist_table()

    def update_playlist_table(self):
        self.tableWidget.setRowCount(0)
        for i, track_info in enumerate(self.playlist):
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(track_info['title']))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(track_info['artist']))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(self.format_length(track_info['length'])))

    def update_currently_playing_song(self):
        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                item.setBackground(QtGui.QColor(255, 255, 255))
        if 0 <= self.current_track_index < self.tableWidget.rowCount():
            for j in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(self.current_track_index, j)
                item.setBackground(QtGui.QColor(0, 128, 255))

    def format_length(self, length):
        minutes, seconds = divmod(length, 60)
        return f"{int(minutes):02d}:{int(seconds):02d}"


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MusicPlayerApp()
    mainWin.show()
    sys.exit(app.exec_())
