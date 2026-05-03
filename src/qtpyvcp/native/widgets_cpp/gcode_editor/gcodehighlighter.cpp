#include "gcodehighlighter.h"
#include <QColor>
#include <QDebug>
#include <algorithm>

GCodeHighlighter::GCodeHighlighter(QTextDocument *parent)
	: QSyntaxHighlighter(parent)
	, syntaxHighlightingEnabled(false)
{
	// Start with empty rules - Python will configure via setTokenColorMap()
}

void GCodeHighlighter::setSyntaxHighlightingEnabled(bool enabled)
{
	if (syntaxHighlightingEnabled == enabled)
		return;
	syntaxHighlightingEnabled = enabled;
	rehighlight();
}

bool GCodeHighlighter::isSyntaxHighlightingEnabled() const
{
	return syntaxHighlightingEnabled;
}

void GCodeHighlighter::setTokenColorMap(const QVariantMap &tokenColorMap)
{
	// Clear existing rules
	highlightRules.clear();
	
	// Build new rules from token→color mapping
	for (auto it = tokenColorMap.constBegin(); it != tokenColorMap.constEnd(); ++it) {
		QString token = it.key();
		QColor color = it.value().value<QColor>();
		
		if (!color.isValid()) {
			qWarning() << "GCodeHighlighter: Invalid color for token" << token;
			continue;
		}
		
		// Build pattern for this token
		QString patternStr = buildPatternForToken(token);
		if (patternStr.isEmpty()) {
			qWarning() << "GCodeHighlighter: Unknown token type" << token;
			continue;
		}
		
		// Create format rule
		HighlightRule rule;
		rule.tokenName = token;
		rule.pattern = QRegularExpression(patternStr);
		rule.format.setForeground(color);
		
		// Apply text formatting (bold/italic) based on token type
		applyTextFormatting(rule.format, token);
		
		highlightRules.append(rule);
	}
	
	// Sort: G/M code rules applied last so they always win over number coloring
	// inside codes like G1, M30 (number rule fires first, G/M rule overwrites)
	std::stable_sort(highlightRules.begin(), highlightRules.end(),
		[](const HighlightRule &a, const HighlightRule &b) {
			bool aIsCode = (a.tokenName == "G" || a.tokenName == "M");
			bool bIsCode = (b.tokenName == "G" || b.tokenName == "M");
			return !aIsCode && bIsCode;
		});
	
	// Trigger rehighlight if enabled
	if (syntaxHighlightingEnabled) {
		rehighlight();
	}
}

void GCodeHighlighter::clearTokenColorMap()
{
	highlightRules.clear();
	if (syntaxHighlightingEnabled) {
		rehighlight();
	}
}

QString GCodeHighlighter::buildPatternForToken(const QString &token) const
{
	// G codes: G0, G1, G2, G01, etc.
	if (token == "G") {
		return "\\bG[0-9]+(\\.[0-9])?\\b";
	}
	
	// M codes: M3, M5, M30, etc.
	if (token == "M") {
		return "\\bM[0-9]+(\\.[0-9])?\\b";
	}
	
	// Single-letter parameter tokens: X, Y, Z, F, S, T, etc.
	// Pattern: letter only (with lookahead to confirm axis context)
	// Number value is matched separately by the 'number' token rule
	QStringList paramTokens = {"X", "Y", "Z", "A", "B", "C", "U", "V", "W",
	                            "I", "J", "K", "R", "Q", "P", "F",
	                            "T", "H", "S", "D", "E", "L", "N", "O"};
	if (paramTokens.contains(token)) {
		// Match the axis letter only, but only when followed by a sign or digit
		return QString("\\b[%1](?=[+-]?[0-9])").arg(token);
	}
	
	// Numbers: signed (handles values after axis letters AND standalone)
	// [+-]?[0-9]+ covers: 10, -10, +10, 10.5, -0.125
	// No leading \b needed since [+-] is non-word; trailing \b anchors end
	if (token == "number") {
		return "[+-]?[0-9]+(\\.[0-9]*)?";
	}
	
	// Semicolon comments: ; to end of line
	if (token == "semicolon" || token == "comment_semicolon") {
		return ";[^\\n]*";
	}
	
	// Parenthesis comments: (comment text)
	if (token == "parenthesis" || token == "comment_parenthesis") {
		return "\\([^\\n]*\\)";
	}
	
	// Generic comment (both types)
	if (token == "comment") {
		return ";[^\\n]*|\\([^\\n]*\\)";
	}
	
	// Single-quoted strings
	if (token == "single_quote") {
		return "'[^']*'";
	}
	
	// Double-quoted strings
	if (token == "double_quote") {
		return "\"[^\"]*\"";
	}
	
	// Generic string (both types)
	if (token == "string") {
		return "\"[^\"]*\"|'[^']*'";
	}
	
	// Unknown token
	return QString();
}

void GCodeHighlighter::applyTextFormatting(QTextCharFormat &format, const QString &token) const
{
	// Make comments italic
	if (token.contains("comment") || token == "semicolon" || token == "parenthesis") {
		format.setFontItalic(true);
	}
}

void GCodeHighlighter::highlightBlock(const QString &text)
{
	if (!syntaxHighlightingEnabled) {
		return;  // Master switch off
	}
	
	// Apply each rule in order
	for (const HighlightRule &rule : highlightRules) {
		QRegularExpressionMatchIterator matches = rule.pattern.globalMatch(text);
		while (matches.hasNext()) {
			QRegularExpressionMatch match = matches.next();
			setFormat(match.capturedStart(), match.capturedLength(), rule.format);
		}
	}
}
