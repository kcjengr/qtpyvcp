#ifndef GCODEHIGHLIGHTER_H
#define GCODEHIGHLIGHTER_H

#include <QSyntaxHighlighter>
#include <QRegularExpression>
#include <QColor>
#include <QVector>
#include <QVariantMap>

// Dynamic format rule: token name + pattern + format
struct HighlightRule {
	QString tokenName;
	QRegularExpression pattern;
	QTextCharFormat format;
};

class GCodeHighlighter : public QSyntaxHighlighter
{
	Q_OBJECT

public:
	GCodeHighlighter(QTextDocument *parent = nullptr);

	void setSyntaxHighlightingEnabled(bool enabled);
	bool isSyntaxHighlightingEnabled() const;
	
	// Dynamic configuration: set token→color mappings from YAML
	void setTokenColorMap(const QVariantMap &tokenColorMap);
	void clearTokenColorMap();

protected:
	void highlightBlock(const QString &text) override;

private:
	bool syntaxHighlightingEnabled;
	QVector<HighlightRule> highlightRules;
	
	// Build regex pattern for a given token type
	QString buildPatternForToken(const QString &token) const;
	
	// Apply text formatting (bold for G/M codes, italic for comments)
	void applyTextFormatting(QTextCharFormat &format, const QString &token) const;
};

#endif // GCODEHIGHLIGHTER_H
