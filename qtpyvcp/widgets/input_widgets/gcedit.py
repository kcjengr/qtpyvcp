
import sys
from PyQt5.QtWidgets import (QApplication, QPlainTextEdit,
	QTextEdit, QWidget)
from PyQt5.QtGui import (QIcon, QFontDatabase, QFont, QColor, QPainter,
	QTextFormat, QSyntaxHighlighter, QTextCharFormat)
from PyQt5.QtCore import (QRect, Qt, QRegularExpression)

from qtpy.QtCore import Slot

class gCodeHighlight(QSyntaxHighlighter):
	def __init__(self, parent=None):
		super(gCodeHighlight, self).__init__(parent)

		# G codes by modal group
		# Modal Group 0 Non-Modal
		group0Format = QTextCharFormat()
		group0Format.setForeground(QColor('#800000')) # Maroon
		group0Format.setFontWeight(QFont.Bold)
		group0Patterns = ['G4', 'G10', 'G28',\
			'G30', 'G52', 'G53', 'G92',\
			'G92.1', 'G92.2', 'G92.3']

		# Modal Group 1 Motion
		group1Format = QTextCharFormat()
		group1Format.setForeground(QColor('#FF0000')) # Red
		group1Format.setFontWeight(QFont.Bold)
		group1Patterns = ['G0', 'G1(?!\d)', 'G2(?!\d)', 'G3(?!\d)',\
			'G33', 'G38.2', 'G38.3', 'G38.4',\
			'G38.5', 'G73', 'G76', 'G80',\
			'G81', 'G82', 'G83', 'G84', 'G85',\
			'G86', 'G87', 'G88', 'G89']

		# Modal Group 2 Plane selection
		group2Format = QTextCharFormat()
		group2Format.setForeground(QColor('#FFA500')) # Orange
		group2Format.setFontWeight(QFont.Bold)
		group2Patterns = ['G17', 'G18', 'G19',\
			'G17.1', '18.1', 'G19.1']

		# Modal Group 3 Distance Mode
		group3Format = QTextCharFormat()
		group3Format.setForeground(QColor('#808000')) # Olive
		group3Format.setFontWeight(QFont.Bold)
		group3Patterns = ['G90', 'G91']

		# Modal Group 4 Arc IJK Distance Mode
		group4Format = QTextCharFormat()
		group4Format.setForeground(QColor('#008000')) # Green
		group4Format.setFontWeight(QFont.Bold)
		group4Patterns = ['G90.1', 'G91.1']

		# Modal Group 5 Feed Rate Mode
		group5Format = QTextCharFormat()
		group5Format.setForeground(QColor('#800080')) # Purple
		group5Format.setFontWeight(QFont.Bold)
		group5Patterns = ['G93', 'G94', 'G95']

		# Modal Group 6 Units
		group6Format = QTextCharFormat()
		group6Format.setForeground(QColor('#FF00FF')) # Fuchsia
		group6Format.setFontWeight(QFont.Bold)
		group6Patterns = ['G20', 'G21']

		# Modal Group 7 Cutter Diameter Compensation
		group7Format = QTextCharFormat()
		group7Format.setForeground(QColor('#A52A2A')) # Brown
		group7Format.setFontWeight(QFont.Bold)
		group7Patterns = ['G40', 'G41', 'G42',\
			'G41.1', 'G42.1']

		# Modal Group 8 Tool Length Offset
		group8Format = QTextCharFormat()
		group8Format.setForeground(QColor('#008080')) # Teal
		group8Format.setFontWeight(QFont.Bold)
		group8Patterns = ['G43', 'G43.1', 'G49']

		# Modal Group 10 Canned Cycles Return Mode
		group10Format = QTextCharFormat()
		group10Format.setForeground(QColor('#00FFFF')) # Aqua
		group10Format.setFontWeight(QFont.Bold)
		group10Patterns = ['G98', 'G99']

		# Modal Group 12 Coordinate System
		group12Format = QTextCharFormat()
		group12Format.setForeground(QColor('#0000FF')) # Blue
		group12Format.setFontWeight(QFont.Bold)
		group12Patterns = ['G54', 'G55', 'G56',\
			'G57', 'G58', 'G59', 'G59.1',\
			'G59.2', 'G59.3']

		# Modal Group 13 Control Mode
		group13Format = QTextCharFormat()
		group13Format.setForeground(QColor('#000080')) # Navy
		group13Format.setFontWeight(QFont.Bold)
		group13Patterns = ['G61', 'G61.1', 'G64']

		# Modal Group 14 Spindle Speed Mode
		group14Format = QTextCharFormat()
		group14Format.setForeground(QColor('#808080')) # Gray
		group14Format.setFontWeight(QFont.Bold)
		group14Patterns = ['G96', 'G97']

		# Modal Group 15 Lathe Diameter Mode
		group15Format = QTextCharFormat()
		group15Format.setForeground(QColor('#C0C0C0')) # Silver
		group15Format.setFontWeight(QFont.Bold)
		group15Patterns = ['G7(?!\d)', 'G8(?!\d)']

		# M Codes
		mCodesFormat = QTextCharFormat()
		mCodesFormat.setForeground(QColor('#FF4500')) # Orange Red
		mCodesFormat.setFontWeight(QFont.Bold)
		mCodesPatterns = ['M\d{1,3}']

		# Other Codes
		otherCodesFormat = QTextCharFormat()
		otherCodesFormat.setForeground(QColor('#006400')) # Dark Green
		otherCodesFormat.setFontWeight(QFont.Bold)
		otherCodesPatterns = ['F\\d+', 'S\\d+', 'T\\d+']

		# Comments
		commentFormat = QTextCharFormat()
		commentFormat.setForeground(QColor('#A9A9A9')) # Dark Gray
		commentFormat.setFontWeight(QFont.Bold)
		commentPatterns = [';.*', '\\(.*\\)']


		self.cio = QRegularExpression.CaseInsensitiveOption
		self.rules = [(QRegularExpression(item, self.cio), group0Format) for item in group0Patterns]
		for item in group1Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group1Format])
		for item in group2Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group2Format])
		for item in group3Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group3Format])
		for item in group4Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group4Format])
		for item in group5Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group5Format])
		for item in group6Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group6Format])
		for item in group7Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group7Format])
		for item in group8Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group8Format])
		for item in group10Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group10Format])
		for item in group12Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group12Format])
		for item in group13Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group13Format])
		for item in group14Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group14Format])
		for item in group15Patterns:
			self.rules.append([QRegularExpression(item, self.cio), group15Format])
		for item in mCodesPatterns:
			self.rules.append([QRegularExpression(item, self.cio), mCodesFormat])
		for item in otherCodesPatterns:
			self.rules.append([QRegularExpression(item, self.cio), otherCodesFormat])
		for item in commentPatterns:
			self.rules.append([QRegularExpression(item, self.cio), commentFormat])

	def highlightBlock(self, text): # Using QRegularExpression
		for pattern, format in self.rules:
			exp = QRegularExpression(pattern)
			result = exp.match(text)
			index = result.capturedStart()
			count = 0
			while index >= 0:
				count += 1
				start = result.capturedStart()
				end = result.capturedEnd()
				length = result.capturedLength()
				self.setFormat(start, length, format)
				# check again starting at the end of the last match
				result = exp.match(text, end)
				index = result.capturedStart()

class gCodeEdit(QPlainTextEdit):
	def __init__(self, parent=None):
		super(gCodeEdit, self).__init__(parent)
		self.setGeometry(50, 50, 800, 640)
		self.setWindowTitle("PyQt5 g Code Editor")
		self.setWindowIcon(QIcon('/usr/share/pixmaps/linuxcncicon.png'))
		self.setFont(QFont("DejaVu Sans Mono", 12))
		self.lineNumbers = self.NumberBar(self)
		self.currentLine = None
		self.currentLineColor = self.palette().alternateBase()
		self.cursorPositionChanged.connect(self.highlightLine)
		self.gCodeHighlighter = gCodeHighlight(self.document())


		# for testing
		test_text = """(Group 0)
G4 G10 G28 G30 G52 G53 G92 G92.1 G92.2 G92.3
(Group 1)
G0 G1 G2 G3 G33 G38.2 G38.3 G38.4 G73 G76 G80 G81 G82 G83 G84 G85 G86 G87 G88 G89
(Group 2)
G17 G18 G19 G17.1 G18.1 G19.1
(Group 3)
G90 G91 ; comment
(Group 4)
G90.1 G91.1
(Group 5)
G93 G94 G95
(Group 6)
G20 G21
(Group 7)
G40 G41 G42 G41.1 G42.1
(Group 8)
G43 G43.1 G49
(Group 10)
G98 G99
(Group 12)
G54 G55 G56 G57 G58 G59 G59.1 G59.2 G59.3
(Group 13)
G61 G61.1 G64
(Group 14)
G96 G97
(Group 15)
G7 G8
M0 M1 (Program Pause) M2 M30 M60 ; Program End
M3 M4 M5 ; Spindle
M6 ; Tool Change
M7 M8 M9 ; Coolant
"""
		self.setPlainText(test_text)
		self.show()

	@Slot(bool)
	def EditorReadOnly(self, state):
		if state:
			self.setReadOnly(True)
			print('setReadOnly(True)')
		else:
			self.setReadOnly(False)
			print('setReadOnly(False)')


	def resizeEvent(self, *e):
		cr = self.contentsRect()
		rec = QRect(cr.left(), cr.top(), self.lineNumbers.getWidth(), cr.height())
		self.lineNumbers.setGeometry(rec)
		QPlainTextEdit.resizeEvent(self, *e)

	def highlightLine(self): # highlights current line, find a way not to use QTextEdit
			newCurrentLineNumber = self.textCursor().blockNumber()
			if newCurrentLineNumber != self.currentLine:                
				self.currentLine = newCurrentLineNumber
				selectedLine = QTextEdit.ExtraSelection() 
				selectedLine.format.setBackground(QColor('#d5d8dc'))
				selectedLine.format.setProperty(QTextFormat.FullWidthSelection, True)
				selectedLine.cursor = self.textCursor()
				selectedLine.cursor.clearSelection() 
				self.setExtraSelections([selectedLine])           

	class NumberBar(QWidget):
		def __init__(self, parent):
			QWidget.__init__(self, parent)
			self.parent = parent
			# this only happens when lines are added or subtracted
			self.parent.blockCountChanged.connect(self.updateWidth)
			# this happens quite often
			self.parent.updateRequest.connect(self.updateContents)
			self.font = QFont()
			self.numberBarColor = QColor("#e8e8e8")

		def getWidth(self):
			blocks = self.parent.blockCount()
			return self.fontMetrics().width(str(blocks)) + 10

		def updateWidth(self): # check the number column width and adjust
			width = self.getWidth()
			if self.width() != width:
				self.setFixedWidth(width)
				self.parent.setViewportMargins(width, 0, 0, 0)

		def updateContents(self, rect, scroll):
			if scroll:
				self.scroll(0, scroll)
			else:
				self.update(0, rect.y(), self.width(), rect.height())
			if rect.contains(self.parent.viewport().rect()):
				fontSize = self.parent.currentCharFormat().font().pointSize()
				self.font.setPointSize(fontSize)
				self.font.setStyle(QFont.StyleNormal)
				self.updateWidth()

		def paintEvent(self, event): # this puts the line numbers in the margin
			painter = QPainter(self)
			painter.fillRect(event.rect(), self.numberBarColor)
			block = self.parent.firstVisibleBlock()
			while block.isValid():
				blockNumber = block.blockNumber()
				block_top = self.parent.blockBoundingGeometry(block).translated(self.parent.contentOffset()).top()
				# if the block is not visible stop wasting time
				if not block.isVisible() or block_top >= event.rect().bottom():
					break
				if blockNumber == self.parent.textCursor().blockNumber():
					self.font.setBold(True)
					painter.setPen(QColor("#000000"))
				else:
					self.font.setBold(False)
					painter.setPen(QColor("#717171"))
				painter.setFont(self.font)
				paint_rect = QRect(0, block_top, self.width(), self.parent.fontMetrics().height())
				painter.drawText(paint_rect, Qt.AlignRight, str(blockNumber+1))
				block = block.next()
			painter.end()
			QWidget.paintEvent(self, event)

"""
if __name__ == '__main__':
	app = QApplication(sys.argv)
	GUI = gcedit()
	sys.exit(app.exec_())
"""
