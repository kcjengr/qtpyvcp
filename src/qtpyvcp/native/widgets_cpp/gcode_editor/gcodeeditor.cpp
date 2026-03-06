#include "gcodeeditor.h"
#include <QScrollBar>
#include <QPainter>
#include <QTextBlock>
#include <QPalette>
#include <QFile>
#include <QFileDialog>
#include <QDialog>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QMessageBox>
#include <QPushButton>
#include <QTextCharFormat>
#include <QTextDocument>
#include <QTextStream>
#include <QVBoxLayout>

void GCodeEditor::applyExtraSelections()
{
	QList<QTextEdit::ExtraSelection> extraSelections = searchExtraSelections;

	if (!isReadOnly() && currentLineHighlight) {
		QTextEdit::ExtraSelection selection;
		selection.format.setBackground(currentLineBackgroundColor);
		selection.format.setForeground(currentLineTextColor);
		selection.format.setProperty(QTextFormat::FullWidthSelection, true);
		selection.cursor = textCursor();
		selection.cursor.clearSelection();
		extraSelections.append(selection);
	}

	setExtraSelections(extraSelections);
}

void GCodeEditor::findDialog()
{
	QDialog dialog(this);
	dialog.setWindowTitle(tr("Find / Replace"));
	dialog.setObjectName("findReplaceDialog");
	dialog.setMinimumWidth(520);
	dialog.setStyleSheet(
		"QDialog#findReplaceDialog QLineEdit {"
		"  font: 10pt \"sans\";"
		"  padding-left: 5px;"
		"}"
	);

	auto *mainLayout = new QVBoxLayout(&dialog);
	mainLayout->setContentsMargins(20, 20, 20, 20);
	mainLayout->setSpacing(20);

	auto *findRow = new QHBoxLayout();
	auto *replaceRow = new QHBoxLayout();
	auto *buttonRow = new QHBoxLayout();
	findRow->setContentsMargins(6, 10, 6, 0);
	findRow->setSpacing(12);
	replaceRow->setContentsMargins(6, 0, 6, 0);
	replaceRow->setSpacing(12);
	buttonRow->setContentsMargins(6, 20, 6, 0);
	buttonRow->setSpacing(15);

	auto *findLabel = new QLabel(tr("Find:"), &dialog);
	auto *replaceLabel = new QLabel(tr("Replace:"), &dialog);
	auto *findEdit = new QLineEdit(&dialog);
	auto *replaceEdit = new QLineEdit(&dialog);
	auto *findPrevButton = new QPushButton(&dialog);
	auto *findNextButton = new QPushButton(&dialog);
	auto *replaceButton = new QPushButton(tr("Replace"), &dialog);
	auto *replaceAllButton = new QPushButton(tr("Replace All"), &dialog);
	auto *closeButton = new QPushButton(tr("Close"), &dialog);
	auto *undoButton = new QPushButton(tr("Undo"), &dialog);
	auto *statusLabel = new QLabel(&dialog);

	findLabel->setFixedWidth(60);
	findLabel->setStyleSheet("QLabel { font: 14pt; }");
	replaceLabel->setFixedWidth(60);
	replaceLabel->setStyleSheet("QLabel { font: 14pt; }");

	findEdit->setPlaceholderText(tr("Enter search text..."));
	findEdit->setMinimumHeight(40);
	findEdit->setMinimumWidth(260);

	replaceEdit->setPlaceholderText(tr("Replace with..."));
	replaceEdit->setMinimumHeight(40);

	findPrevButton->setText(QString());
	findPrevButton->setToolTip(tr("Previous (Shift+Enter)"));
	findPrevButton->setFixedSize(50, 42);
	findPrevButton->setIcon(QIcon(":/images/up_arrow.png"));
	findPrevButton->setIconSize(QSize(20, 20));

	findNextButton->setText(QString());
	findNextButton->setToolTip(tr("Next (Enter)"));
	findNextButton->setFixedSize(50, 42);
	findNextButton->setIcon(QIcon(":/images/down_arrow.png"));
	findNextButton->setIconSize(QSize(20, 20));

	statusLabel->setFixedWidth(110);
	statusLabel->setAlignment(Qt::AlignCenter);
	statusLabel->setStyleSheet(QStringLiteral(
		"QLabel {"
		"  border-style: solid;"
		"  border-color: %1;"
		"  border-width: 1px;"
		"  border-radius: 5px;"
		"  color: %2;"
		"  background: %3;"
		"  font: 15pt;"
		"  font-weight: bold;"
		"}"
	)
		.arg(findStatusBorderColor.name(QColor::HexArgb))
		.arg(findStatusTextColor.name(QColor::HexArgb))
		.arg(findStatusBackgroundColor.name(QColor::HexArgb)));

	replaceButton->setMinimumSize(120, 40);
	replaceAllButton->setMinimumSize(120, 40);
	closeButton->setMinimumSize(100, 40);
	undoButton->setMinimumSize(100, 40);
	undoButton->setEnabled(false);

	QPalette defaultPalette = findEdit->palette();
	QPalette errorPalette = findEdit->palette();
	errorPalette.setColor(QPalette::Base, findErrorBackgroundColor);
	errorPalette.setColor(QPalette::Text, findErrorTextColor);

	struct ReplaceRecord {
		int pos;
		QString original;
		QString new_text;
	};
	QVector<QVector<ReplaceRecord>> replaceUndoStack;

	auto rebuildHighlightsAndStatus = [this, findEdit, statusLabel]() {
		const QString needle = findEdit->text();
		searchExtraSelections.clear();

		if (needle.isEmpty()) {
			statusLabel->clear();
			applyExtraSelections();
			return;
		}

		QTextCursor scan(document());
		scan.movePosition(QTextCursor::Start);

		int count = 0;
		int currentIndex = -1;
		const int currentStart = textCursor().selectionStart();

		QTextCharFormat fmt;
		fmt.setBackground(findHighlightBackgroundColor);
		fmt.setForeground(findHighlightTextColor);

		while (true) {
			QTextCursor found = document()->find(needle, scan);
			if (found.isNull()) {
				break;
			}

			QTextEdit::ExtraSelection sel;
			sel.cursor = found;
			sel.format = fmt;
			searchExtraSelections.append(sel);

			count++;
			if (found.selectionStart() == currentStart) {
				currentIndex = count;
			}

			scan = found;
		}

		if (count == 0) {
			statusLabel->setText(QStringLiteral("Not found"));
		} else {
			if (currentIndex < 1) {
				currentIndex = 1;
			}
			statusLabel->setText(QString::number(currentIndex) + QStringLiteral(" of ") + QString::number(count));
		}

		applyExtraSelections();
	};

	findRow->addWidget(findLabel);
	findRow->addWidget(findEdit, 1);
	findRow->addWidget(findPrevButton);
	findRow->addWidget(findNextButton);

	replaceRow->addWidget(replaceLabel);
	replaceRow->addWidget(replaceEdit, 1);
	replaceRow->addWidget(statusLabel);

	buttonRow->addWidget(replaceButton);
	buttonRow->addWidget(replaceAllButton);
	buttonRow->addWidget(undoButton);
	buttonRow->addStretch(1);
	buttonRow->addWidget(closeButton);

	mainLayout->addLayout(findRow);
	mainLayout->addLayout(replaceRow);
	mainLayout->addLayout(buttonRow);

	auto findNext = [this, findEdit]() {
		const QString needle = findEdit->text();
		if (needle.isEmpty()) {
			return false;
		}

		QTextCursor found = document()->find(needle, textCursor());
		if (found.isNull()) {
			QTextCursor start(document());
			start.movePosition(QTextCursor::Start);
			setTextCursor(start);
			found = document()->find(needle, textCursor());
		}

		if (!found.isNull()) {
			setTextCursor(found);
			centerCursor();
			return true;
		}
		return false;
	};

	auto findPrev = [this, findEdit]() {
		const QString needle = findEdit->text();
		if (needle.isEmpty()) {
			return false;
		}

		QTextCursor found = document()->find(needle, textCursor(), QTextDocument::FindBackward);
		if (found.isNull()) {
			QTextCursor end(document());
			end.movePosition(QTextCursor::End);
			setTextCursor(end);
			found = document()->find(needle, textCursor(), QTextDocument::FindBackward);
		}

		if (!found.isNull()) {
			setTextCursor(found);
			centerCursor();
			return true;
		}
		return false;
	};

	auto focusFirstMatch = [this, findEdit]() {
		const QString needle = findEdit->text();
		if (needle.isEmpty()) {
			QTextCursor cursor = textCursor();
			cursor.clearSelection();
			setTextCursor(cursor);
			return false;
		}

		QTextCursor start(document());
		start.movePosition(QTextCursor::Start);
		QTextCursor found = document()->find(needle, start);
		if (found.isNull()) {
			QTextCursor cursor = textCursor();
			cursor.clearSelection();
			setTextCursor(cursor);
			return false;
		}

		setTextCursor(found);
		centerCursor();
		return true;
	};

	QObject::connect(findEdit, &QLineEdit::textChanged, &dialog, [findEdit, defaultPalette, focusFirstMatch, rebuildHighlightsAndStatus]() {
		findEdit->setPalette(defaultPalette);
		focusFirstMatch();
		rebuildHighlightsAndStatus();
	});

	QObject::connect(findNextButton, &QPushButton::clicked, &dialog, [findNext, findEdit, errorPalette, rebuildHighlightsAndStatus]() {
		if (findNext()) {
			rebuildHighlightsAndStatus();
		} else {
			findEdit->setPalette(errorPalette);
		}
	});
	QObject::connect(findPrevButton, &QPushButton::clicked, &dialog, [findPrev, findEdit, errorPalette, rebuildHighlightsAndStatus]() {
		if (findPrev()) {
			rebuildHighlightsAndStatus();
		} else {
			findEdit->setPalette(errorPalette);
		}
	});
	QObject::connect(findEdit, &QLineEdit::returnPressed, &dialog, [findNext, findEdit, errorPalette, rebuildHighlightsAndStatus]() {
		if (findNext()) {
			rebuildHighlightsAndStatus();
		} else {
			findEdit->setPalette(errorPalette);
		}
	});
	QObject::connect(replaceEdit, &QLineEdit::returnPressed, &dialog, [replaceButton]() {
		replaceButton->click();
	});

	QObject::connect(replaceButton, &QPushButton::clicked, &dialog, [this, findEdit, replaceEdit, findNext, &replaceUndoStack, undoButton, rebuildHighlightsAndStatus]() {
		const QString needle = findEdit->text();
		if (needle.isEmpty()) {
			return;
		}

		QTextCursor cursor = textCursor();
		QVector<ReplaceRecord> records;
		if (cursor.hasSelection() && cursor.selectedText() == needle) {
			records.append({cursor.selectionStart(), cursor.selectedText(), replaceEdit->text()});
			cursor.insertText(replaceEdit->text());
		}

		if (!records.isEmpty()) {
			replaceUndoStack.append(records);
			undoButton->setEnabled(true);
		}

		findNext();
		rebuildHighlightsAndStatus();
	});

	QObject::connect(replaceAllButton, &QPushButton::clicked, &dialog, [this, findEdit, replaceEdit, &replaceUndoStack, undoButton, statusLabel, rebuildHighlightsAndStatus]() {
		const QString needle = findEdit->text();
		if (needle.isEmpty()) {
			return;
		}

		QTextCursor cursor(document());
		QVector<ReplaceRecord> records;
		cursor.beginEditBlock();
		cursor.movePosition(QTextCursor::Start);

		while (true) {
			QTextCursor found = document()->find(needle, cursor);
			if (found.isNull()) {
				break;
			}
			records.append({found.selectionStart(), found.selectedText(), replaceEdit->text()});
			found.insertText(replaceEdit->text());
			cursor = found;
		}

		cursor.endEditBlock();

		if (!records.isEmpty()) {
			replaceUndoStack.append(records);
			undoButton->setEnabled(true);
			statusLabel->setText(QStringLiteral("Replaced ") + QString::number(records.size()));
		} else {
			statusLabel->setText(QStringLiteral("Not found"));
		}

		rebuildHighlightsAndStatus();
	});

	QObject::connect(undoButton, &QPushButton::clicked, &dialog, [this, &replaceUndoStack, undoButton, rebuildHighlightsAndStatus]() {
		if (replaceUndoStack.isEmpty()) {
			return;
		}

		const QVector<ReplaceRecord> records = replaceUndoStack.takeLast();
		QTextCursor cursor(document());
		cursor.beginEditBlock();
		for (int i = records.size() - 1; i >= 0; --i) {
			const ReplaceRecord &record = records.at(i);
			cursor.setPosition(record.pos);
			cursor.setPosition(record.pos + record.new_text.size(), QTextCursor::KeepAnchor);
			cursor.insertText(record.original);
		}
		cursor.endEditBlock();

		undoButton->setEnabled(!replaceUndoStack.isEmpty());
		rebuildHighlightsAndStatus();
	});

	auto clearSearchUiState = [this]() {
		searchExtraSelections.clear();
		QTextCursor cursor = textCursor();
		if (cursor.hasSelection()) {
			cursor.clearSelection();
			setTextCursor(cursor);
		}
		applyExtraSelections();
	};

	QObject::connect(closeButton, &QPushButton::clicked, &dialog, &QDialog::accept);
	QObject::connect(&dialog, &QDialog::finished, this, clearSearchUiState);

	findEdit->setFocus();
	rebuildHighlightsAndStatus();
	dialog.exec();
}

void GCodeEditor::saveFile()
{
	if (currentFilePath.isEmpty()) {
		saveFileAs();
		return;
	}

	QFile file(currentFilePath);
	if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
		QMessageBox::warning(this,
						 tr("Save Failed"),
						 tr("Unable to save file:\n%1").arg(currentFilePath));
		return;
	}

	QTextStream out(&file);
	out << toPlainText();
}

void GCodeEditor::saveFileAs()
{
	const QString path = QFileDialog::getSaveFileName(this,
									  tr("Save G-code As"),
									  currentFilePath,
									  tr("G-code Files (*.ngc *.nc *.tap *.txt);;All Files (*)"));
	if (path.isEmpty()) {
		return;
	}

	currentFilePath = path;
	saveFile();
}

void GCodeEditor::EditorReadWrite(bool editable)
{
	setReadOnly(!editable);
}

void GCodeEditor::setEditable(bool editable)
{
	EditorReadWrite(editable);
}

void GCodeEditor::setFilename(const QString &path)
{
	setFilePath(path);
}

GCodeEditor::GCodeEditor(QWidget *parent) : QPlainTextEdit(parent)
{
	highlighter = new GCodeHighlighter(document());
	lineNumberArea = new LineNumberArea(this);
	lineNumberAreaBackgroundColor = QColor(240, 240, 240);
	lineNumberAreaTextColor = Qt::black;
	lineNumberAreaFont = font();
	lineNumberAreaFont.setPointSize(10);
	currentLineHighlight = true;
	currentLineBackgroundColor = QColor(Qt::yellow).lighter(160);
	currentLineTextColor = palette().color(QPalette::Text);
	findHighlightBackgroundColor = QColor(85, 85, 238, 90);
	findHighlightTextColor = QColor(Qt::white);
	findErrorBackgroundColor = QColor(Qt::red);
	findErrorTextColor = QColor(Qt::white);
	findStatusBackgroundColor = QColor(90, 90, 90);
	findStatusTextColor = QColor(Qt::white);
	findStatusBorderColor = QColor(95, 95, 95);

	connect(document(), &QTextDocument::blockCountChanged,
			this, &GCodeEditor::updateLineNumberAreaWidth);
	connect(this, &QPlainTextEdit::updateRequest,
			this, &GCodeEditor::updateLineNumberArea);
	connect(verticalScrollBar(), &QScrollBar::valueChanged,
			this, [this](int){ lineNumberArea->update(); });
	connect(this, &QPlainTextEdit::cursorPositionChanged,
			this, &GCodeEditor::highlightCurrentLine);

	updateLineNumberAreaWidth(0);
	lineNumberArea->raise();
	highlightCurrentLine();
}

GCodeEditor::~GCodeEditor()
{
	delete highlighter;
}

int GCodeEditor::lineNumberAreaWidth() const
{
	int digits = 1;
	int max = qMax(1, document()->blockCount());
	while (max >= 10) {
		max /= 10;
		++digits;
	}
	QFontMetrics marginMetrics(lineNumberAreaFont);
	return 10 + marginMetrics.horizontalAdvance('9') * digits;
}

void GCodeEditor::lineNumberAreaPaintEvent(QPaintEvent *event)
{
	QPainter painter(lineNumberArea);
	painter.fillRect(event->rect(), lineNumberAreaBackgroundColor);
	painter.setFont(lineNumberAreaFont);

	QTextBlock block = firstVisibleBlock();
	int blockNumber = block.blockNumber();

	qreal top = blockBoundingGeometry(block).translated(contentOffset()).top();
	qreal bottom = top + blockBoundingRect(block).height();

	while (block.isValid() && top <= event->rect().bottom()) {
		if (block.isVisible() && bottom >= event->rect().top()) {
			QString number = QString::number(blockNumber + 1);
			painter.setPen(lineNumberAreaTextColor);
			painter.drawText(0, top,
							 lineNumberArea->width() - 5,
							 QFontMetrics(lineNumberAreaFont).height(),
							 Qt::AlignRight, number);
		}

		block = block.next();
		top = bottom;
		bottom = top + blockBoundingRect(block).height();
		++blockNumber;
	}
}

void GCodeEditor::resizeEvent(QResizeEvent *event)
{
	QPlainTextEdit::resizeEvent(event);
	updateLineNumberAreaWidth(0);

	QRect cr = contentsRect();
	lineNumberArea->setGeometry(QRect(cr.left(), cr.top(),
									  lineNumberAreaWidth(), cr.height()));
}

void GCodeEditor::showEvent(QShowEvent *event)
{
	QPlainTextEdit::showEvent(event);
	updateLineNumberAreaWidth(0);
	QRect cr = contentsRect();
	lineNumberArea->setGeometry(QRect(cr.left(), cr.top(),
									  lineNumberAreaWidth(), cr.height()));
	lineNumberArea->raise();
}

void GCodeEditor::changeEvent(QEvent *event)
{
	QPlainTextEdit::changeEvent(event);

	switch (event->type()) {
	case QEvent::StyleChange:
	case QEvent::FontChange:
	case QEvent::PaletteChange:
	case QEvent::LayoutDirectionChange:
		updateLineNumberAreaWidth(0);
		lineNumberArea->update();
		break;
	default:
		break;
	}
}

void GCodeEditor::updateLineNumberAreaWidth(int)
{
	setViewportMargins(lineNumberAreaWidth(), 0, 0, 0);
}

void GCodeEditor::highlightCurrentLine()
{
	applyExtraSelections();
}

void GCodeEditor::updateLineNumberArea(const QRect &rect, int dy)
{
	if (dy)
		lineNumberArea->scroll(0, dy);
	else
		lineNumberArea->update(0, rect.y(), lineNumberArea->width(), rect.height());
}

bool GCodeEditor::gCodeHighlightEnabled() const
{
	return highlighter->isGCodeHighlightEnabled();
}

void GCodeEditor::setGCodeHighlightEnabled(bool enabled)
{
	highlighter->setGCodeHighlightEnabled(enabled);
}

bool GCodeEditor::mCodeHighlightEnabled() const
{
	return highlighter->isMCodeHighlightEnabled();
}

void GCodeEditor::setMCodeHighlightEnabled(bool enabled)
{
	highlighter->setMCodeHighlightEnabled(enabled);
}

bool GCodeEditor::parameterHighlightEnabled() const
{
	return highlighter->isParameterHighlightEnabled();
}

void GCodeEditor::setParameterHighlightEnabled(bool enabled)
{
	highlighter->setParameterHighlightEnabled(enabled);
}

bool GCodeEditor::numberHighlightEnabled() const
{
	return highlighter->isNumberHighlightEnabled();
}

void GCodeEditor::setNumberHighlightEnabled(bool enabled)
{
	highlighter->setNumberHighlightEnabled(enabled);
}

bool GCodeEditor::commentHighlightEnabled() const
{
	return highlighter->isCommentHighlightEnabled();
}

void GCodeEditor::setCommentHighlightEnabled(bool enabled)
{
	highlighter->setCommentHighlightEnabled(enabled);
}

bool GCodeEditor::stringHighlightEnabled() const
{
	return highlighter->isStringHighlightEnabled();
}

void GCodeEditor::setStringHighlightEnabled(bool enabled)
{
	highlighter->setStringHighlightEnabled(enabled);
}

QColor GCodeEditor::gCodeColor() const
{
	return highlighter->gCodeColor();
}

void GCodeEditor::setGCodeColor(const QColor &color)
{
	highlighter->setGCodeColor(color);
}

QColor GCodeEditor::mCodeColor() const
{
	return highlighter->mCodeColor();
}

void GCodeEditor::setMCodeColor(const QColor &color)
{
	highlighter->setMCodeColor(color);
}

QColor GCodeEditor::parameterColor() const
{
	return highlighter->parameterColor();
}

void GCodeEditor::setParameterColor(const QColor &color)
{
	highlighter->setParameterColor(color);
}

QColor GCodeEditor::numberColor() const
{
	return highlighter->numberColor();
}

void GCodeEditor::setNumberColor(const QColor &color)
{
	highlighter->setNumberColor(color);
}

QColor GCodeEditor::commentColor() const
{
	return highlighter->commentColor();
}

void GCodeEditor::setCommentColor(const QColor &color)
{
	highlighter->setCommentColor(color);
}

QColor GCodeEditor::stringColor() const
{
	return highlighter->stringColor();
}

void GCodeEditor::setStringColor(const QColor &color)
{
	highlighter->setStringColor(color);
}

QColor GCodeEditor::lineNumberAreaBackground() const
{
	return lineNumberAreaBackgroundColor;
}

void GCodeEditor::setLineNumberAreaBackground(const QColor &color)
{
	lineNumberAreaBackgroundColor = color;
	lineNumberArea->update();
}

QColor GCodeEditor::lineNumberAreaColor() const
{
	return lineNumberAreaTextColor;
}

void GCodeEditor::setLineNumberAreaColor(const QColor &color)
{
	lineNumberAreaTextColor = color;
	lineNumberArea->update();
}

QString GCodeEditor::lineNumberFontFamily() const
{
	return lineNumberAreaFont.family();
}

void GCodeEditor::setLineNumberFontFamily(const QString &family)
{
	lineNumberAreaFont.setFamily(family);
	updateLineNumberAreaWidth(0);
	lineNumberArea->update();
}

int GCodeEditor::lineNumberFontPointSize() const
{
	return lineNumberAreaFont.pointSize();
}

void GCodeEditor::setLineNumberFontPointSize(int pointSize)
{
	lineNumberAreaFont.setPointSize(pointSize);
	updateLineNumberAreaWidth(0);
	lineNumberArea->update();
}

int GCodeEditor::lineNumberFontWeight() const
{
	return lineNumberAreaFont.weight();
}

void GCodeEditor::setLineNumberFontWeight(int weight)
{
	lineNumberAreaFont.setWeight(static_cast<QFont::Weight>(weight));
	lineNumberArea->update();
}

bool GCodeEditor::lineNumberFontItalic() const
{
	return lineNumberAreaFont.italic();
}

void GCodeEditor::setLineNumberFontItalic(bool italic)
{
	lineNumberAreaFont.setItalic(italic);
	lineNumberArea->update();
}

bool GCodeEditor::currentLineHighlightEnabled() const
{
	return currentLineHighlight;
}

void GCodeEditor::setCurrentLineHighlightEnabled(bool enabled)
{
	currentLineHighlight = enabled;
	highlightCurrentLine();
}

QColor GCodeEditor::currentLineBackground() const
{
	return currentLineBackgroundColor;
}

void GCodeEditor::setCurrentLineBackground(const QColor &color)
{
	currentLineBackgroundColor = color;
	highlightCurrentLine();
}

QColor GCodeEditor::currentLineColor() const
{
	return currentLineTextColor;
}

QColor GCodeEditor::findHighlightBackground() const
{
	return findHighlightBackgroundColor;
}

void GCodeEditor::setFindHighlightBackground(const QColor &color)
{
	findHighlightBackgroundColor = color;
}

QColor GCodeEditor::findHighlightText() const
{
	return findHighlightTextColor;
}

void GCodeEditor::setFindHighlightText(const QColor &color)
{
	findHighlightTextColor = color;
}

QColor GCodeEditor::findErrorBackground() const
{
	return findErrorBackgroundColor;
}

void GCodeEditor::setFindErrorBackground(const QColor &color)
{
	findErrorBackgroundColor = color;
}

QColor GCodeEditor::findErrorText() const
{
	return findErrorTextColor;
}

void GCodeEditor::setFindErrorText(const QColor &color)
{
	findErrorTextColor = color;
}

QColor GCodeEditor::findStatusBackground() const
{
	return findStatusBackgroundColor;
}

void GCodeEditor::setFindStatusBackground(const QColor &color)
{
	findStatusBackgroundColor = color;
}

QColor GCodeEditor::findStatusText() const
{
	return findStatusTextColor;
}

void GCodeEditor::setFindStatusText(const QColor &color)
{
	findStatusTextColor = color;
}

QColor GCodeEditor::findStatusBorder() const
{
	return findStatusBorderColor;
}

void GCodeEditor::setFindStatusBorder(const QColor &color)
{
	findStatusBorderColor = color;
}

QString GCodeEditor::filePath() const
{
	return currentFilePath;
}

void GCodeEditor::setFilePath(const QString &path)
{
	currentFilePath = path;
}

void GCodeEditor::setCurrentLineColor(const QColor &color)
{
	currentLineTextColor = color;
	highlightCurrentLine();
}
