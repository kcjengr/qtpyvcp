#include "gcodehighlighter.h"

// Initialize static regex patterns for better performance
QRegularExpression GCodeHighlighter::gCodeRegex("\\bG[0-9]+(\\.[0-9])?\\b");
QRegularExpression GCodeHighlighter::mCodeRegex("\\bM[0-9]+(\\.[0-9])?\\b");
QRegularExpression GCodeHighlighter::parameterRegex("\\b[XYZABCUVWIJKRQPF][+-]?[0-9]+(\\.[0-9]*)?\\b");
QRegularExpression GCodeHighlighter::numberRegex("(?<![GMXYZABCUVWIJKRQPF])[0-9]+(\\.[0-9]*)?\\b");
QRegularExpression GCodeHighlighter::commentRegex(";[^\\n]*|\\([^\\n]*\\)");
QRegularExpression GCodeHighlighter::stringRegex("\"[^\"]*\"|'[^']*'");

GCodeHighlighter::GCodeHighlighter(QTextDocument *parent)
    : QSyntaxHighlighter(parent)
    , gCodeHighlightEnabled(true)
    , mCodeHighlightEnabled(true)
    , parameterHighlightEnabled(true)
    , numberHighlightEnabled(true)
    , commentHighlightEnabled(true)
    , stringHighlightEnabled(true)
    , lazyHighlightingEnabled(true)
    , visibleStartBlock(-1)
    , visibleEndBlock(-1)
{
    gCodeFormat.setFontWeight(QFont::Bold);
    mCodeFormat.setFontWeight(QFont::Bold);
    commentFormat.setFontItalic(true);
    applyColors();
}

void GCodeHighlighter::setLazyHighlightingEnabled(bool enabled)
{
    if (lazyHighlightingEnabled == enabled)
        return;
    lazyHighlightingEnabled = enabled;
    if (!enabled) {
        // If disabling lazy highlighting, rehighlight everything
        clearVisibleBlockRange();
        rehighlight();
    }
}

bool GCodeHighlighter::isLazyHighlightingEnabled() const
{
    return lazyHighlightingEnabled;
}

void GCodeHighlighter::setVisibleBlockRange(int startBlock, int endBlock)
{
    if (!lazyHighlightingEnabled) {
        return;
    }

    visibleStartBlock = startBlock;
    visibleEndBlock = endBlock;

    // Clear highlighted blocks outside the new visible range
    QSet<int> blocksToKeep;
    for (int i = startBlock; i <= endBlock; ++i) {
        blocksToKeep.insert(i);
    }

    QSet<int> blocksToRemove;
    for (int block : highlightedBlocks) {
        if (!blocksToKeep.contains(block)) {
            blocksToRemove.insert(block);
        }
    }

    for (int block : blocksToRemove) {
        highlightedBlocks.remove(block);
    }

    rehighlightVisibleBlocks();
}

void GCodeHighlighter::clearVisibleBlockRange()
{
    visibleStartBlock = -1;
    visibleEndBlock = -1;
    highlightedBlocks.clear();
}

void GCodeHighlighter::rehighlightVisibleBlocks()
{
    if (!lazyHighlightingEnabled || visibleStartBlock < 0 || visibleEndBlock < 0) {
        rehighlight();
        return;
    }

    // Instead of trying to use setCurrentBlock, we'll rehighlight the entire document
    // but let highlightBlock() check visibility and skip non-visible blocks
    // This is more efficient than trying to manually set blocks
    rehighlight();
}

bool GCodeHighlighter::isBlockVisible(int blockNumber) const
{
    if (!lazyHighlightingEnabled)
        return true;

    if (visibleStartBlock < 0 || visibleEndBlock < 0)
        return true;

    return (blockNumber >= visibleStartBlock && blockNumber <= visibleEndBlock);
}

void GCodeHighlighter::setGCodeHighlightEnabled(bool enabled)
{
    if (gCodeHighlightEnabled == enabled)
        return;
    gCodeHighlightEnabled = enabled;
    rehighlight();
}

bool GCodeHighlighter::isGCodeHighlightEnabled() const
{
    return gCodeHighlightEnabled;
}

void GCodeHighlighter::setMCodeHighlightEnabled(bool enabled)
{
    if (mCodeHighlightEnabled == enabled)
        return;
    mCodeHighlightEnabled = enabled;
    rehighlight();
}

bool GCodeHighlighter::isMCodeHighlightEnabled() const
{
    return mCodeHighlightEnabled;
}

void GCodeHighlighter::setParameterHighlightEnabled(bool enabled)
{
    if (parameterHighlightEnabled == enabled)
        return;
    parameterHighlightEnabled = enabled;
    rehighlight();
}

bool GCodeHighlighter::isParameterHighlightEnabled() const
{
    return parameterHighlightEnabled;
}

void GCodeHighlighter::setNumberHighlightEnabled(bool enabled)
{
    if (numberHighlightEnabled == enabled)
        return;
    numberHighlightEnabled = enabled;
    rehighlight();
}

bool GCodeHighlighter::isNumberHighlightEnabled() const
{
    return numberHighlightEnabled;
}

void GCodeHighlighter::setCommentHighlightEnabled(bool enabled)
{
    if (commentHighlightEnabled == enabled)
        return;
    commentHighlightEnabled = enabled;
    rehighlight();
}

bool GCodeHighlighter::isCommentHighlightEnabled() const
{
    return commentHighlightEnabled;
}

void GCodeHighlighter::setStringHighlightEnabled(bool enabled)
{
    if (stringHighlightEnabled == enabled)
        return;
    stringHighlightEnabled = enabled;
    rehighlight();
}

bool GCodeHighlighter::isStringHighlightEnabled() const
{
    return stringHighlightEnabled;
}

void GCodeHighlighter::setGCodeColor(const QColor &color)
{
    gCodeFormat.setForeground(color);
    rehighlight();
}

QColor GCodeHighlighter::gCodeColor() const
{
    return gCodeFormat.foreground().color();
}

void GCodeHighlighter::setMCodeColor(const QColor &color)
{
    mCodeFormat.setForeground(color);
    rehighlight();
}

QColor GCodeHighlighter::mCodeColor() const
{
    return mCodeFormat.foreground().color();
}

void GCodeHighlighter::setParameterColor(const QColor &color)
{
    parameterFormat.setForeground(color);
    rehighlight();
}

QColor GCodeHighlighter::parameterColor() const
{
    return parameterFormat.foreground().color();
}

void GCodeHighlighter::setNumberColor(const QColor &color)
{
    numberFormat.setForeground(color);
    rehighlight();
}

QColor GCodeHighlighter::numberColor() const
{
    return numberFormat.foreground().color();
}

void GCodeHighlighter::setCommentColor(const QColor &color)
{
    commentFormat.setForeground(color);
    rehighlight();
}

QColor GCodeHighlighter::commentColor() const
{
    return commentFormat.foreground().color();
}

void GCodeHighlighter::setStringColor(const QColor &color)
{
    stringFormat.setForeground(color);
    rehighlight();
}

QColor GCodeHighlighter::stringColor() const
{
    return stringFormat.foreground().color();
}

void GCodeHighlighter::applyColors()
{
    gCodeFormat.setForeground(Qt::darkBlue);
    mCodeFormat.setForeground(Qt::darkMagenta);
    parameterFormat.setForeground(Qt::darkGreen);
    numberFormat.setForeground(Qt::darkRed);
    commentFormat.setForeground(Qt::darkGreen);
    stringFormat.setForeground(Qt::darkCyan);
}

void GCodeHighlighter::highlightBlock(const QString &text)
{
    // Only process if this block should be visible (or lazy highlighting is disabled)
    if (lazyHighlightingEnabled && !isBlockVisible(currentBlock().blockNumber())) {
        return;
    }

    if (gCodeHighlightEnabled) {
        QRegularExpressionMatchIterator gMatches = gCodeRegex.globalMatch(text);
        while (gMatches.hasNext()) {
            QRegularExpressionMatch match = gMatches.next();
            setFormat(match.capturedStart(), match.capturedLength(), gCodeFormat);
        }
    }

    if (mCodeHighlightEnabled) {
        QRegularExpressionMatchIterator mMatches = mCodeRegex.globalMatch(text);
        while (mMatches.hasNext()) {
            QRegularExpressionMatch match = mMatches.next();
            setFormat(match.capturedStart(), match.capturedLength(), mCodeFormat);
        }
    }

    if (parameterHighlightEnabled) {
        QRegularExpressionMatchIterator paramMatches = parameterRegex.globalMatch(text);
        while (paramMatches.hasNext()) {
            QRegularExpressionMatch match = paramMatches.next();
            setFormat(match.capturedStart(), match.capturedLength(), parameterFormat);
        }
    }

    if (numberHighlightEnabled) {
        QRegularExpressionMatchIterator numberMatches = numberRegex.globalMatch(text);
        while (numberMatches.hasNext()) {
            QRegularExpressionMatch match = numberMatches.next();
            setFormat(match.capturedStart(), match.capturedLength(), numberFormat);
        }
    }

    if (commentHighlightEnabled) {
        QRegularExpressionMatchIterator commentMatches = commentRegex.globalMatch(text);
        while (commentMatches.hasNext()) {
            QRegularExpressionMatch match = commentMatches.next();
            setFormat(match.capturedStart(), match.capturedLength(), commentFormat);
        }
    }

    if (stringHighlightEnabled) {
        QRegularExpressionMatchIterator stringMatches = stringRegex.globalMatch(text);
        while (stringMatches.hasNext()) {
            QRegularExpressionMatch match = stringMatches.next();
            setFormat(match.capturedStart(), match.capturedLength(), stringFormat);
        }
    }
}
