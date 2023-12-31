import sys
from datetime import datetime
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QCalendarWidget, QLabel,
                             QHBoxLayout, QPushButton, QVBoxLayout, QLineEdit,
                             QListWidget, QMessageBox, QInputDialog, QLCDNumber,
                             QTextEdit, QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import QDate, Qt, QTimer, QTime
from PyQt5 import QtGui
from PyQt5.QtGui import QTextCharFormat, QColor, QPixmap
from os import path


class Calendar(QWidget):
    # keep the current time as class variable for reference
    currentDay = str(datetime.now().day).rjust(2, '0')
    currentMonth = str(datetime.now().month).rjust(2, '0')
    currentYear = str(datetime.now().year).rjust(2, '0')

    def __init__(self, width, height):
        super().__init__()
        folder = path.dirname(__file__)
        self.icon_folder = path.join(folder, "icons")

        self.setWindowTitle("Planner")
        self.setWindowIcon(QtGui.QIcon(path.join(self.icon_folder, 'window.png')))

        self.setGeometry(width // 4, height // 4, width // 2, height // 2)
        self.initUI()

    def initUI(self):
        # Initialize QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(QtGui.QIcon(path.join(self.icon_folder, 'icon.png')), self)
        self.tray_icon.setToolTip('Planner')

        # Create a context menu for the system tray icon
        menu = QMenu(self)
        show_action = QAction('Show', self)
        quit_action = QAction('Quit', self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.close)

        menu.addAction(show_action)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)

        # Initialize vbox
        vbox = QVBoxLayout()

        # Add notes_textedit to vbox
        self.notes_textedit = QTextEdit()
        addNotesButton = QPushButton("Add Notes")
        addNotesButton.clicked.connect(self.addNote)  # Connect the button to the addNote method

        # Add the QTextEdit and the "Add Notes" button to vbox
        vbox.addWidget(self.notes_textedit)
        vbox.addWidget(addNotesButton)

        # don't allow going back to past months in calendar
        self.calendar.setMinimumDate(QDate(int(self.currentYear), int(self.currentMonth), 1))

        # format for dates in calendar that have events
        self.fmt = QTextCharFormat()
        self.fmt.setBackground(QColor(255, 165, 0, 100))

        # format for the current day
        cur_fmt = QTextCharFormat()
        cur_fmt.setBackground(QColor(0, 255, 90, 70))

        # format to change back to if all events are deleted
        self.delfmt = QTextCharFormat()
        self.delfmt.setBackground(Qt.transparent)

        # check if json file exists, if it does load the data from it
        file_exists = path.isfile(path.join(path.dirname(__file__), "data.json"))
        if file_exists:
            with open("data.json", "r") as json_file:
                self.data = json.load(json_file)
        else:
            self.data = {}

        # delete data from days prior to the current day
        cur = QDate.currentDate()
        for date in list(self.data.keys()):
            check_date = QDate.fromString(date, "ddMMyyyy")
            if cur.daysTo(check_date) <= 0 and cur != check_date:
                self.data.pop(date)
            else:
                self.calendar.setDateTextFormat(check_date, self.fmt)

        # mark current day in calendar
        current = self.currentDay + self.currentMonth + self.currentYear
        self.calendar.setDateTextFormat(QDate.fromString(current, "ddMMyyyy"), cur_fmt)

        # organize buttons and layouts for display
        addButton = QPushButton("Add Event")
        addButton.clicked.connect(self.addNote)
        editButton = QPushButton("Edit")
        editButton.clicked.connect(self.editNote)
        delButton = QPushButton("Delete")
        delButton.clicked.connect(self.delNote)

        self.calendar.selectionChanged.connect(self.showDateInfo)
        self.calendar.selectionChanged.connect(self.labelDate)
        self.calendar.selectionChanged.connect(self.highlightFirstItem)

        self.note_group = QListWidget()
        self.note_group.setSortingEnabled(True)
        self.note_group.setStyleSheet("QListView::item {height: 40px;}")

        self.label = QLabel()
        label_font = QtGui.QFont("Gabriola", 18)
        self.label.setFont(label_font)
        self.labelDate()
        self.showDateInfo()

        labelp = QLabel()
        pixmap = QPixmap(path.join(self.icon_folder, 'calendar.png'))
        labelp.setPixmap(pixmap)

        # set up a timer that automatically updates every second
        self.lcd = QLCDNumber()
        self.lcd.setSegmentStyle(QLCDNumber.Filled)
        self.lcd.setMinimumWidth(80)
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
        self.showTime()

        hbox1 = QHBoxLayout()
        hbox1.addStretch(1)
        hbox1.addWidget(self.label)
        hbox1.addStretch(1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(addButton)
        hbox2.addWidget(editButton)
        hbox2.addWidget(delButton)

        hbox3 = QHBoxLayout()
        hbox3.addStretch(1)
        hbox3.addWidget(labelp)
        hbox3.addWidget(self.lcd)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.note_group)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        hbox = QHBoxLayout()
        hbox.addWidget(self.calendar, 55)
        hbox.addLayout(vbox, 45)

        self.setLayout(hbox)

    def showDateInfo(self):
        # add events to selected date
        date = self.getDate()
        self.note_group.clear()
        if date in self.data:
            self.note_group.addItems(self.data[date])

    def addNote(self):
        # adding notes for selected date
        # if a note starts with any number other than 0, 1, 2
        # add a 0 before it so that we can easily sort events
        # by start time
        date = self.getDate()
        row = self.note_group.currentRow()
        title = "Add event"
        string, ok = QInputDialog.getText(self, title, "Enter your note:")

        if ok and string:
            if string[0].isdigit() and string[0] not in ["0", "1", "2"]:
                string = string.replace(string[0], "0" + string[0])
            self.note_group.insertItem(row, string)
            self.calendar.setDateTextFormat(QDate.fromString(date, "ddMMyyyy"), self.fmt)
            if date in self.data:
                self.data[date].append(string)
            else:
                self.data[date] = [string]

            # Save the notes locally
            notes_filename = "notes.txt"
            with open(notes_filename, "a") as notes_file:
                notes_file.write(string + "\n")

            # Check if the note is an event with a specific time or date
            if self.isEventApproaching(string):
                # Show a notification
                self.showNotification('Event Approaching', f'The event "{string}" is approaching!')

    def isEventApproaching(self, event_text):
        # Check if the note is an event with a specific time or date
        # For example, you can assume that events containing "at" are time-specific
        if "at" in event_text.lower():
            # Extract the time from the event text and compare it with the current time
            event_time_str = event_text.lower().split("at")[1].strip()
            event_time = QTime.fromString(event_time_str, "hh:mm")
            current_time = QTime.currentTime()

            # Check if the event time is within a certain time frame (e.g., 15 minutes)
            time_difference = current_time.msecsTo(event_time)
            return 0 < time_difference <= 15 * 60 * 1000  # 15 minutes

        # Add additional conditions based on your specific format for event notes
        # ...

        return False

    def delNote(self):
        # delete the currently selected item
        date = self.getDate()
        row = self.note_group.currentRow()
        item = self.note_group.item(row)

        if not item:
            return
        reply = QMessageBox.question(self, " ", "Remove",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            item = self.note_group.takeItem(row)
            self.data[date].remove(item.text())
            if not self.data[date]:
                del(self.data[date])
                self.calendar.setDateTextFormat(QDate.fromString(date, "ddMMyyyy"), self.delfmt)
            del(item)

    def editNote(self):
        # edit the currently selected item
        date = self.getDate()
        row = self.note_group.currentRow()
        item = self.note_group.item(row)

        if item:
            copy = item.text()
            title = "Edit event"
            string, ok = QInputDialog.getText(self, title, "Enter your note:",
                                              QLineEdit.Normal, item.text())

            if ok and string:
                self.data[date].remove(copy)
                self.data[date].append(string)
                if string[0].isdigit() and string[0] not in ["0", "1", "2"]:
                    string = string.replace(string[0], "0" + string[0])
                item.setText(string)

    def getDate(self):
        # parse the selected date into usable string form
        select = self.calendar.selectedDate()
        date = str(select.day()).rjust(2, '0') + str(select.month()).rjust(2, '0') + str(select.year())
        return date

    def labelDate(self):
        # label to show the long name form of the selected date
        # format US style like "Thursday, February 20, 2020"
        select = self.calendar.selectedDate()
        weekday, month = select.dayOfWeek(), select.month()
        day, year = str(select.day()), str(select.year())
        week_day, word_month = QDate.longDayName(weekday), QDate.longMonthName(month)
        self.label.setText(week_day + ", " + word_month + " " + day + ", " + year)

    def highlightFirstItem(self):
        # highlight the first item immediately after switching selection
        if self.note_group.count() > 0:
            self.note_group.setCurrentRow(0)

    def showTime(self):
        # keep the current time updated
        time = QTime.currentTime()
        text = time.toString("hh:mm")
        if time.second() % 2 == 0:
            text.replace(text[2], '')
        self.lcd.display(text)

    def showNotification(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)

    def closeEvent(self, e):
        # save all data into json file when the user closes the app
        with open("data.json", "w") as json_file:
            json.dump(self.data, json_file)

        notes_filename = "notes.txt"
        with open(notes_filename, "a") as notes_file:
            notes_file.write(self.notes_textedit.toPlainText() + "\n")

        e.accept()
        e.ignore()
        self.hide()
        self.tray_icon.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    window = Calendar(size.width(), size.height())
    window.show()
    sys.exit(app.exec_())
