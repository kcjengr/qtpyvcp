#ifndef GCODEHIGHLIGHTER_H
#define GCODEHIGHLIGHTER_H

#include <QSyntaxHighlighter>
#include <QRegularExpression>
#include <QColor>
#include <QSet>

class GCodeHighlighter : public QSyntaxHighlighter
{
    Q_OBJECT

public:
    GCodeHighlighter(QTextDocument *parent = nullptr);

    void setGCodeHighlightEnabled(bool enabled);
    bool isGCodeHighlightEnabled() const;
    void setMCodeHighlightEnabled(bool enabled);
    bool isMCodeHighlightEnabled() const;
    void setParameterHighlightEnabled(bool enabled);
    bool isParameterHighlightEnabled() const;
    void setNumberHighlightEnabled(bool enabled);
    bool isNumberHighlightEnabled() const;
    void setCommentHighlightEnabled(bool enabled);
    bool isCommentHighlightEnabled() const;
    void setStringHighlightEnabled(bool enabled);
    bool isStringHighlightEnabled() const;

    void setGCodeColor(const QColor &color);
    QColor gCodeColor() const;
    void setMCodeColor(const QColor &color);
    QColor mCodeColor() const;
    void setParameterColor(const QColor &color);
    QColor parameterColor() const;
    void setNumberColor(const QColor &color);
    QColor numberColor() const;
    void setCommentColor(const QColor &color);
    QColor commentColor() const;
    void setStringColor(const QColor &color);
    QColor stringColor() const;

    // Performance optimization methods
    void setLazyHighlightingEnabled(bool enabled);
    bool isLazyHighlightingEnabled() const;
    void setVisibleBlockRange(int startBlock, int endBlock);
    void clearVisibleBlockRange();
    void rehighlightVisibleBlocks();

protected:
    void highlightBlock(const QString &text) override;

private:
    bool gCodeHighlightEnabled;
    bool mCodeHighlightEnabled;
    bool parameterHighlightEnabled;
    bool numberHighlightEnabled;
    bool commentHighlightEnabled;
    bool stringHighlightEnabled;

    // Performance optimization
    bool lazyHighlightingEnabled;
    int visibleStartBlock;
    int visibleEndBlock;
    QSet<int> highlightedBlocks;

    QTextCharFormat gCodeFormat;
    QTextCharFormat mCodeFormat;
    QTextCharFormat commentFormat;
    QTextCharFormat numberFormat;
    QTextCharFormat parameterFormat;
    QTextCharFormat stringFormat;

    void applyColors();
    bool isBlockVisible(int blockNumber) const;

    // Static regex patterns for better performance
    static QRegularExpression gCodeRegex;
    static QRegularExpression mCodeRegex;
    static QRegularExpression parameterRegex;
    static QRegularExpression numberRegex;
    static QRegularExpression commentRegex;
    static QRegularExpression stringRegex;
};

#endif // GCODEHIGHLIGHTER_H
