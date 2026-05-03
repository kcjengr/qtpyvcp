#ifndef GCODEEDITOR_H
#define GCODEEDITOR_H

#include <QPlainTextEdit>
#include <QPainter>
#include <QTextBlock>
#include <QColor>
#include <QFont>
#include "gcodehighlighter.h"

class LineNumberArea;

class GCodeEditor : public QPlainTextEdit
{
	Q_OBJECT
	// Single master switch for all syntax highlighting
	Q_PROPERTY(bool syntaxHighlightingEnabled READ syntaxHighlightingEnabled WRITE setSyntaxHighlightingEnabled)
	
	Q_PROPERTY(QColor lineNumberAreaBackground READ lineNumberAreaBackground WRITE setLineNumberAreaBackground)
	Q_PROPERTY(QColor lineNumberAreaColor READ lineNumberAreaColor WRITE setLineNumberAreaColor)
	Q_PROPERTY(QString lineNumberFontFamily READ lineNumberFontFamily WRITE setLineNumberFontFamily)
	Q_PROPERTY(int lineNumberFontPointSize READ lineNumberFontPointSize WRITE setLineNumberFontPointSize)
	Q_PROPERTY(int lineNumberFontWeight READ lineNumberFontWeight WRITE setLineNumberFontWeight)
	Q_PROPERTY(bool lineNumberFontItalic READ lineNumberFontItalic WRITE setLineNumberFontItalic)

	Q_PROPERTY(bool currentLineHighlightEnabled READ currentLineHighlightEnabled WRITE setCurrentLineHighlightEnabled)
	Q_PROPERTY(QColor currentLineBackground READ currentLineBackground WRITE setCurrentLineBackground)
	Q_PROPERTY(QColor currentLineColor READ currentLineColor WRITE setCurrentLineColor)
	Q_PROPERTY(QColor findHighlightBackground READ findHighlightBackground WRITE setFindHighlightBackground)
	Q_PROPERTY(QColor findHighlightText READ findHighlightText WRITE setFindHighlightText)
	Q_PROPERTY(QColor findErrorBackground READ findErrorBackground WRITE setFindErrorBackground)
	Q_PROPERTY(QColor findErrorText READ findErrorText WRITE setFindErrorText)
	Q_PROPERTY(QColor findStatusBackground READ findStatusBackground WRITE setFindStatusBackground)
	Q_PROPERTY(QColor findStatusText READ findStatusText WRITE setFindStatusText)
	Q_PROPERTY(QColor findStatusBorder READ findStatusBorder WRITE setFindStatusBorder)
	Q_PROPERTY(QString filePath READ filePath WRITE setFilePath)

public:
	explicit GCodeEditor(QWidget *parent = nullptr);
	~GCodeEditor();

	int lineNumberAreaWidth() const;
	void lineNumberAreaPaintEvent(QPaintEvent *event);

	bool syntaxHighlightingEnabled() const;
	void setSyntaxHighlightingEnabled(bool enabled);

	QColor lineNumberAreaBackground() const;
	void setLineNumberAreaBackground(const QColor &color);
	QColor lineNumberAreaColor() const;
	void setLineNumberAreaColor(const QColor &color);
	QString lineNumberFontFamily() const;
	void setLineNumberFontFamily(const QString &family);
	int lineNumberFontPointSize() const;
	void setLineNumberFontPointSize(int pointSize);
	int lineNumberFontWeight() const;
	void setLineNumberFontWeight(int weight);
	bool lineNumberFontItalic() const;
	void setLineNumberFontItalic(bool italic);

	bool currentLineHighlightEnabled() const;
	void setCurrentLineHighlightEnabled(bool enabled);
	QColor currentLineBackground() const;
	void setCurrentLineBackground(const QColor &color);
	QColor currentLineColor() const;
	void setCurrentLineColor(const QColor &color);
	QColor findHighlightBackground() const;
	void setFindHighlightBackground(const QColor &color);
	QColor findHighlightText() const;
	void setFindHighlightText(const QColor &color);
	QColor findErrorBackground() const;
	void setFindErrorBackground(const QColor &color);
	QColor findErrorText() const;
	void setFindErrorText(const QColor &color);
	QColor findStatusBackground() const;
	void setFindStatusBackground(const QColor &color);
	QColor findStatusText() const;
	void setFindStatusText(const QColor &color);
	QColor findStatusBorder() const;
	void setFindStatusBorder(const QColor &color);
	QString filePath() const;
	void setFilePath(const QString &path);

public slots:
	// Dynamic token→color mapping (called from Python with YAML data)
	void setTokenColorMap(const QVariantMap &tokenColorMap);
	void clearTokenColorMap();
	
	void findDialog();
	void saveFile();
	void saveFileAs();
	void EditorReadWrite(bool editable);
	void setEditable(bool editable);
	void setFilename(const QString &path);

protected:
	void resizeEvent(QResizeEvent *event) override;
	void showEvent(QShowEvent *event) override;
	void changeEvent(QEvent *event) override;

private:
	GCodeHighlighter *highlighter;
	QWidget *lineNumberArea;
	QColor lineNumberAreaBackgroundColor;
	QColor lineNumberAreaTextColor;
	QFont lineNumberAreaFont;
	bool currentLineHighlight;
	QColor currentLineBackgroundColor;
	QColor currentLineTextColor;
	QColor findHighlightBackgroundColor;
	QColor findHighlightTextColor;
	QColor findErrorBackgroundColor;
	QColor findErrorTextColor;
	QColor findStatusBackgroundColor;
	QColor findStatusTextColor;
	QColor findStatusBorderColor;
	QString currentFilePath;
	QList<QTextEdit::ExtraSelection> searchExtraSelections;

	void applyExtraSelections();

	void updateLineNumberAreaWidth(int newBlockCount);
	void highlightCurrentLine();
	void updateLineNumberArea(const QRect &rect, int dy);

	friend class LineNumberArea;
};

class LineNumberArea : public QWidget
{
public:
	LineNumberArea(GCodeEditor *editor) : QWidget(editor), editor(editor) {}

	QSize sizeHint() const override {
		return QSize(editor->lineNumberAreaWidth(), 0);
	}

protected:
	void paintEvent(QPaintEvent *event) override {
		editor->lineNumberAreaPaintEvent(event);
	}

private:
	GCodeEditor *editor;
};

#endif // GCODEEDITOR_H
